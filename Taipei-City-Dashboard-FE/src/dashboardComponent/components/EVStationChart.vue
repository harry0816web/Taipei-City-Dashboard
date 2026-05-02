<!-- Developed for Taipei City Dashboard Hackathon 2025 -->
<!-- EV Charging Station Distribution Chart -->
<!-- Shows charging station count per district with EV-specific tooltip -->
<!-- Pairs with MapLegend type for map view -->

<script setup>
import { ref, computed } from "vue";
import VueApexCharts from "vue3-apexcharts";

const props = defineProps([
	"chart_config",
	"activeChart",
	"series",
	"map_config",
	"map_filter",
	"map_filter_on",
]);

const emits = defineEmits([
	"filterByParam",
	"filterByLayer",
	"clearByParamFilter",
	"clearByLayerFilter",
	"fly",
]);

// ── Summary stats computed from series ──────────────────────────────────────
// series format:
// [{ name: "充電站數量", data: [{ x: "中正區", y: 15, total_guns: 30, operators: "台電,中油" }, ...] }]

const totalStations = computed(() => {
	if (!props.series || !props.series[0]) return 0;
	return props.series[0].data.reduce((sum, d) => sum + (d.y || 0), 0);
});

const totalGuns = computed(() => {
	if (!props.series || !props.series[0]) return 0;
	return props.series[0].data.reduce((sum, d) => sum + (d.total_guns || 0), 0);
});

const topDistrict = computed(() => {
	if (!props.series || !props.series[0]) return "-";
	const sorted = [...props.series[0].data].sort((a, b) => b.y - a.y);
	return sorted[0]?.x || "-";
});

// ── Chart options ────────────────────────────────────────────────────────────
const chartOptions = ref({
	chart: {
		offsetY: 10,
		toolbar: { show: false },
		animations: { enabled: true, speed: 600 },
	},
	colors: props.chart_config?.color?.length
		? [...props.chart_config.color]
		: ["#4CAF93"],
	dataLabels: {
		enabled: true,
		offsetX: 20,
		textAnchor: "start",
		style: {
			fontSize: "11px",
			colors: ["#ccc"],
		},
		formatter: (val) => `${val} 站`,
	},
	grid: { show: false },
	legend: { show: false },
	plotOptions: {
		bar: {
			borderRadius: 3,
			distributed: true,
			horizontal: true,
			dataLabels: { hideOverflowingLabels: false },
			barHeight: "65%",
		},
	},
	stroke: {
		colors: ["#282a2c"],
		show: true,
		width: 1,
	},
	tooltip: {
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
			const label = w.globals.labels[dataPointIndex];
			const val = series[seriesIndex][dataPointIndex];
			// Extra fields attached to each data point by the API pipeline
			const point = props.series[0]?.data[dataPointIndex];
			const guns = point?.total_guns ? `${point.total_guns} 槍` : "-";
			const operators = point?.operators || "-";
			return (
				'<div class="chart-tooltip">' +
				`<h6>${label}</h6>` +
				`<span>充電站：<b>${val} 站</b></span>` +
				`<span>充電槍：<b>${guns}</b></span>` +
				`<span>營運商：${operators}</span>` +
				"</div>"
			);
		},
		followCursor: true,
	},
	xaxis: {
		axisBorder: { show: false },
		axisTicks: { show: false },
		labels: { show: false },
		type: "category",
	},
	yaxis: {
		labels: {
			formatter: (value) =>
				value && value.length > 4 ? value.slice(0, 3) + ".." : value,
		},
	},
});

// ── Dynamic height based on data rows ───────────────────────────────────────
const chartHeight = computed(() => {
	const rows = props.series?.[0]?.data?.length || 12;
	return `${30 + rows * 28}`;
});

// ── Map filter interaction ───────────────────────────────────────────────────
const selectedIndex = ref(null);

function handleDataSelection(_e, _chartContext, config) {
	if (!props.map_filter || !props.map_filter_on) return;

	const key = `${config.dataPointIndex}-${config.seriesIndex}`;
	if (key !== selectedIndex.value) {
		if (props.map_filter.mode === "byParam") {
			emits(
				"filterByParam",
				props.map_filter,
				props.map_config,
				config.w.globals.labels[config.dataPointIndex],
				null
			);
		} else if (props.map_filter.mode === "byLayer") {
			emits(
				"filterByLayer",
				props.map_config,
				config.w.globals.labels[config.dataPointIndex]
			);
		}
		selectedIndex.value = key;
	} else {
		if (props.map_filter.mode === "byParam") {
			emits("clearByParamFilter", props.map_config);
		} else if (props.map_filter.mode === "byLayer") {
			emits("clearByLayerFilter", props.map_config);
		}
		selectedIndex.value = null;
	}
}
</script>

<template>
  <div
    v-if="activeChart === 'EVStationChart'"
    class="ev-station-chart"
  >
    <!-- Summary bar at top -->
    <div class="ev-station-chart-summary">
      <div class="ev-station-chart-summary-item">
        <span class="material-icons ev-icon">ev_station</span>
        <div>
          <p class="ev-station-chart-summary-value">{{ totalStations }}</p>
          <p class="ev-station-chart-summary-label">充電站</p>
        </div>
      </div>
      <div class="ev-station-chart-summary-item">
        <span class="material-icons ev-icon">bolt</span>
        <div>
          <p class="ev-station-chart-summary-value">{{ totalGuns }}</p>
          <p class="ev-station-chart-summary-label">充電槍</p>
        </div>
      </div>
      <div class="ev-station-chart-summary-item">
        <span class="material-icons ev-icon">location_on</span>
        <div>
          <p class="ev-station-chart-summary-value ev-station-chart-summary-value--district">
            {{ topDistrict }}
          </p>
          <p class="ev-station-chart-summary-label">最多站點</p>
        </div>
      </div>
    </div>

    <!-- Bar chart -->
    <VueApexCharts
      width="100%"
      :height="chartHeight"
      type="bar"
      :options="chartOptions"
      :series="series"
      @data-point-selection="handleDataSelection"
    />
  </div>
</template>

<style scoped lang="scss">
* {
	margin: 0;
	padding: 0;
	font-family: "微軟正黑體", "Microsoft JhengHei", "Droid Sans", "Open Sans", "Helvetica";
}

.ev-station-chart {
	width: 100%;
	overflow-y: auto;
	overflow-x: hidden;

	&-summary {
		display: flex;
		justify-content: space-around;
		align-items: center;
		padding: 6px 4px 10px;
		border-bottom: 1px solid var(--color-border);
		margin-bottom: 4px;

		&-item {
			display: flex;
			align-items: center;
			gap: 6px;
		}

		&-value {
			font-size: var(--font-m);
			font-weight: 700;
			color: var(--color-normal-text);
			line-height: 1.2;

			&--district {
				font-size: var(--font-s);
			}
		}

		&-label {
			font-size: var(--font-s);
			color: var(--color-complement-text);
		}
	}
}

.ev-icon {
	font-family: var(--font-icon) !important;
	font-size: 1.2rem;
	color: #4caf93;
}
</style>
