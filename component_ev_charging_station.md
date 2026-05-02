# 組件說明：電動車充電站分布與即時使用狀況

> **負責人參考文件** — 請詳讀後再開始實作

---

## 一、背景與用途

### 比賽資訊

| 項目 | 內容 |
|------|------|
| 比賽名稱 | 2025 臺北市暨新北市程式設計節 城市儀表板黑客松 |
| 主辦單位 | 臺北市政府資訊局 / 臺北大數據中心（TUIC） |
| 主題分類 | **永續環境** — 整合環境監測、能源使用與碳排相關資料，協助政府推動低碳政策並引導市民參與環境保護行動 |
| 報名/活動頁 | https://codefest.taipei |

### 目標平台

| 項目 | 內容 |
|------|------|
| 平台名稱 | 臺北城市儀表板（Taipei City Dashboard） |
| 對外網址 | https://citydashboard.taipei |
| 官方文件 | https://citydashboard.taipei/documentation |
| Contribution 指南 | https://citydashboard.taipei/documentation/front-end/contribution-overview |
| 主要 GitHub（官方） | https://github.com/taipei-doit/Taipei-City-Dashboard |
| 我們的 Fork | https://github.com/harry0816web/Taipei-City-Dashboard |

### 這兩個組件在做什麼

**組件一：電動車充電站分布 (`ev_station_distribution`)**
呈現雙北各行政區的電動車充電站數量與充電槍總數，搭配地圖可點選各站點查看詳細資訊（費率、服務時間、營運商等）。

**組件二：充電站即時使用狀況 (`ev_station_realtime`)**
以行政區彙整充電槍的即時空閒與使用中數量，地圖以顏色標示各站點即時狀態（綠=有空位、紅=全滿），協助市民快速找到可用充電站。

兩個組件均符合「低碳交通基礎設施」定位——電動車普及是城市低碳轉型的核心，提升充電站能見度可直接引導市民選擇電動車。

---

## 二、組件規格

### 組件一：電動車充電站分布

| 項目 | 規格 |
|------|------|
| index | `ev_station_distribution` |
| 圖表類型 | `MapLegend`（地圖圖例）+ `EVStationChart`（各區充電站橫向長條圖） |
| 更新頻率 | 每日（API 核准後）/ 靜態（目前） |
| 地圖圖層 | circle — 固定綠色，點擊 popup 顯示站點詳情 |
| 支援城市 | taipei / metrotaipei |

### 組件二：充電站即時使用狀況

| 項目 | 規格 |
|------|------|
| index | `ev_station_realtime` |
| 圖表類型 | `MapLegend`（綠/紅圖例）+ `EVRealtimeChart`（各區空閒率堆疊百分比圖） |
| 更新頻率 | 每 5 分鐘（API 核准後）/ 靜態（目前） |
| 地圖圖層 | circle — 依 `available > 0` 動態切換綠/紅色 |
| 支援城市 | taipei / metrotaipei |

---

## 三、資料來源

### 3-1 TDX 電動車充電站 API

- **來源**：交通部 TDX 運輸資料流通服務平台
- **Swagger 文件**：https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8
- **費用**：免費（需申請 API Token）
- **⚠️ 目前狀態**：API 帳號審核中，現用下載靜態資料

| Endpoint | 說明 | 使用於 |
|----------|------|--------|
| `GET /v1/EV/Station/City/{City}` | 充電站基本資料（位置、槍數、費率） | 組件一 + 二 |
| `GET /v1/EV/ConnectorLiveStatus/City/{City}` | 充電槍即時狀態 | 組件二 |
| `GET /v1/EV/ChargingRate/City/{City}` | 充電費率明細 | 參考用 |
| `GET /v1/EV/Operator/City/{City}` | 營運業者資料 | 組件一 tooltip |
| `GET /v1/EV/ChargingPoint/City/{City}` | 充電樁基本資料 | 參考用 |
| `GET /v1/EV/Connector/City/{City}` | 充電槍規格 | 參考用 |
| `GET /v1/EV/ParkingRate/City/{City}` | 停車費率 | 參考用 |
| `GET /v1/EV/ServiceTime/City/{City}` | 服務時間 | 參考用 |

**City 參數**：`Taipei`（臺北市）、`NewTaipei`（新北市）

**ConnectorStatus 代碼**：

| 值 | 意義 |
|----|------|
| 1 | Available — 空閒 |
| 2 | Occupied — 使用中 |
| 3 | Unavailable — 不可用 / 故障 |

### 3-2 API 認證方式（TDX OAuth2）

```bash
# Step 1: 取得 Access Token（有效期 24 小時）
curl -X POST \
  https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token \
  -H 'content-type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET'

# Step 2: 呼叫 API
curl -X GET \
  'https://tdx.transportdata.tw/api/basic/v1/EV/Station/City/Taipei?$format=JSON' \
  -H 'Authorization: Bearer ACCESS_TOKEN'
```

未申請帳號時：每 IP 每日可免費呼叫 50 次（無需 token）。

### 3-3 已下載靜態資料（現用）

| 檔案 | 對應 API | 內容 |
|------|----------|------|
| `data/static/taipei_station.json` | Station / Taipei | 臺北市 403 站 |
| `data/static/newtaipei_station.json` | Station / NewTaipei | 新北市 257 站 |
| `data/static/taipei_connector_live_status.json` | ConnectorLiveStatus / Taipei | 臺北市 1,587 筆充電槍狀態 |
| `data/static/newtaipei_connector_live_status.json` | ConnectorLiveStatus / NewTaipei | 新北市 1,256 筆充電槍狀態 |
| `data/static/taipei_service_time.json` | ServiceTime / Taipei | 臺北市 403 筆服務時間 |
| `data/static/newtaipei_service_time.json` | ServiceTime / NewTaipei | 新北市 257 筆服務時間 |
| `data/static/taipei_parking_rate.json` | ParkingRate / Taipei | 臺北市 389 筆停車費率 |
| `data/static/newtaipei_parking_rate.json` | ParkingRate / NewTaipei | 新北市 256 筆停車費率 |
| `data/static/taipei_operator.json` | Operator / Taipei | 臺北市 84 家營運商 |
| `data/static/newtaipei_operator.json` | Operator / NewTaipei | 新北市 54 家營運商 |
| `data/static/taipei_connector.json` | Connector / Taipei | 臺北市 1,625 筆充電槍規格 |
| `data/static/newtaipei_connector.json` | Connector / NewTaipei | 新北市 1,299 筆充電槍規格 |
| `data/static/taipei_charging_rate.json` | ChargingRate / Taipei | 臺北市 1,742 筆充電費率 |
| `data/static/newtaipei_charging_rate.json` | ChargingRate / NewTaipei | 新北市 1,298 筆充電費率 |
| `data/static/taipei_charging_point.json` | ChargingPoint / Taipei | 臺北市 1,710 個充電樁 |
| `data/static/newtaipei_charging_point.json` | ChargingPoint / NewTaipei | 新北市 1,260 個充電樁 |

**資料下載時間**：2026-05-02。原始 `response_*.json` 已重新命名並放在 `Taipei-City-Dashboard-DE/dags/proj_city_dashboard/ev_charging_station/data/static/`；`response_1777703087046.json` 未含可用 endpoint payload，未納入。

### 3-4 行政區界 GeoJSON（空間 join 用）

- **來源**：Taipei City Dashboard 內建
- **臺北市**：`Taipei-City-Dashboard-FE/public/mapData/taipei_town.geojson`（12 個行政區）
- **雙北**：`Taipei-City-Dashboard-FE/public/mapData/metrotaipei_town.geojson`

---

## 四、ETL 計算邏輯

### Step 1 — 載入充電站資料

```python
# 從 TDX API 或靜態 JSON 取得 Station 清單
stations = pd.DataFrame([flatten_station(s, city) for s in raw["Stations"]])
# 關鍵欄位：station_id, lat, lon, operator_id, charging_points, charging_rate
```

### Step 2 — 空間 join 取得行政區

```python
import geopandas as gpd
from shapely.geometry import Point

towns = gpd.read_file("taipei_town.geojson")[["TNAME", "geometry"]].to_crs("EPSG:4326")
gdf = gpd.GeoDataFrame(stations, geometry=[Point(lon, lat) for lon, lat in ...], crs="EPSG:4326")
joined = gpd.sjoin(gdf, towns, how="left", predicate="within")
stations["district"] = joined["TNAME"].values
# 結果：約 4 筆缺行政區（邊界外或資料異常），其餘全部命中
```

### Step 3 — 彙整充電槍即時狀態

```python
# ConnectorStatus: 1=空閒, 2=使用中, 3=不可用
live_agg = live_df.groupby(["station_id", "status"]).size().unstack(fill_value=0)
live_agg.rename(columns={1: "available", 2: "occupied", 3: "unavailable"})
```

### Step 4 — 產生組件一 chart_data（各行政區站數）

```python
chart1 = [{"name": "充電站數量", "data": [
    {"x": district, "y": station_count, "total_guns": total_guns}
    for district in sorted_districts
]}]
```

### Step 5 — 產生組件二 chart_data（各行政區空閒率）

```python
chart2 = [
    {"name": "空閒",   "data": [{"x": d, "y": available_count} for d in districts]},
    {"name": "使用中", "data": [{"x": d, "y": occupied_count}  for d in districts]},
]
```

### Step 6 — 產生地圖 GeoJSON

每個充電站一個 Feature，properties 包含站名、行政區、空閒槍數、費率等，供 Mapbox popup 使用。

---

## 五、資料統計（2026-05-02 快照）

| 項目 | 臺北市 | 新北市 | 雙北合計 |
|------|--------|--------|----------|
| 充電站數 | 399 | 257 | 656 |
| 充電槍數 | 1,937 | — | — |
| 即時空閒槍 | 1,039 | 656 | — |
| 即時使用中槍 | 545 | 566 | — |
| 全市空閒率 | **66%** | 54% | — |

---

## 六、前端組件規格

### EVStationChart.vue（組件一非地圖視圖）

```
位置: Taipei-City-Dashboard-FE/src/dashboardComponent/components/EVStationChart.vue
activeChart 值: 'EVStationChart'
```

- 橫向長條圖，依行政區排序
- 頂部摘要列：全市充電站數 / 充電槍數 / 最多站點行政區
- 自訂 tooltip：顯示充電槍數、營運商
- 點擊長條 → 篩選地圖對應行政區（map_filter byParam）

**series 格式**：
```json
[{
  "name": "充電站數量",
  "data": [
    { "x": "中正區", "y": 23, "total_guns": 93 },
    ...
  ]
}]
```

### EVRealtimeChart.vue（組件二非地圖視圖）

```
位置: Taipei-City-Dashboard-FE/src/dashboardComponent/components/EVRealtimeChart.vue
activeChart 值: 'EVRealtimeChart'
```

- 100% 堆疊橫向長條圖（空閒 vs 使用中）
- 固定配色：綠 `#4CAF93` = 空閒，紅 `#E05C5C` = 使用中
- 頂部顯示全市即時空閒率（%），依比例變色：≥50% 綠、≥25% 黃、<25% 紅
- tooltip 顯示各區空閒槍數、使用中槍數、空閒率

**series 格式**：
```json
[
  { "name": "空閒",   "data": [{ "x": "中正區", "y": 44 }, ...] },
  { "name": "使用中", "data": [{ "x": "中正區", "y": 38 }, ...] }
]
```

### MapLegend（地圖視圖）

組件一地圖：固定綠色圓點，點擊 popup 顯示站點全部詳情。
組件二地圖：綠色（`available > 0`）/ 紅色（全滿）動態配色。

---

## 七、檔案結構

```
Taipei-City-Dashboard-develop/
│
├── component_ev_charging_station.md          ← 本文件
├── ev_charging_seed.sql                      ← DB 匯入 SQL
│
├── Taipei-City-Dashboard-FE/
│   ├── public/mapData/
│   │   ├── ev_stations_taipei.geojson        ← 臺北市 399 站 GeoJSON
│   │   └── ev_stations_metrotaipei.geojson   ← 雙北 656 站 GeoJSON
│   └── src/dashboardComponent/
│       ├── components/
│       │   ├── EVStationChart.vue            ← 組件一圖表
│       │   └── EVRealtimeChart.vue           ← 組件二圖表
│       ├── DashboardComponent.vue            ← 已加入 import + switch case
│       └── utilities/chartTypes.ts           ← 已加入 EVStationChart / EVRealtimeChart
│
└── Taipei-City-Dashboard-DE/dags/
    └── proj_city_dashboard/ev_charging_station/
        ├── __init__.py
        ├── job_config.json                   ← DAG 設定（含 API 文件）
        ├── ev_charging_station.py            ← Airflow DAG（API 核准後啟用）
        └── etl_static.py                     ← 靜態資料 ETL 腳本（現用）
```

---

## 八、部署流程

### 現在（靜態資料）

```bash
# 1. 執行靜態 ETL（已完成，輸出已存入 mapData/）
python etl_static.py \
  --out-dir ./output

# 2. 匯入 DB（map_config_ids 會用 component_maps.index 自動查 ID）
psql $DATABASE_URL < ev_charging_seed.sql
```

### API 核准後（切換到 Live DAG）

```bash
# 1. 將 TDX Client ID / Secret 設定為 Airflow Variables 或 Connections
# 2. 在 Airflow UI 啟用 ev_charging_station DAG
# 3. 修改 query_chart 欄位從 'static' 改為 'two_d'，使用真實 DB 查詢
```

---

## 九、DB Schema 對照

依照 `db.md` 的格式：

### components 表

| index | name | query_type |
|-------|------|------------|
| `ev_station_distribution` | 電動車充電站分布 | `two_d` |
| `ev_station_realtime` | 充電站即時使用狀況 | `two_d` |

### component_charts 表

| index | color | types | unit |
|-------|-------|-------|------|
| `ev_station_distribution` | `{#4CAF93,...}` (12色漸層) | `{MapLegend,EVStationChart}` | 站 |
| `ev_station_realtime` | `{#4CAF93,#E05C5C}` | `{MapLegend,EVRealtimeChart}` | 槍 |

### component_maps 表

| index | title | type | paint |
|-------|-------|------|-------|
| `ev_station_distribution` | 電動車充電站 | circle | 固定 `#4CAF93` |
| `ev_station_realtime` | 充電站即時狀態 | circle | case available>0 → 綠 / 紅 |

### query_charts 表

city 必須是 `taipei` 或 `metrotaipei`，每個 index 各兩筆。

---

## 十、注意事項

| 項目 | 說明 |
|------|------|
| 靜態資料時間戳記 | 快照時間為 2026-05-02，不代表即時狀態 |
| 4 筆缺行政區的站點 | 座標落在行政區邊界外，district 為 NULL，已從圖表排除 |
| ConnectorStatus=3 | 故障/不可用，比例極低（TPE 1 筆，NTP 34 筆），計算時排除 |
| GeoJSON 大小 | 雙北 393KB、臺北 238KB，Mapbox 可直接載入 |
| 新北市 API City 參數 | 使用 `NewTaipei`（非 `New-Taipei`） |
| 永續主題定位 | 說明文字需標注：「充電站普及率直接影響市民選擇電動車的意願，是城市低碳轉型的關鍵指標」 |

---

## 十一、參考資料

- TDX 運輸資料流通服務 Swagger：https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8
- TDX 新手上路指引：https://motc-ptx.gitbook.io/tdx-xin-shou-zhi-yin
- TDX GitHub 範例程式碼：https://github.com/tdxmotc/SampleCode
- 臺北城市儀表板組件開發文件：https://citydashboard.taipei/documentation/data-end/dag-code
- GeoPandas 官方文件：https://geopandas.org

---

*最後更新：2026-05-02*
