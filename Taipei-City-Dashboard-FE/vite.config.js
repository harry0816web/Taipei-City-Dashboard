import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import viteCompression from "vite-plugin-compression";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ── Hackathon Mock Plugin ─────────────────────────────────────────────────────
// Serves our EV charging station dashboard components without a running backend.
// Also aliases ev_realtime_*.geojson → ev_stations_*.geojson so both layers
// use separate Mapbox sources (prevents the solid-green distribution layer from
// masking the colour-coded realtime layer).
function evMockPlugin() {

	// ── Chart data (extracted from ev_charging_seed.sql) ──────────────────────
	const CHART1_TPE = [{"name":"充電站數量","data":[{"x":"中正區","y":23,"total_guns":93},{"x":"南港區","y":23,"total_guns":146},{"x":"大同區","y":24,"total_guns":94},{"x":"萬華區","y":24,"total_guns":152},{"x":"文山區","y":30,"total_guns":110},{"x":"內湖區","y":31,"total_guns":129},{"x":"松山區","y":32,"total_guns":170},{"x":"士林區","y":36,"total_guns":136},{"x":"北投區","y":37,"total_guns":140},{"x":"信義區","y":39,"total_guns":296},{"x":"大安區","y":49,"total_guns":239},{"x":"中山區","y":51,"total_guns":232}]}];
	const CHART2_TPE = [{"name":"空閒","data":[{"x":"大同區","y":42},{"x":"中正區","y":44},{"x":"文山區","y":52},{"x":"中山區","y":79},{"x":"內湖區","y":82},{"x":"南港區","y":88},{"x":"士林區","y":88},{"x":"松山區","y":91},{"x":"北投區","y":93},{"x":"萬華區","y":101},{"x":"信義區","y":133},{"x":"大安區","y":146}]},{"name":"使用中","data":[{"x":"大同區","y":38},{"x":"中正區","y":38},{"x":"文山區","y":20},{"x":"中山區","y":65},{"x":"內湖區","y":15},{"x":"南港區","y":43},{"x":"士林區","y":39},{"x":"松山區","y":52},{"x":"北投區","y":29},{"x":"萬華區","y":21},{"x":"信義區","y":116},{"x":"大安區","y":69}]}];
	const CHART1_METRO = [{"name":"充電站數量","data":[{"x":"貢寮區","y":1,"total_guns":2},{"x":"石門區","y":1,"total_guns":3},{"x":"深坑區","y":1,"total_guns":3},{"x":"坪林區","y":1,"total_guns":4},{"x":"瑞芳區","y":2,"total_guns":8},{"x":"烏來區","y":2,"total_guns":11},{"x":"五股區","y":2,"total_guns":7},{"x":"鶯歌區","y":3,"total_guns":7},{"x":"三芝區","y":3,"total_guns":13},{"x":"金山區","y":3,"total_guns":10},{"x":"泰山區","y":4,"total_guns":29},{"x":"八里區","y":5,"total_guns":26},{"x":"樹林區","y":5,"total_guns":15},{"x":"三峽區","y":8,"total_guns":41},{"x":"永和區","y":9,"total_guns":77},{"x":"汐止區","y":10,"total_guns":62},{"x":"淡水區","y":12,"total_guns":52},{"x":"蘆洲區","y":14,"total_guns":47},{"x":"林口區","y":18,"total_guns":100},{"x":"土城區","y":20,"total_guns":81},{"x":"新店區","y":20,"total_guns":79},{"x":"南港區","y":23,"total_guns":146},{"x":"中正區","y":23,"total_guns":93},{"x":"中和區","y":23,"total_guns":140},{"x":"萬華區","y":24,"total_guns":152},{"x":"大同區","y":24,"total_guns":94},{"x":"新莊區","y":25,"total_guns":137},{"x":"三重區","y":28,"total_guns":123},{"x":"文山區","y":30,"total_guns":110},{"x":"內湖區","y":31,"total_guns":129},{"x":"松山區","y":32,"total_guns":170},{"x":"士林區","y":36,"total_guns":136},{"x":"板橋區","y":37,"total_guns":174},{"x":"北投區","y":37,"total_guns":140},{"x":"信義區","y":39,"total_guns":296},{"x":"大安區","y":49,"total_guns":239},{"x":"中山區","y":51,"total_guns":232}]}];
	const CHART2_METRO = [{"name":"空閒","data":[{"x":"鶯歌區","y":0},{"x":"瑞芳區","y":1},{"x":"深坑區","y":1},{"x":"貢寮區","y":2},{"x":"烏來區","y":2},{"x":"石門區","y":3},{"x":"五股區","y":3},{"x":"坪林區","y":4},{"x":"金山區","y":4},{"x":"樹林區","y":8},{"x":"三芝區","y":11},{"x":"泰山區","y":12},{"x":"八里區","y":14},{"x":"永和區","y":15},{"x":"蘆洲區","y":23},{"x":"淡水區","y":23},{"x":"三峽區","y":34},{"x":"土城區","y":37},{"x":"新店區","y":41},{"x":"大同區","y":42},{"x":"中正區","y":44},{"x":"汐止區","y":46},{"x":"文山區","y":52},{"x":"三重區","y":59},{"x":"林口區","y":65},{"x":"新莊區","y":79},{"x":"中山區","y":79},{"x":"中和區","y":80},{"x":"內湖區","y":82},{"x":"士林區","y":88},{"x":"南港區","y":88},{"x":"板橋區","y":89},{"x":"松山區","y":91},{"x":"北投區","y":93},{"x":"萬華區","y":101},{"x":"信義區","y":133},{"x":"大安區","y":146}]},{"name":"使用中","data":[{"x":"鶯歌區","y":5},{"x":"瑞芳區","y":7},{"x":"深坑區","y":2},{"x":"貢寮區","y":0},{"x":"烏來區","y":6},{"x":"石門區","y":0},{"x":"五股區","y":4},{"x":"坪林區","y":0},{"x":"金山區","y":6},{"x":"樹林區","y":7},{"x":"三芝區","y":2},{"x":"泰山區","y":17},{"x":"八里區","y":12},{"x":"永和區","y":60},{"x":"蘆洲區","y":20},{"x":"淡水區","y":26},{"x":"三峽區","y":10},{"x":"土城區","y":42},{"x":"新店區","y":42},{"x":"大同區","y":38},{"x":"中正區","y":38},{"x":"汐止區","y":12},{"x":"文山區","y":20},{"x":"三重區","y":62},{"x":"林口區","y":34},{"x":"新莊區","y":32},{"x":"中山區","y":65},{"x":"中和區","y":62},{"x":"內湖區","y":15},{"x":"士林區","y":39},{"x":"南港區","y":43},{"x":"板橋區","y":96},{"x":"松山區","y":52},{"x":"北投區","y":29},{"x":"萬華區","y":21},{"x":"信義區","y":116},{"x":"大安區","y":69}]}];

	// ── Map paint ─────────────────────────────────────────────────────────────
	// Distribution: subtle hollow-style circles — won't mask the realtime layer
	const PAINT_DIST = {
		"circle-radius": 5,
		"circle-color": "#4CAF93",
		"circle-opacity": 0.5,
		"circle-stroke-color": "#4CAF93",
		"circle-stroke-width": 1.5,
	};
	// Realtime: 3-colour scale based on availability_pct
	//   Red  < 30 %  →  mostly occupied
	//   Orange 30–59 %  →  moderate
	//   Green ≥ 60 %  →  mostly free
	const PAINT_LIVE = {
		"circle-radius": 7,
		"circle-color": ["step", ["get", "availability_pct"],
			"#E05C5C",   // 0 – 29 %
			30, "#FFA726",   // 30 – 59 %
			60, "#4CAF93"    // 60 %+
		],
		"circle-stroke-color": "#ffffff",
		"circle-stroke-width": 1.5,
		"circle-opacity": 0.9,
	};

	// ── Popup property definitions ────────────────────────────────────────────
	const PROP_DIST = [
		{ key: "station_name",    name: "充電站名稱" },
		{ key: "district",        name: "行政區" },
		{ key: "operator_name",   name: "營運業者" },
		{ key: "charging_points", name: "充電槍總數" },
		{ key: "charging_rate",   name: "充電費率" },
		{ key: "parking_rate",    name: "停車費率" },
		{ key: "service_time",    name: "服務時間" },
		{ key: "address",         name: "地址" },
	];
	const PROP_LIVE = [
		{ key: "station_name",     name: "充電站名稱" },
		{ key: "district",         name: "行政區" },
		{ key: "charging_points",  name: "充電槍總數" },
		{ key: "available",        name: "目前空閒" },
		{ key: "occupied",         name: "目前使用中" },
		{ key: "availability_pct", name: "空閒率 (%)" },
		{ key: "charging_rate",    name: "充電費率" },
		{ key: "service_time",     name: "服務時間" },
	];

	// ── Component definitions ─────────────────────────────────────────────────
	function makeDistComp(id, city, geojsonIndex, chartData) {
		return {
			id, index: "ev_station_distribution",
			name: "電動車充電站分布", city,
			chart_config: {
				index: "ev_station_distribution",
				color: ["#4CAF93","#5BB8A0","#6DC1AC","#7ECAB8","#90D3C5","#A2DCD1","#B4E5DE","#C6EEEA","#D8F7F6","#EAF9F8","#C8E6C9","#A5D6A7"],
				types: ["MapLegend", "EVStationChart"],
				unit: "站",
			},
			history_config: null,
			map_config: [{
				id: id * 10, index: geojsonIndex, title: "電動車充電站",
				type: "circle", source: "geojson", size: null, icon: null,
				paint: PAINT_DIST, property: PROP_DIST, city,
			}],
			map_filter: { mode: "byParam", byParam: { xParam: "district" } },
			time_from: "static", time_to: null, update_freq: 1, update_freq_unit: "day",
			source: "交通部 TDX 運輸資料流通服務",
			short_desc: city === "taipei" ? "臺北市各行政區電動車充電站數量分布" : "雙北各行政區電動車充電站數量分布",
			long_desc: "呈現各行政區的電動車充電站數量與充電槍總數。資料來源為交通部TDX平台，涵蓋各類充電規格（AC/DC）與多家營運商。點擊地圖站點可查看詳細費率與服務資訊。",
			use_case: "政府可透過本組件掌握充電基礎設施的空間分布，識別充電站不足的行政區，優先補充資源，推動低碳電動車普及。",
			links: ["https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8"],
			contributors: ["hackathon_team"],
			updated_at: "2026-05-02T00:00:00Z", query_type: "static",
		};
	}

	function makeLiveComp(id, city, geojsonIndex, chartData) {
		return {
			id, index: "ev_station_realtime",
			name: "充電站即時使用狀況", city,
			chart_config: {
				index: "ev_station_realtime",
				color: ["#4CAF93", "#E05C5C"],
				types: ["MapLegend", "EVRealtimeChart"],
				unit: "槍",
			},
			history_config: null,
			map_config: [{
				id: id * 10, index: geojsonIndex, title: "充電站即時狀態",
				type: "circle", source: "geojson", size: null, icon: null,
				paint: PAINT_LIVE, property: PROP_LIVE, city,
			}],
			map_filter: { mode: "byParam", byParam: { xParam: "district" } },
			time_from: "static", time_to: null, update_freq: 5, update_freq_unit: "minute",
			source: "交通部 TDX 運輸資料流通服務",
			short_desc: city === "taipei" ? "臺北市充電站即時使用率" : "雙北充電站即時使用率",
			long_desc: "以行政區彙整充電槍空閒與使用中數量。地圖綠色=空閒充足，橘色=部分空閒，紅色=幾乎全滿。ConnectorStatus: 1=空閒, 2=使用中, 3=不可用。",
			use_case: "市民即時查詢鄰近充電站使用情形，減少尋站時間，提升電動車便利性。",
			links: ["https://tdx.transportdata.tw/api-service/swagger/basic/b378d320-04a9-4fba-80b8-0df1b96dd5e8"],
			contributors: ["hackathon_team"],
			updated_at: "2026-05-02T00:00:00Z", query_type: "static",
		};
	}

	// IDs & GeoJSON sources:
	//   9001 = TPE distribution  → ev_stations_taipei.geojson
	//   9002 = TPE realtime      → ev_realtime_taipei.geojson   (alias, separate Mapbox source)
	//   9003 = METRO distribution → ev_stations_metrotaipei.geojson
	//   9004 = METRO realtime     → ev_realtime_metrotaipei.geojson (alias)
	const C9001 = makeDistComp(9001, "taipei",      "ev_stations_taipei",      CHART1_TPE);
	const C9002 = makeLiveComp(9002, "taipei",      "ev_realtime_taipei",      CHART2_TPE);
	const C9003 = makeDistComp(9003, "metrotaipei", "ev_stations_metrotaipei", CHART1_METRO);
	const C9004 = makeLiveComp(9004, "metrotaipei", "ev_realtime_metrotaipei", CHART2_METRO);

	const DASHBOARD_LIST = {
		public: [],
		taipei: [{
			index: "ev_sustainability",
			name: "永續環境 — 電動車充電站",
			components: [9001, 9002],
			icon: "energy_savings_leaf",
			updated_at: "2026-05-02T00:00:00Z",
		}],
		metrotaipei: [{
			index: "ev_metro",
			name: "永續環境 — 雙北電動車充電站",
			components: [9003, 9004],
			icon: "energy_savings_leaf",
			updated_at: "2026-05-02T00:00:00Z",
		}],
		personal: [],
	};

	// ── GeoJSON aliases (serve same data under a second filename) ─────────────
	const GEOJSON_ALIASES = {
		"/mapData/ev_realtime_taipei.geojson":      "ev_stations_taipei.geojson",
		"/mapData/ev_realtime_metrotaipei.geojson": "ev_stations_metrotaipei.geojson",
	};

	// ── Respond helper ────────────────────────────────────────────────────────
	function json(res, body) {
		res.setHeader("Content-Type", "application/json; charset=utf-8");
		res.end(JSON.stringify(body));
	}

	return {
		name: "ev-mock",
		configureServer(server) {
			server.middlewares.use((req, res, next) => {
				const url = req.url.split("?")[0];

				// GeoJSON aliases — must be intercepted BEFORE Vite's static handler
				if (GEOJSON_ALIASES[url]) {
					const target = path.join(__dirname, "public/mapData", GEOJSON_ALIASES[url]);
					try {
						const data = fs.readFileSync(target);
						res.setHeader("Content-Type", "application/json");
						res.end(data);
					} catch (e) {
						res.statusCode = 404;
						res.end(`GeoJSON not found: ${target}`);
					}
					return;
				}

				// Dashboard list
				if (url === "/api/dashboard" || url === "/api/dashboard/") {
					return json(res, { status: "success", data: DASHBOARD_LIST });
				}
				// Taipei EV dashboard
				if (url === "/api/dashboard/ev_sustainability") {
					return json(res, { status: "success", data: [C9001, C9002] });
				}
				// MetroTaipei EV dashboard
				if (url === "/api/dashboard/ev_metro") {
					return json(res, { status: "success", data: [C9003, C9004] });
				}
				// Map layer lists (mapview page)
				if (url.startsWith("/api/dashboard/map-layers-")) {
					return json(res, { status: "success", data: [] });
				}
				// Chart data
				if (url === "/api/component/9001/chart") return json(res, { status: "success", data: CHART1_TPE });
				if (url === "/api/component/9002/chart") return json(res, { status: "success", data: CHART2_TPE });
				if (url === "/api/component/9003/chart") return json(res, { status: "success", data: CHART1_METRO });
				if (url === "/api/component/9004/chart") return json(res, { status: "success", data: CHART2_METRO });
				// Contributors
				if (url === "/api/contributor" || url === "/api/contributor/") {
					return json(res, { status: "success", data: [] });
				}

				next();
			});
		},
	};
}

// ── Vite server config ────────────────────────────────────────────────────────
let isDockerCompose = process?.env.DOCKER_COMPOSE === "true"; // eslint-disable-line no-undef

const serverConfig = isDockerCompose
	? {
		host: "0.0.0.0",
		port: 80,
		proxy: {
			"/api/dev": {
				target: "http://dashboard-be:8080",
				changeOrigin: true,
				rewrite: (path) => path.replace("/dev", "/v1"),
			},
		},
	}
	: {
		host: "0.0.0.0",
		port: 80,
		proxy: {
			"/api": {
				target: "https://citydashboard.taipei/api/v1",
				changeOrigin: true,
				secure: false,
				rewrite: (path) => path.replace(/^\/api/, ""),
			},
			"/geo_server": {
				target: "https://citydashboard.taipei/geo_server/",
				changeOrigin: true,
				secure: false,
				rewrite: (path) => path.replace(/^\/geo_server/, ""),
			},
		},
	};

export default defineConfig({
	plugins: [vue(), viteCompression(), evMockPlugin()],
	build: {
		rollupOptions: {
			output: {
				manualChunks(id) {
					if (id.includes("node_modules")) {
						return id.toString().split("node_modules/")[1].split("/")[0].toString();
					}
				},
			},
		},
		chunkSizeWarningLimit: 1600,
	},
	base: "/",
	server: serverConfig,
});
