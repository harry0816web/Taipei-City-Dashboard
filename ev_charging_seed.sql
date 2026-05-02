-- ============================================================
-- EV Charging Station — DB Seed SQL
-- Hackathon 2025 永續環境主題
-- Run order: components → component_charts → component_maps → query_charts
-- ============================================================

-- ── 1. components ────────────────────────────────────────────
INSERT INTO public.components (index, name)
VALUES
  ('ev_station_distribution', '電動車充電站分布'),
  ('ev_station_realtime',     '充電站即時使用狀況')
ON CONFLICT (index) DO NOTHING;

-- ── 2. component_charts ──────────────────────────────────────
INSERT INTO public.component_charts (index, color, types, unit)
VALUES (
  'ev_station_distribution',
  '{#4CAF93,#5BB8A0,#6DC1AC,#7ECAB8,#90D3C5,#A2DCD1,#B4E5DE,#C6EEEA,#D8F7F6,#EAF9F8,#C8E6C9,#A5D6A7}',
  '{MapLegend,EVStationChart}',
  '站'
) ON CONFLICT (index) DO UPDATE SET color=EXCLUDED.color, types=EXCLUDED.types, unit=EXCLUDED.unit;

INSERT INTO public.component_charts (index, color, types, unit)
VALUES (
  'ev_station_realtime',
  '{#4CAF93,#E05C5C}',
  '{MapLegend,EVRealtimeChart}',
  '槍'
) ON CONFLICT (index) DO UPDATE SET color=EXCLUDED.color, types=EXCLUDED.types, unit=EXCLUDED.unit;

-- ── 3. component_maps ────────────────────────────────────────
-- query_charts.map_config_ids below resolves these map IDs by index, so no
-- manual ID replacement is needed after inserting component_maps.

INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES (
  'ev_station_distribution',
  '電動車充電站',
  'circle',
  'geojson',
  NULL, NULL,
  '{"circle-radius": 6, "circle-color": "#4CAF93", "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5, "circle-opacity": 0.85}',
  '[{"key":"station_name","name":"充電站名稱"},{"key":"district","name":"行政區"},{"key":"operator_name","name":"營運業者"},{"key":"charging_points","name":"充電槍數"},{"key":"charging_rate","name":"充電費率"},{"key":"parking_rate","name":"停車費率"},{"key":"service_time","name":"服務時間"},{"key":"address","name":"地址"}]'
) ON CONFLICT DO NOTHING;

INSERT INTO public.component_maps (index, title, type, source, size, icon, paint, property)
VALUES (
  'ev_station_realtime',
  '充電站即時狀態',
  'circle',
  'geojson',
  NULL, NULL,
  '{"circle-radius": 7, "circle-color": ["case",[">",["get","available"],0],"#4CAF93","#E05C5C"], "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5}',
  '[{"key":"station_name","name":"充電站名稱"},{"key":"district","name":"行政區"},{"key":"available","name":"空閒槍數"},{"key":"occupied","name":"使用中槍數"},{"key":"availability_pct","name":"空閒率 (%)"},{"key":"charging_rate","name":"充電費率"},{"key":"service_time","name":"服務時間"}]'
) ON CONFLICT DO NOTHING;

-- ── 4. query_charts ──────────────────────────────────────────

DELETE FROM public.query_charts
WHERE index IN ('ev_station_distribution', 'ev_station_realtime');

-- ev_station_distribution / taipei
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'ev_station_distribution', 'taipei',
  NULL, (ARRAY[(SELECT id FROM public.component_maps WHERE index = 'ev_station_distribution' LIMIT 1)]),
  '{"mode":"byParam","byParam":{"xParam":"district"}}',
  'static', NULL, 1, 'day',
  '交通部 TDX 運輸資料流通服務',
  '臺北市各行政區電動車充電站數量分布',
  '呈現臺北市12個行政區的電動車充電站數量與充電槍總數。資料來源為交通部TDX平台，涵蓋各類充電規格（AC/DC）與多家營運商。點擊地圖站點可查看詳細費率與服務資訊。',
  '政府可透過本組件掌握充電基礎設施的空間分布，識別充電站不足的行政區，優先補充資源，推動低碳電動車普及。',
  '{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}',
  '{hackathon_team}',
  NOW(), NOW(),
  'static',
  'SELECT ''[{"name": "充電站數量", "data": [{"x": "中正區", "y": 23, "total_guns": 93}, {"x": "南港區", "y": 23, "total_guns": 146}, {"x": "大同區", "y": 24, "total_guns": 94}, {"x": "萬華區", "y": 24, "total_guns": 152}, {"x": "文山區", "y": 30, "total_guns": 110}, {"x": "內湖區", "y": 31, "total_guns": 129}, {"x": "松山區", "y": 32, "total_guns": 170}, {"x": "士林區", "y": 36, "total_guns": 136}, {"x": "北投區", "y": 37, "total_guns": 140}, {"x": "信義區", "y": 39, "total_guns": 296}, {"x": "大安區", "y": 49, "total_guns": 239}, {"x": "中山區", "y": 51, "total_guns": 232}]}]''::json AS data',
  NULL
);

-- ev_station_distribution / metrotaipei
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'ev_station_distribution', 'metrotaipei',
  NULL, (ARRAY[(SELECT id FROM public.component_maps WHERE index = 'ev_station_distribution' LIMIT 1)]),
  '{"mode":"byParam","byParam":{"xParam":"district"}}',
  'static', NULL, 1, 'day',
  '交通部 TDX 運輸資料流通服務',
  '雙北市各行政區電動車充電站數量分布',
  '呈現臺北市與新北市電動車充電站分布，共660站。',
  '比較雙北充電基礎設施密度，協助政策規劃。',
  '{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}',
  '{hackathon_team}',
  NOW(), NOW(),
  'static',
  'SELECT ''[{"name": "充電站數量", "data": [{"x": "貢寮區", "y": 1, "total_guns": 2}, {"x": "石門區", "y": 1, "total_guns": 3}, {"x": "深坑區", "y": 1, "total_guns": 3}, {"x": "坪林區", "y": 1, "total_guns": 4}, {"x": "瑞芳區", "y": 2, "total_guns": 8}, {"x": "烏來區", "y": 2, "total_guns": 11}, {"x": "五股區", "y": 2, "total_guns": 7}, {"x": "鶯歌區", "y": 3, "total_guns": 7}, {"x": "三芝區", "y": 3, "total_guns": 13}, {"x": "金山區", "y": 3, "total_guns": 10}, {"x": "泰山區", "y": 4, "total_guns": 29}, {"x": "八里區", "y": 5, "total_guns": 26}, {"x": "樹林區", "y": 5, "total_guns": 15}, {"x": "三峽區", "y": 8, "total_guns": 41}, {"x": "永和區", "y": 9, "total_guns": 77}, {"x": "汐止區", "y": 10, "total_guns": 62}, {"x": "淡水區", "y": 12, "total_guns": 52}, {"x": "蘆洲區", "y": 14, "total_guns": 47}, {"x": "林口區", "y": 18, "total_guns": 100}, {"x": "土城區", "y": 20, "total_guns": 81}, {"x": "新店區", "y": 20, "total_guns": 79}, {"x": "南港區", "y": 23, "total_guns": 146}, {"x": "中正區", "y": 23, "total_guns": 93}, {"x": "中和區", "y": 23, "total_guns": 140}, {"x": "萬華區", "y": 24, "total_guns": 152}, {"x": "大同區", "y": 24, "total_guns": 94}, {"x": "新莊區", "y": 25, "total_guns": 137}, {"x": "三重區", "y": 28, "total_guns": 123}, {"x": "文山區", "y": 30, "total_guns": 110}, {"x": "內湖區", "y": 31, "total_guns": 129}, {"x": "松山區", "y": 32, "total_guns": 170}, {"x": "士林區", "y": 36, "total_guns": 136}, {"x": "板橋區", "y": 37, "total_guns": 174}, {"x": "北投區", "y": 37, "total_guns": 140}, {"x": "信義區", "y": 39, "total_guns": 296}, {"x": "大安區", "y": 49, "total_guns": 239}, {"x": "中山區", "y": 51, "total_guns": 232}]}]''::json AS data',
  NULL
);

-- ev_station_realtime / taipei
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'ev_station_realtime', 'taipei',
  NULL, (ARRAY[(SELECT id FROM public.component_maps WHERE index = 'ev_station_realtime' LIMIT 1)]),
  '{"mode":"byParam","byParam":{"xParam":"district"}}',
  'static', NULL, 5, 'minute',
  '交通部 TDX 運輸資料流通服務',
  '臺北市充電站即時使用率',
  '以行政區彙整充電槍空閒與使用中數量。地圖綠色=有空位，紅色=全滿。ConnectorStatus: 1=空閒, 2=使用中, 3=不可用。',
  '市民即時查詢鄰近充電站使用情形，減少尋站時間，提升電動車便利性。',
  '{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}',
  '{hackathon_team}',
  NOW(), NOW(),
  'static',
  'SELECT ''[{"name": "空閒", "data": [{"x": "大同區", "y": 42}, {"x": "中正區", "y": 44}, {"x": "文山區", "y": 52}, {"x": "中山區", "y": 79}, {"x": "內湖區", "y": 82}, {"x": "南港區", "y": 88}, {"x": "士林區", "y": 88}, {"x": "松山區", "y": 91}, {"x": "北投區", "y": 93}, {"x": "萬華區", "y": 101}, {"x": "信義區", "y": 133}, {"x": "大安區", "y": 146}]}, {"name": "使用中", "data": [{"x": "大同區", "y": 38}, {"x": "中正區", "y": 38}, {"x": "文山區", "y": 20}, {"x": "中山區", "y": 65}, {"x": "內湖區", "y": 15}, {"x": "南港區", "y": 43}, {"x": "士林區", "y": 39}, {"x": "松山區", "y": 52}, {"x": "北投區", "y": 29}, {"x": "萬華區", "y": 21}, {"x": "信義區", "y": 116}, {"x": "大安區", "y": 69}]}]''::json AS data',
  NULL
);

-- ev_station_realtime / metrotaipei
INSERT INTO public.query_charts
  (index, city, history_config, map_config_ids, map_filter, time_from, time_to,
   update_freq, update_freq_unit, source, short_desc, long_desc, use_case,
   links, contributors, created_at, updated_at, query_type, query_chart, query_history)
VALUES (
  'ev_station_realtime', 'metrotaipei',
  NULL, (ARRAY[(SELECT id FROM public.component_maps WHERE index = 'ev_station_realtime' LIMIT 1)]),
  '{"mode":"byParam","byParam":{"xParam":"district"}}',
  'static', NULL, 5, 'minute',
  '交通部 TDX 運輸資料流通服務',
  '雙北充電站即時使用率',
  '雙北660站充電槍空閒與使用中彙整。',
  '政府掌握雙北充電需求熱點，規劃充電基礎設施擴建優先區域。',
  '{https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8}',
  '{hackathon_team}',
  NOW(), NOW(),
  'static',
  'SELECT ''[{"name": "空閒", "data": [{"x": "鶯歌區", "y": 0}, {"x": "瑞芳區", "y": 1}, {"x": "深坑區", "y": 1}, {"x": "貢寮區", "y": 2}, {"x": "烏來區", "y": 2}, {"x": "石門區", "y": 3}, {"x": "五股區", "y": 3}, {"x": "坪林區", "y": 4}, {"x": "金山區", "y": 4}, {"x": "樹林區", "y": 8}, {"x": "三芝區", "y": 11}, {"x": "泰山區", "y": 12}, {"x": "八里區", "y": 14}, {"x": "永和區", "y": 15}, {"x": "蘆洲區", "y": 23}, {"x": "淡水區", "y": 23}, {"x": "三峽區", "y": 34}, {"x": "土城區", "y": 37}, {"x": "新店區", "y": 41}, {"x": "大同區", "y": 42}, {"x": "中正區", "y": 44}, {"x": "汐止區", "y": 46}, {"x": "文山區", "y": 52}, {"x": "三重區", "y": 59}, {"x": "林口區", "y": 65}, {"x": "新莊區", "y": 79}, {"x": "中山區", "y": 79}, {"x": "中和區", "y": 80}, {"x": "內湖區", "y": 82}, {"x": "士林區", "y": 88}, {"x": "南港區", "y": 88}, {"x": "板橋區", "y": 89}, {"x": "松山區", "y": 91}, {"x": "北投區", "y": 93}, {"x": "萬華區", "y": 101}, {"x": "信義區", "y": 133}, {"x": "大安區", "y": 146}]}, {"name": "使用中", "data": [{"x": "鶯歌區", "y": 5}, {"x": "瑞芳區", "y": 7}, {"x": "深坑區", "y": 2}, {"x": "貢寮區", "y": 0}, {"x": "烏來區", "y": 6}, {"x": "石門區", "y": 0}, {"x": "五股區", "y": 4}, {"x": "坪林區", "y": 0}, {"x": "金山區", "y": 6}, {"x": "樹林區", "y": 7}, {"x": "三芝區", "y": 2}, {"x": "泰山區", "y": 17}, {"x": "八里區", "y": 12}, {"x": "永和區", "y": 60}, {"x": "蘆洲區", "y": 20}, {"x": "淡水區", "y": 26}, {"x": "三峽區", "y": 10}, {"x": "土城區", "y": 42}, {"x": "新店區", "y": 42}, {"x": "大同區", "y": 38}, {"x": "中正區", "y": 38}, {"x": "汐止區", "y": 12}, {"x": "文山區", "y": 20}, {"x": "三重區", "y": 62}, {"x": "林口區", "y": 34}, {"x": "新莊區", "y": 32}, {"x": "中山區", "y": 65}, {"x": "中和區", "y": 62}, {"x": "內湖區", "y": 15}, {"x": "士林區", "y": 39}, {"x": "南港區", "y": 43}, {"x": "板橋區", "y": 96}, {"x": "松山區", "y": 52}, {"x": "北投區", "y": 29}, {"x": "萬華區", "y": 21}, {"x": "信義區", "y": 116}, {"x": "大安區", "y": 69}]}]''::json AS data',
  NULL
);
