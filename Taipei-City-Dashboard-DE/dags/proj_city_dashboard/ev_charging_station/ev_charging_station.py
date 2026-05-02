"""
EV Charging Station DAG — Taipei City
======================================
⚠️  STATUS: API pending approval — TDX account under review.
           Use etl_static.py for now to load static data.
           This DAG is ready to activate once TDX API key is obtained.

Data sources (TDX /v1/EV/ endpoints):
  Station basic info   : GET /v1/EV/Station/City/Taipei
  Connector live status: GET /v1/EV/ConnectorLiveStatus/City/Taipei
  Charging rate        : GET /v1/EV/ChargingRate/City/Taipei
  Operator info        : GET /v1/EV/Operator/City/Taipei

ConnectorStatus codes:
  1 = Available (空閒)
  2 = Occupied  (使用中)
  3 = Unavailable (不可用 / 故障)

Output tables:
  ev_charging_station_taipei  — one row per district with station/gun counts + availability
  (GeoJSON updated to public/mapData/ev_stations_taipei.geojson)

Schedule: daily 06:00 for station info; realtime chart updated separately if needed.
"""

from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    """
    ETL for EV charging station data from TDX API.
    Aggregates station counts and live availability by district (行政區).

    chart_data output format
    -------------------------
    Component 1 — ev_station_distribution (EVStationChart):
      [{"name":"充電站數量","data":[{"x":"中正區","y":23,"total_guns":93},...]}]

    Component 2 — ev_station_realtime (EVRealtimeChart):
      [
        {"name":"空閒",   "data":[{"x":"中正區","y":44},...] },
        {"name":"使用中", "data":[{"x":"中正區","y":38},...] }
      ]
    """
    import json
    import pandas as pd
    import geopandas as gpd
    from shapely.geometry import Point
    from sqlalchemy import create_engine
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import save_dataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from utils.transform_time import convert_str_to_time_format

    # ── Config ────────────────────────────────────────────────────────────────
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")

    CITY = "Taipei"
    BASE_URL = "https://tdx.transportdata.tw/api/basic/v1/EV"
    TOWN_GEOJSON = "/opt/airflow/dags/proj_city_dashboard/ev_charging_station/taipei_town.geojson"

    # ── Extract ───────────────────────────────────────────────────────────────
    stations_raw  = get_tdx_data(f"{BASE_URL}/Station/City/{CITY}?$format=JSON", output_format="dataframe")
    live_raw      = get_tdx_data(f"{BASE_URL}/ConnectorLiveStatus/City/{CITY}?$format=JSON", output_format="dataframe")
    operators_raw = get_tdx_data(f"{BASE_URL}/Operator/City/{CITY}?$format=JSON", output_format="dataframe")

    # Unwrap nested data if returned as dict with key
    if isinstance(stations_raw, dict):
        stations_raw = pd.DataFrame(stations_raw.get("Stations", []))
    if isinstance(live_raw, dict):
        live_raw = pd.DataFrame(live_raw.get("LiveStatuses", []))
    if isinstance(operators_raw, dict):
        operators_raw = pd.DataFrame(operators_raw.get("Operators", []))

    # ── Transform: Station ────────────────────────────────────────────────────
    stations = pd.DataFrame([{
        "station_id":      s.get("StationID"),
        "station_name":    s.get("StationName", {}).get("Zh_tw", "") if isinstance(s.get("StationName"), dict) else "",
        "operator_id":     s.get("OperatorID"),
        "lat":             s.get("PositionLat"),
        "lon":             s.get("PositionLon"),
        "charging_points": s.get("ChargingPoints", 0),
        "charging_rate":   s.get("ChargingRate", ""),
        "parking_rate":    s.get("ParkingRate", ""),
        "service_time":    s.get("ServiceTime", ""),
    } for s in stations_raw.to_dict("records")])

    # Spatial join → assign district
    towns = gpd.read_file(TOWN_GEOJSON)[["TNAME", "geometry"]].to_crs("EPSG:4326")
    gdf = gpd.GeoDataFrame(
        stations,
        geometry=[Point(r.lon, r.lat) for _, r in stations.iterrows()],
        crs="EPSG:4326"
    )
    joined = gpd.sjoin(gdf, towns, how="left", predicate="within")
    stations["district"] = joined["TNAME"].values

    # ── Transform: Live status → availability per station ─────────────────────
    live_agg = (
        live_raw
        .groupby(["StationID", "ConnectorStatus"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"StationID": "station_id", 1: "available", 2: "occupied", 3: "unavailable"})
    )
    for c in ["available", "occupied", "unavailable"]:
        if c not in live_agg.columns:
            live_agg[c] = 0

    # ── Transform: Operator names ─────────────────────────────────────────────
    ops = operators_raw[["OperatorID", "OperatorName"]].copy()
    ops["operator_name"] = ops["OperatorName"].apply(
        lambda x: x.get("Zh_tw", "") if isinstance(x, dict) else ""
    )
    ops = ops.rename(columns={"OperatorID": "operator_id"})[["operator_id", "operator_name"]]

    # ── Merge all ──────────────────────────────────────────────────────────────
    merged = stations.merge(live_agg, on="station_id", how="left")
    merged = merged.merge(ops, on="operator_id", how="left")
    merged["available"] = merged["available"].fillna(0).astype(int)
    merged["occupied"]  = merged["occupied"].fillna(0).astype(int)

    # ── Build chart1: count by district ───────────────────────────────────────
    chart1_grp = merged.groupby("district").agg(
        station_count=("station_id", "count"),
        total_guns=("charging_points", "sum"),
    ).reset_index()
    chart1_grp = chart1_grp[chart1_grp["district"].notna()].sort_values("station_count")

    chart1_data = json.dumps([{
        "name": "充電站數量",
        "data": [{"x": r["district"], "y": int(r["station_count"]), "total_guns": int(r["total_guns"])}
                 for _, r in chart1_grp.iterrows()]
    }], ensure_ascii=False)

    # ── Build chart2: availability by district ────────────────────────────────
    chart2_grp = merged.groupby("district").agg(
        available=("available", "sum"),
        occupied=("occupied", "sum"),
    ).reset_index()
    chart2_grp = chart2_grp[chart2_grp["district"].notna()].sort_values("available")

    chart2_data = json.dumps([
        {"name": "空閒",   "data": [{"x": r["district"], "y": int(r["available"])} for _, r in chart2_grp.iterrows()]},
        {"name": "使用中", "data": [{"x": r["district"], "y": int(r["occupied"])}  for _, r in chart2_grp.iterrows()]},
    ], ensure_ascii=False)

    # ── Ready data: one row per district with both chart payloads ─────────────
    ready_data = chart1_grp[["district", "station_count", "total_guns"]].merge(
        chart2_grp[["district", "available", "occupied"]], on="district", how="outer"
    )
    ready_data["chart1_data"] = chart1_data
    ready_data["chart2_data"] = chart2_data
    ready_data["data_time"] = convert_str_to_time_format(
        [stations_raw.iloc[0].get("UpdateTime", "")] if len(stations_raw) else [""]
    )

    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine, data=ready_data, load_behavior=load_behavior,
        default_table=default_table, history_table="",
    )
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=ready_data["data_time"].max()
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="ev_charging_station")
dag.create_dag(etl_func=_transfer)
