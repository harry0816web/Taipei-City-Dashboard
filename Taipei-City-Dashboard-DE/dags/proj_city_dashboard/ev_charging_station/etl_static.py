"""
EV Charging Station — Static ETL Script
========================================
Purpose : Process downloaded TDX JSON files into dashboard-ready data.
          Run this ONCE to populate the DB with static data.
          When TDX API access is approved, replace with ev_charging_station.py DAG.

Usage   : python etl_static.py --out-dir ./output

API reference (future live use)
--------------------------------
  Station basic info  : GET /v1/EV/Station/City/{City}
  Connector live status: GET /v1/EV/ConnectorLiveStatus/City/{City}
  Charging rate       : GET /v1/EV/ChargingRate/City/{City}
  Charging point      : GET /v1/EV/ChargingPoint/City/{City}
  Operator info       : GET /v1/EV/Operator/City/{City}
  Connector info      : GET /v1/EV/Connector/City/{City}
  Parking rate        : GET /v1/EV/ParkingRate/City/{City}
  Service time        : GET /v1/EV/ServiceTime/City/{City}

  Auth : Bearer token via
         POST https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token
         body: grant_type=client_credentials&client_id=...&client_secret=...

Data files expected in --data-dir
-----------------------------------
  Files are copied from Swagger "Try it out" downloads into data/static
  with descriptive names. response_1777703087046.json is intentionally
  excluded because it does not contain a usable endpoint payload.

ConnectorStatus codes (TDX spec)
----------------------------------
  1 = Available  (空閒)
  2 = Occupied   (使用中)
  3 = Unavailable (不可用 / 故障)
"""

import json
import argparse
import os
import pandas as pd

# ── File mapping ──────────────────────────────────────────────────────────────
FILE_MAP = {
    "stations_tpe":        "taipei_station.json",
    "stations_ntp":        "newtaipei_station.json",
    "live_tpe":            "taipei_connector_live_status.json",
    "live_ntp":            "newtaipei_connector_live_status.json",
    "service_times_tpe":   "taipei_service_time.json",
    "service_times_ntp":   "newtaipei_service_time.json",
    "parking_rates_tpe":   "taipei_parking_rate.json",
    "parking_rates_ntp":   "newtaipei_parking_rate.json",
    "operators_tpe":       "taipei_operator.json",
    "operators_ntp":       "newtaipei_operator.json",
    "connectors_tpe":      "taipei_connector.json",
    "connectors_ntp":      "newtaipei_connector.json",
    "charging_rates_tpe":  "taipei_charging_rate.json",
    "charging_rates_ntp":  "newtaipei_charging_rate.json",
    "charging_points_tpe": "taipei_charging_point.json",
    "charging_points_ntp": "newtaipei_charging_point.json",
}

SCRIPT_DIR = os.path.dirname(__file__)
DEFAULT_DATA_DIR = os.path.join(SCRIPT_DIR, "data/static")

# District boundaries (from dashboard repo)
TOWN_GEOJSON_TPE = os.path.join(
    SCRIPT_DIR,
    "../../../..",
    "Taipei-City-Dashboard-FE/public/mapData/taipei_town.geojson"
)
TOWN_GEOJSON_METRO = os.path.join(
    SCRIPT_DIR,
    "../../../..",
    "Taipei-City-Dashboard-FE/public/mapData/metrotaipei_town.geojson"
)

STATUS_MAP = {1: "available", 2: "occupied", 3: "unavailable"}
STATUS_LABEL = {1: "空閒", 2: "使用中", 3: "不可用"}


def load_json(data_dir, key):
    path = os.path.join(data_dir, FILE_MAP[key])
    with open(path) as f:
        return json.load(f)


def load_stations(data_dir):
    """Load and combine TPE + NTP station data."""
    tpe = load_json(data_dir, "stations_tpe")["Stations"]
    ntp = load_json(data_dir, "stations_ntp")["Stations"]

    rows = []
    for s in tpe:
        rows.append(_flatten_station(s, city="taipei"))
    for s in ntp:
        rows.append(_flatten_station(s, city="newtaipei"))

    df = pd.DataFrame(rows)
    return df


def _flatten_station(s, city):
    loc = s.get("Location", {})
    addr = loc.get("Address", {})
    place = loc.get("Place", {})

    name = s.get("StationName", {}).get("Zh_tw", "")
    address_str = (
        addr.get("City", "") + addr.get("Town", "") +
        addr.get("Road", "") + addr.get("No", "")
    ) or place.get("POI", "")

    return {
        "station_id":     s.get("StationID"),
        "station_name":   name,
        "operator_id":    s.get("OperatorID"),
        "lat":            s.get("PositionLat"),
        "lon":            s.get("PositionLon"),
        "spaces":         s.get("Spaces", 0),
        "charging_points":s.get("ChargingPoints", 0),
        "service_time":   s.get("ServiceTime", ""),
        "parking_rate":   s.get("ParkingRate", ""),
        "charging_rate":  s.get("ChargingRate", ""),
        "description":    s.get("Description", ""),
        "address":        address_str,
        "floors":         s.get("Floors", ""),
        "telephone":      s.get("Telephone", ""),
        "city":           city,
    }


def assign_districts(df, town_geojson_path):
    df = df.copy()
    districts = _load_district_polygons(town_geojson_path)
    df["district"] = [
        _find_district(row.lon, row.lat, districts)
        for _, row in df.iterrows()
    ]
    return df


def _load_district_polygons(town_geojson_path):
    """Load district polygons from GeoJSON without requiring geopandas/shapely."""
    with open(town_geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    districts = []
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        name = props.get("TNAME") or props.get("TOWNNAME") or props.get("townname")
        geometry = feature.get("geometry", {})
        polygons = _geometry_to_polygons(geometry)
        if name and polygons:
            districts.append((name, polygons))
    return districts


def _geometry_to_polygons(geometry):
    if geometry.get("type") == "Polygon":
        return [geometry.get("coordinates", [])]
    if geometry.get("type") == "MultiPolygon":
        return geometry.get("coordinates", [])
    return []


def _find_district(lon, lat, districts):
    if pd.isna(lon) or pd.isna(lat):
        return None
    point = (float(lon), float(lat))
    for name, polygons in districts:
        for polygon in polygons:
            if _point_in_polygon(point, polygon):
                return name
    return None


def _point_in_polygon(point, polygon):
    """Ray-casting point-in-polygon. First ring is shell; later rings are holes."""
    if not polygon or not _point_in_ring(point, polygon[0]):
        return False
    return not any(_point_in_ring(point, hole) for hole in polygon[1:])


def _point_in_ring(point, ring):
    x, y = point
    inside = False
    if not ring:
        return False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        intersects = (yi > y) != (yj > y)
        if intersects:
            x_at_y = (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
            if x < x_at_y:
                inside = not inside
        j = i
    return inside


def load_live_status(data_dir):
    """Load connector live status for TPE + NTP, aggregate to station level."""
    tpe_raw = load_json(data_dir, "live_tpe")["LiveStatuses"]
    ntp_raw = load_json(data_dir, "live_ntp")["LiveStatuses"]

    rows = []
    for r in tpe_raw:
        rows.append({"station_id": r["StationID"], "status": r["ConnectorStatus"], "city": "taipei"})
    for r in ntp_raw:
        rows.append({"station_id": r["StationID"], "status": r["ConnectorStatus"], "city": "newtaipei"})

    df = pd.DataFrame(rows)

    # Aggregate: per station, count available / occupied / unavailable connectors
    agg = df.groupby(["station_id", "status"]).size().unstack(fill_value=0).reset_index()
    for col in [1, 2, 3]:
        if col not in agg.columns:
            agg[col] = 0
    agg = agg.rename(columns={1: "available", 2: "occupied", 3: "unavailable"})
    return agg


def load_operators(data_dir):
    tpe = load_json(data_dir, "operators_tpe")["Operators"]
    ntp = load_json(data_dir, "operators_ntp")["Operators"]
    rows = []
    for o in tpe + ntp:
        rows.append({
            "operator_id":   o.get("OperatorID"),
            "operator_name": o.get("OperatorName", {}).get("Zh_tw", ""),
        })
    return pd.DataFrame(rows).drop_duplicates("operator_id")


def build_chart1_district_count(stations_df):
    """
    Component 1 — 充電站分布圖 (EVStationChart)
    Output format:
      [{ name: "充電站數量", data: [{ x: "中正區", y: N, total_guns: M, operators: "..." }] }]
    """
    grouped = stations_df.groupby("district").agg(
        station_count=("station_id", "count"),
        total_guns=("charging_points", "sum"),
    ).reset_index().sort_values("station_count", ascending=True)

    data = []
    for _, row in grouped.iterrows():
        if pd.isna(row["district"]):
            continue
        data.append({
            "x": row["district"],
            "y": int(row["station_count"]),
            "total_guns": int(row["total_guns"]),
        })

    return [{"name": "充電站數量", "data": data}]


def build_chart2_realtime(stations_df, live_df):
    """
    Component 2 — 即時充電使用狀況 (EVRealtimeChart)
    Output format:
      [
        { name: "空閒", data: [{ x: "中正區", y: N }] },
        { name: "使用中", data: [{ x: "中正區", y: M }] }
      ]
    """
    merged = stations_df[["station_id", "district"]].merge(live_df, on="station_id", how="left")
    merged["available"] = merged["available"].fillna(0).astype(int)
    merged["occupied"] = merged["occupied"].fillna(0).astype(int)

    grouped = merged.groupby("district").agg(
        available=("available", "sum"),
        occupied=("occupied", "sum"),
    ).reset_index().sort_values("available", ascending=True)

    districts = [r["district"] for _, r in grouped.iterrows() if not pd.isna(r["district"])]
    avail_data = [{"x": r["district"], "y": int(r["available"])} for _, r in grouped.iterrows() if not pd.isna(r["district"])]
    occup_data = [{"x": r["district"], "y": int(r["occupied"])} for _, r in grouped.iterrows() if not pd.isna(r["district"])]

    return [
        {"name": "空閒", "data": avail_data},
        {"name": "使用中", "data": occup_data},
    ]


def build_geojson(stations_df, live_df, operators_df):
    """
    GeoJSON for Mapbox — one feature per station with popup properties.
    """
    merged = stations_df.merge(live_df, on="station_id", how="left")
    merged = merged.merge(operators_df, on="operator_id", how="left")
    merged["available"] = merged["available"].fillna(0).astype(int)
    merged["occupied"] = merged["occupied"].fillna(0).astype(int)
    merged["total_connectors"] = merged["available"] + merged["occupied"]
    merged["availability_pct"] = merged.apply(
        lambda r: round(r["available"] / r["total_connectors"] * 100) if r["total_connectors"] > 0 else 0,
        axis=1
    )

    features = []
    for _, r in merged.iterrows():
        if pd.isna(r["lat"]) or pd.isna(r["lon"]):
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                "station_id":       json_string(r["station_id"]),
                "station_name":     json_string(r["station_name"]),
                "district":         json_nullable_string(r.get("district")),
                "city":             json_string(r["city"]),
                "operator_name":    json_string(r.get("operator_name")),
                "charging_points":  int(r["charging_points"]),
                "available":        int(r["available"]),
                "occupied":         int(r["occupied"]),
                "availability_pct": int(r["availability_pct"]),
                "charging_rate":    json_string(r["charging_rate"]),
                "parking_rate":     json_string(r["parking_rate"]),
                "service_time":     json_string(r["service_time"]),
                "address":          json_string(r["address"]),
                "telephone":        json_string(r["telephone"]),
                "floors":           json_string(r["floors"]),
            }
        })

    return {"type": "FeatureCollection", "features": features}


def json_string(value):
    if pd.isna(value):
        return ""
    return str(value)


def json_nullable_string(value):
    if pd.isna(value):
        return None
    return str(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="Directory with downloaded TDX JSON files")
    parser.add_argument("--out-dir", default="./output", help="Output directory")
    parser.add_argument("--city", choices=["taipei", "newtaipei", "both"], default="both")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    print("Loading stations...")
    stations = load_stations(args.data_dir)
    print(f"  TPE: {len(stations[stations.city=='taipei'])} stations")
    print(f"  NTP: {len(stations[stations.city=='newtaipei'])} stations")

    print("Assigning districts via spatial join...")
    # TPE stations → taipei_town.geojson
    tpe_mask = stations["city"] == "taipei"
    ntp_mask = stations["city"] == "newtaipei"

    tpe_stations = assign_districts(stations[tpe_mask].copy(), TOWN_GEOJSON_TPE)
    ntp_stations = assign_districts(stations[ntp_mask].copy(), TOWN_GEOJSON_METRO)
    all_stations = pd.concat([tpe_stations, ntp_stations], ignore_index=True)
    print(f"  Districts assigned. Missing: {all_stations['district'].isna().sum()}")

    print("Loading live status...")
    live = load_live_status(args.data_dir)

    print("Loading operators...")
    operators = load_operators(args.data_dir)

    # ── Output for Taipei (city='taipei') ─────────────────────────────────────
    if args.city in ("taipei", "both"):
        tpe = all_stations[all_stations["city"] == "taipei"]
        tpe_live = live[live["station_id"].isin(tpe["station_id"])]

        chart1 = build_chart1_district_count(tpe)
        chart2 = build_chart2_realtime(tpe, tpe_live)
        geojson = build_geojson(tpe, tpe_live, operators)

        with open(f"{args.out_dir}/chart1_ev_station_distribution_taipei.json", "w", encoding="utf-8") as f:
            json.dump(chart1, f, ensure_ascii=False, indent=2)
        with open(f"{args.out_dir}/chart2_ev_realtime_taipei.json", "w", encoding="utf-8") as f:
            json.dump(chart2, f, ensure_ascii=False, indent=2)
        with open(f"{args.out_dir}/ev_stations_taipei.geojson", "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False)
        print(f"Taipei: {len(tpe)} stations → chart1/chart2/geojson written")

    # ── Output for Metro Taipei (city='metrotaipei', both cities) ─────────────
    if args.city in ("both",):
        metro = all_stations  # both cities combined
        metro_live = live

        chart1_m = build_chart1_district_count(metro)
        chart2_m = build_chart2_realtime(metro, metro_live)
        geojson_m = build_geojson(metro, metro_live, operators)

        with open(f"{args.out_dir}/chart1_ev_station_distribution_metrotaipei.json", "w", encoding="utf-8") as f:
            json.dump(chart1_m, f, ensure_ascii=False, indent=2)
        with open(f"{args.out_dir}/chart2_ev_realtime_metrotaipei.json", "w", encoding="utf-8") as f:
            json.dump(chart2_m, f, ensure_ascii=False, indent=2)
        with open(f"{args.out_dir}/ev_stations_metrotaipei.geojson", "w", encoding="utf-8") as f:
            json.dump(geojson_m, f, ensure_ascii=False)
        print(f"MetroTaipei: {len(metro)} stations → chart1/chart2/geojson written")

    print("\nDone! Output files:")
    for f in os.listdir(args.out_dir):
        size = os.path.getsize(f"{args.out_dir}/{f}") // 1024
        print(f"  {f}  ({size} KB)")


if __name__ == "__main__":
    main()
