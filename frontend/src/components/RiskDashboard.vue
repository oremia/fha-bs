<template>
  <div class="dashboard-container" v-loading="store.loading">
    <el-row :gutter="20" class="kpi-row">
      <el-col :span="8"><el-card shadow="hover"><div class="kpi-card"><div class="kpi-value">{{ dashboardData.kpis.total }}</div><div class="kpi-label">总分析条目数</div></div></el-card></el-col>
      <el-col :span="8"><el-card shadow="hover" body-class="catastrophic"><div class="kpi-card"><div class="kpi-value">{{ dashboardData.kpis.catastrophic }}</div><div class="kpi-label">灾难级风险</div></div></el-card></el-col>
      <el-col :span="8"><el-card shadow="hover" body-class="hazardous"><div class="kpi-card"><div class="kpi-value">{{ dashboardData.kpis.hazardous }}</div><div class="kpi-label">危险级风险</div></div></el-card></el-col>
    </el-row>
    <el-row :gutter="20" class="main-content-row">
      <el-col :span="14"><el-card shadow="never" class="chart-card"><template #header>FHA 风险分布旭日图</template><div ref="sunburstChartRef" style="width: 100%; height: 450px;"></div></el-card></el-col>
      <el-col :span="10"><el-card shadow="never" class="summary-card"><template #header>智能分析与建议</template><div class="summary-text">{{ dashboardData.summaryText }}</div></el-card></el-col>
    </el-row>
    <el-row>
        <el-col :span="24">
            <el-card shadow="never" class="cross-table-card">
                 <template #header>风险/功能 交叉分析矩阵</template>
                 <el-table :data="crossAnalysisTableData" border style="width: 100%;"><el-table-column label="功能" prop="func" width="180" header-align="center"><template #default="scope"><strong>{{ scope.row.func }}</strong></template></el-table-column><el-table-column v-for="(col, index) in dashboardData.crossAnalysis.columns" :key="col" :label="col" align="center"><template #default="scope"><div :style="getCellStyle(scope.row.values[index])">{{ scope.row.values[index] }}</div></template></el-table-column></el-table>
            </el-card>
        </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue';
import * as echarts from 'echarts';
import { useFhaStore } from '@/store/fha';

const store = useFhaStore();
const sunburstChartRef = ref(null);
let chartInstance = null;

const dashboardData = computed(() => store.dashboardData);

const crossAnalysisTableData = computed(() => {
    if (!dashboardData.value.crossAnalysis.rows) return [];
    return dashboardData.value.crossAnalysis.rows.map((row, rowIndex) => ({
        func: row,
        values: dashboardData.value.crossAnalysis.data[rowIndex] || []
    }));
});

const getCellStyle = (value) => {
    if (value > 0) {
        const intensity = Math.min(1, 0.2 + value * 0.2);
        return { backgroundColor: `rgba(211, 47, 47, ${intensity})`, color: 'white', fontWeight: 'bold' };
    }
    return {};
};

const resizeChart = () => {
    if (chartInstance) {
        chartInstance.resize();
    }
}

const initAndDrawChart = () => {
    if (sunburstChartRef.value) {
        chartInstance = echarts.init(sunburstChartRef.value);
        window.addEventListener('resize', resizeChart);

        const latestData = store.dashboardData;
        const option = {
            tooltip: { trigger: 'item', formatter: '{b}: {c}' },
            series: {
              type: 'sunburst', data: latestData.sunburstData.children, radius: [60, '90%'],
              label: { rotate: 'radial' },
              emphasis: { label: { show: true, fontSize: '16', fontWeight: 'bold' } }
            }
        };
        chartInstance.setOption(option, true);
    }
};

// **关键修正：在组件挂载到DOM后，才执行图表的初始化和绘制**
onMounted(() => {
    // nextTick 确保DOM元素已经渲染完毕
    nextTick(() => {
        initAndDrawChart();
    });
});

onUnmounted(() => {
    window.removeEventListener('resize', resizeChart);
    chartInstance?.dispose();
});
</script>

<style scoped>
.dashboard-container { padding: 20px; background-color: #f0f2f5; height: 100%; overflow-y: auto; }
.kpi-row, .main-content-row { margin-bottom: 20px; }
.kpi-card { text-align: center; }
.kpi-value { font-size: 32px; font-weight: bold; }
.kpi-label { font-size: 14px; color: #606266; }
:deep(.el-card__body.catastrophic) { background-color: #fde2e2; color: #D32F2F; }
:deep(.el-card__body.hazardous) { background-color: #fff0de; color: #FFA000; }
.chart-card, .summary-card, .cross-table-card { height: 100%; }
.summary-text { font-size: 14px; line-height: 1.8; white-space: pre-wrap; height: 400px; overflow-y: auto; }
</style>