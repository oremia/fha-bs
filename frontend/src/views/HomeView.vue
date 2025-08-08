<template>
  <div class="common-layout">
    <el-container style="height: 100vh;">
      <el-header class="main-header">
        <h1>FHA 结构化分析系统 (Web版)</h1>
      </el-header>
      <el-main v-loading="store.loading">
        <el-tabs v-model="activeTab" type="border-card" class="main-tabs">
          <el-tab-pane label="FHA 总表" name="table">
            <FhaTable />
          </el-tab-pane>
          <el-tab-pane label="风险摘要" name="dashboard" :lazy="true">
             <RiskDashboard v-if="activeTab === 'dashboard'" />
          </el-tab-pane>
        </el-tabs>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useFhaStore } from '@/store/fha';
import FhaTable from '@/components/FhaTable.vue';
import RiskDashboard from '@/components/RiskDashboard.vue';

const store = useFhaStore();
const activeTab = ref('table');

onMounted(async () => {
  await store.fetchConfig();
  await store.fetchData();
});
</script>

<style scoped>
.main-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  line-height: 60px;
}
.main-header h1 {
  margin: 0;
  font-size: 20px;
}
.el-main {
  padding: 0;
}
.main-tabs {
  height: calc(100vh - 60px);
  border: none;
  display: flex;
  flex-direction: column;
}
:deep(.el-tabs__content) {
  flex-grow: 1;
  overflow-y: auto;
  padding: 15px;
}
</style>