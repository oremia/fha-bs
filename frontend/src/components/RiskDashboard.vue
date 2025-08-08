<template>
  <div class="dashboard-container" v-loading="store.loading">
    <el-row :gutter="20" class="kpi-row">
      <el-col :span="8"><el-card shadow="hover"><div class="kpi-card"><div class="kpi-value">{{ dashboardData.kpis.total }}</div><div class="kpi-label">总分析条目数</div></div></el-card></el-col>
      <el-col :span="8"><el-card shadow="hover" body-class="catastrophic"><div class="kpi-card"><div class="kpi-value">{{ dashboardData.kpis.catastrophic }}</div><div class="kpi-label">灾难级风险</div></div></el-card></el-col>
      <el-col :span="8"><el-card shadow="hover" body-class="hazardous"><div class="kpi-card"><div class="kpi-value">{{ dashboardData.kpis.hazardous }}</div><div class="kpi-label">危险级风险</div></div></el-card></el-col>
    </el-row>

    <el-row :gutter="20" class="main-content-row">
      <el-col :span="10">
        <el-card shadow="never" class="content-card">
          <template #header>FHA 风险分布旭日图</template>
          <div ref="sunburstChartRef" style="width: 100%; height: 420px;"></div>
        </el-card>
      </el-col>

      <el-col :span="5">
        <el-card shadow="never" class="content-card">
          <template #header>图例统计</template>
          <div class="legend-container" v-if="dashboardData.legendData">
            <div class="legend-section">
              <strong>功能分类 (风险数)</strong>
              <ul>
                <li v-for="item in dashboardData.legendData.functions" :key="item.name">
                  <span class="legend-color-box" :style="{ backgroundColor: item.color }"></span>
                  {{ item.name }}: {{ item.count }}
                </li>
              </ul>
            </div>
            <div class="legend-section">
              <strong>危害性等级 (总计)</strong>
              <ul>
                <li v-for="item in dashboardData.legendData.hazards" :key="item.name">
                  <span class="legend-color-box" :style="{ backgroundColor: item.color }"></span>
                  {{ item.name }}: {{ item.count }}
                </li>
              </ul>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="9">
        <el-card shadow="never" class="content-card">
          <template #header>智能分析与建议</template>
          <div class="summary-text">{{ dashboardData.summaryText }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row>
        <el-col :span="24">
            <el-card shadow="never" class="cross-table-card">
                 <template #header>风险/功能 交叉分析矩阵</template>
                 <el-table :data="crossAnalysisTableData" border style="width: 100%;">
                   <el-table-column label="功能" prop="func" width="180" header-align="center">
                     <template #default="scope"><strong>{{ scope.row.func }}</strong></template>
                   </el-table-column>
                   <el-table-column v-for="(col, index) in dashboardData.crossAnalysis.columns" :key="col" :label="col" align="center">
                     <template #default="scope"><div :style="getCellStyle(scope.row.values[index])">{{ scope.row.values[index] }}</div></template>
                   </el-table-column>
                 </el-table>
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
    if (!dashboardData.value.crossAnalysis || !dashboardData.value.crossAnalysis.rows) return [];
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
        if (!latestData || !latestData.sunburstData) return;

        const option = {
            // **关键修改：使用 formatter 函数自定义 tooltip**
            tooltip: {
                trigger: 'item',
                formatter: (params) => {
                    const data = params.data;
                    // 如果是"其他"分类，并且有我们预存的详情，就显示它
                    if (data.name === '其他' && data.tooltipDetail) {
                        return data.tooltipDetail;
                    }
                    // 对其他所有数据，显示 "名称: 数量"
                    return `${params.name}: ${params.value}`;
                }
            },
            series: {
              type: 'sunburst',
              data: latestData.sunburstData.children,
              radius: ['20%', '90%'],
              nodeClick: 'zoomToNode',
              label: {
                hideOverlap: true,
              },
              levels: [
                {},
                {
                  label: { rotate: 0, fontSize: 11, minAngle: 5 }
                },
                {
                  label: { show: false }
                }
              ],
              emphasis: {
                label: {
                  show: true,
                  fontSize: '14',
                  fontWeight: 'bold'
                }
              }
            }
        };
        chartInstance.setOption(option, true);
    }
};

onMounted(() => {
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

.content-card {
  height: 500px;
}
.summary-text, .legend-container {
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  height: 420px; /* 匹配图表高度 */
  overflow-y: auto;
}

.legend-section {
  margin-bottom: 20px;
}
.legend-section strong {
  font-size: 14px;
}
.legend-section ul {
  list-style: none;
  padding-left: 10px;
  margin-top: 8px;
}
.legend-section li {
  font-size: 13px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
}
.legend-color-box {
  width: 12px;
  height: 12px;
  margin-right: 8px;
  display: inline-block;
  border: 1px solid #ddd;
  flex-shrink: 0;
}
.cross-table-card {
  height: 100%;
}
</style>
