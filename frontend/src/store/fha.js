import { defineStore } from 'pinia';
import api from '@/api';
import { ElMessage, ElNotification } from 'element-plus';

const ARP4761_CATEGORIES = [
    "", "灾难的 (Catastrophic)", "危险的 (Hazardous)", "严重的 (Major)",
    "轻微的 (Minor)", "无安全影响 (No Safety Effect)"
];

export const useFhaStore = defineStore('fha', {
  state: () => ({
    fhaData: [],
    config: {
      failure_mode_library: {},
      arp4761_categories: ARP4761_CATEGORIES,
      mission_phases: [],
      function_types: [],
    },
    loading: false,
  }),
  getters: {
    tableData: (state) => state.fhaData.map((row, index) => ({ ...row, originalIndex: index })),
    dashboardData(state) {
      const df = state.fhaData;
      if (!df || df.length === 0) {
        return {
          kpis: { total: 0, catastrophic: 0, hazardous: 0 },
          sunburstData: { name: "FHA风险", children: [] },
          crossAnalysis: { rows: [], columns: [], data: [] },
          summaryText: "暂无数据，请先新建项目或导入数据。",
        };
      }
      const df_analyzed = df.filter(row => row['失效状态'] && row['失效状态'] !== '');
      const hazardCounts = df_analyzed.reduce((acc, row) => {
        const category = row['危害性分类'];
        if (category) acc[category] = (acc[category] || 0) + 1;
        return acc;
      }, {});
      const kpis = {
        total: df_analyzed.length,
        catastrophic: hazardCounts["灾难的 (Catastrophic)"] || 0,
        hazardous: hazardCounts["危险的 (Hazardous)"] || 0,
      };
      const df_filtered = df_analyzed.filter(row =>
        row['一级功能'] && row['危害性分类'] && row['危害性分类'] !== '无安全影响 (No Safety Effect)'
      );
      const sunburstData = { name: "FHA风险", children: [] };
      if (df_filtered.length > 0) {
        const colorMap = {
            "灾难的 (Catastrophic)": "#D32F2F", "危险的 (Hazardous)": "#FFA000",
            "严重的 (Major)": "#388E3C", "轻微的 (Minor)": "#1976D2",
        };
        const funcGroups = df_filtered.reduce((acc, row) => {
            const func = row['一级功能'];
            if (!acc[func]) acc[func] = [];
            acc[func].push(row);
            return acc;
        }, {});
        sunburstData.children = Object.entries(funcGroups).map(([name, group]) => {
            const hazardCountsGroup = group.reduce((acc, row) => {
                const hazard = row['危害性分类'];
                if(hazard) acc[hazard] = (acc[hazard] || 0) + 1;
                return acc;
            }, {});
            return {
                name: name,
                children: Object.entries(hazardCountsGroup).map(([hazard, count]) => ({
                    name: hazard.split(' ')[0], value: count, itemStyle: { color: colorMap[hazard] }
                }))
            };
        });
      }
      const crossAnalysis = { rows: [], columns: [], data: [] };
      let summaryText = "";
      const df_cross = df_analyzed.filter(row => row['一级功能'] && row['危害性分类']);
      if (df_cross.length > 0) {
        const rows = [...new Set(df_cross.map(r => r['一级功能']))];
        const cols = ARP4761_CATEGORIES.filter(c => c && c !== '无安全影响 (No Safety Effect)');
        const crossData = rows.map(rowLabel => {
            const rowData = df_cross.filter(r => r['一级功能'] === rowLabel);
            return cols.map(colLabel => rowData.filter(r => r['危害性分类'] === colLabel).length);
        });
        crossAnalysis.rows = rows;
        crossAnalysis.columns = cols.map(c => c.split(' ')[0]);
        crossAnalysis.data = crossData;
        const high_risk_items_count = kpis.catastrophic + kpis.hazardous;
        summaryText += `当前共识别出 ${high_risk_items_count} 项高风险条目（灾难级或危险级）。\n\n`;
        const highRiskColsIndices = [cols.indexOf("灾难的 (Catastrophic)"), cols.indexOf("危险的 (Hazardous)")].filter(i => i !== -1);
        if (highRiskColsIndices.length > 0) {
            let topFunc = '';
            let maxRisk = -1;
            rows.forEach((func, rowIndex) => {
                const currentRisk = highRiskColsIndices.reduce((sum, colIndex) => sum + crossData[rowIndex][colIndex], 0);
                if (currentRisk > maxRisk) { maxRisk = currentRisk; topFunc = func; }
            });
            if (topFunc) {
                const topFuncIndex = rows.indexOf(topFunc);
                const topFuncCatCount = cols.indexOf("灾难的 (Catastrophic)") !== -1 ? crossData[topFuncIndex][cols.indexOf("灾难的 (Catastrophic)")] : 0;
                const topFuncHazCount = cols.indexOf("危险的 (Hazardous)") !== -1 ? crossData[topFuncIndex][cols.indexOf("危险的 (Hazardous)")] : 0;
                summaryText += `核心关注点：\n风险主要集中在 “${topFunc}” 系统中，其中包含 ${topFuncCatCount} 个“灾难级”和 ${topFuncHazCount} 个“危险级”风险。\n\n`;
            }
        }
        summaryText += "行动建议：\n请结合下方交叉分析矩阵，优先审查高风险区域对应的功能模块，并为这些风险制定缓解措施和验证计划。";
      } else {
        summaryText = "暂无已完成分析的条目，无法生成摘要。";
      }
      return { kpis, sunburstData, crossAnalysis, summaryText };
    }
  },
  actions: {
    async fetchConfig() {
      try { const response = await api.getConfig(); this.config = response.data; }
      catch (error) { ElMessage.error('获取配置信息失败'); }
    },
    async fetchData() {
      this.loading = true;
      try { const response = await api.getFhaData(); this.fhaData = response.data; }
      catch (error) { ElMessage.error('获取FHA数据失败'); }
      finally { this.loading = false; }
    },
    async handleApiCall(apiCall, ...args) {
      this.loading = true;
      try {
        const response = await apiCall(...args);
        // **关键修正：确保每次都用服务器返回的最新数据完整替换本地数据**
        if (response.data && response.data.data) {
          this.fhaData = response.data.data;
        } else {
          await this.fetchData(); // 作为备用方案，重新获取全部数据
        }
        if (response.data.message) {
          ElNotification({ title: '成功', message: response.data.message, type: 'success', duration: 2000 });
        }
        return response;
      } catch (error) {
        const errorMessage = error.response?.data?.detail || '操作失败';
        ElNotification({ title: '错误', message: errorMessage, type: 'error' });
        throw error;
      } finally {
        this.loading = false;
      }
    },
    async exportData() {
        this.loading = true;
        try {
            const response = await api.exportToExcel();
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'FHA_Report.xlsx');
            document.body.appendChild(link);
            link.click();
            link.remove();
            ElMessage.success('导出成功！');
        } catch (error) {
            ElMessage.error(error.response?.data?.detail || '导出失败');
        } finally {
            this.loading = false;
        }
    },
  }
});