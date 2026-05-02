<!-- Developed for Taipei City Dashboard Hackathon 2025 -->
<!-- EV Charging Station Real-Time Availability Chart -->
<!-- Shows available vs in-use chargers per district as 100% stacked bar -->
<!-- Green = available, Red = in-use -->
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

// ── EV availability color palette (always green/red regardless of chart_config) ──
const EV_COLORS = ["#4CAF93", "#E05C5C"]; // [空閒, 使用中]

// ── Summary stats ────────────────────────────────────────────────────────────
// series format:
// [
//   { name: "空閒", data: [{ x: "中正區", y: 12 }, ...] },
//   { name: "使用中", data: [{ x: "中正區", y: 8 }, ...] }
// ]

const cityWideTotals = computed(() => {
	if (!props.series || props.series.length < 2) return { available: 0, inUse: 0 };
	const available = props.series[0].data.reduce((s, d) => s + (d.y || 0), 0);
	const inUse = props.series[1].data.reduce((s, d) => s + (d.y || 0), 0);
	return { available, inUse };
});

const availabilityRate = computed(() => {
	const { available, inUse } = cityWideTotals.value;
	const total = available + inUse;
	if (!total) return 0;
	return Math.round((available / total) * 100);
});

const rateColor = computed(() => {
	const r = availabilityRate.value;
	if (r >= 50) return "#4CAF93";
	if (r >= 25) return "#E6B84A";
	return "#E05C5C";
});

// ── Chart options ────────────────────────────────────────────────────────────
const chartOptions = ref({
	chart: {
		stacked: true,
		stackType: "100%",
		toolbar: { show: false },
		animations: { enabled: true, speed: 600 },
	},
	colors: EV_COLORS,
	dataLabels: {
		enabled: false,
	},
	grid: { show: false },
	legend: {
		show: true,
		position: "top",
		offsetY: 4,
		labels: {
			colors: ["#aaa"],
		},
	},
	plotOptions: {
		bar: {
			borderRadius: 3,
			horizontal: true,
			barHeight: "60%",
		},
	},
	stroke: {
		colors: ["#282a2c"],
		show: true,
		width: 2,
	},
	tooltip: {
		custom: function ({ series, seriesIndex, dataPointIndex, w }) {
			const label = w.globals.labels[dataPointIndex];
			const available = props.series[0]?.data[dataPointIndex]?.y ?? 0;
			const inUse = props.series[1]?.data[dataPointIndex]?.y ?? 0;
			const total = available + inUse;
			const pct = total ? Math.round((available / total) * 100) : 0;
			const statusColor = pct >= 50 ? "#4CAF93" : pct >= 25 ? "#E6B84A" : "#E05C5C";
			return (
				'<div class="chart-tooltip">' +
				`<h6>${label}</h6>` +
				`<span>空閒：<b style="color:#4CAF93">${available} 槍</b></span>` +
				`<span>使用中：<b style="color:#E05C5C">${inUse} 槍</b></span>` +
				`<span>空閒率：<b style="color:${statusColor}">${pct}%</b></span>` +
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

// ── Dynamic height ───────────────────────────────────────────────────────────
const chartHeight = computed(() => {
	const rows = props.series?.[0]?.data?.length || 12;
	return `${40 + rows * 28}`;
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
    v-if="activeChart === 'EVRealtimeChart'"
    class="ev-realtime-chart"
  >
    <!-- City-wide availability summary -->
    <div class="ev-realtime-chart-header">
      <div class="ev-realtime-chart-header-rate">
        <span
          class="ev-realtime-chart-header-rate-value"
          :style="{ color: rateColor }"
        >
          {{ availabilityRate }}%
        </span>
        <span class="ev-realtime-chart-header-rate-label">全市空閒率</span>
      </div>
      <div class="ev-realtime-chart-header-stats">
        <div class="ev-realtime-chart-header-stat">
          <span class="ev-dot ev-dot--available" />
          <span>空閒 {{ cityWideTotals.available }} 槍</span>
        </div>
        <div class="ev-realtime-chart-header-stat">
          <span class="ev-dot ev-dot--inuse" />
          <span>使用中 {{ cityWideTotals.inUse }} 槍</span>
        </div>
      </div>
    </div>

    <!-- Stacked percent bar chart -->
    <VueApexCharts
      type="bar"
      width="100%"
      :height="chartHeight"
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

.ev-realtime-chart {
	width: 100%;
	overflow-y: auto;
	overflow-x: hidden;

	&-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 6px 8px 10px;
		border-bottom: 1px solid var(--color-border);
		margin-bottom: 4px;

		&-rate {
			display: flex;
			align-items: baseline;
			gap: 6px;

			&-value {
				font-size: 1.6rem;
				font-weight: 700;
				line-height: 1;
				transition: color 0.3s;
			}

			&-label {
				font-size: var(--font-s);
				color: var(--color-complement-text);
			}
		}

		&-stats {
			display: flex;
			flex-direction: column;
			gap: 4px;
			align-items: flex-end;
		}

		&-stat {
			display: flex;
			align-items: center;
			gap: 5px;
			font-size: var(--font-s);
			color: var(--color-normal-text);
		}
	}
}

.ev-dot {
	display: inline-block;
	width: 8px;
	height: 8px;
	border-radius: 50%;
	flex-shrink: 0;

	&--available {
		background-color: #4caf93;
	}

	&--inuse {
		background-color: #e05c5c;
	}
}
</style>
