<template>
  <div class="fha-table-container">
    <div class="toolbar">
      <el-button type="primary" :icon="DocumentAdd" @click="newProject">新建分析项目</el-button>
      <el-upload
        action=""
        :show-file-list="false"
        :before-upload="handleImport"
        accept=".xlsx, .xls"
        style="margin: 0 12px;"
      >
        <el-button :icon="Upload">导入旧格式表格</el-button>
      </el-upload>
      <el-button :icon="Download" @click="store.exportData">导出为表格</el-button>
      <el-divider direction="vertical" />
      <el-button type="success" :icon="Plus" @click="addRow">添加行</el-button>
      <el-button type="danger" :icon="Delete" @click="deleteSelectedRows" :disabled="selectedRows.length === 0">删除选中行</el-button>
      <el-divider direction="vertical" />
      <el-button type="warning" :icon="MagicStick" @click="startAnalysis" :disabled="selectedRows.length !== 1">引导式分析</el-button>
    </div>

    <div class="table-wrapper">
      <el-table
        :data="store.tableData"
        :row-key="row => row.编号"
        border
        stripe
        style="width: 100%"
        height="100%"
        @selection-change="handleSelectionChange"
        ref="tableRef"
        table-layout="fixed"
      >
        <el-table-column type="selection" width="55" fixed />
        <el-table-column prop="编号" label="编号" width="120" fixed />

        <el-table-column label="一级功能" width="180">
          <template #default="scope">
            <el-input v-model="scope.row['一级功能']" @change="handleCellChange(scope.row)" placeholder="一级功能"/>
          </template>
        </el-table-column>

        <el-table-column label="二级功能" width="180">
          <template #default="scope">
            <el-input v-model="scope.row['二级功能']" @change="handleCellChange(scope.row)" placeholder="二级功能"/>
          </template>
        </el-table-column>

        <el-table-column label="三级功能" width="180">
          <template #default="scope">
            <el-input v-model="scope.row['三级功能']" @change="handleCellChange(scope.row)" placeholder="三级功能"/>
          </template>
        </el-table-column>

        <el-table-column label="功能类型" width="150">
          <template #default="scope">
            <el-input v-model="scope.row['功能类型']" @change="handleCellChange(scope.row)" placeholder="功能类型"/>
          </template>
        </el-table-column>

        <el-table-column label="飞行阶段" width="150">
          <template #default="scope">
            <el-input v-model="scope.row['飞行阶段']" @change="handleCellChange(scope.row)" placeholder="飞行阶段"/>
          </template>
        </el-table-column>

        <el-table-column label="失效状态" width="200">
          <template #default="scope">
            <el-input v-model="scope.row['失效状态']" @change="handleCellChange(scope.row)" placeholder="失效状态"/>
          </template>
        </el-table-column>

        <el-table-column label="对飞行器的影响" width="250">
          <template #default="scope">
            <el-input type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" v-model="scope.row['对于飞行器的影响']" @change="handleCellChange(scope.row)" placeholder="对飞行器的影响"/>
          </template>
        </el-table-column>

        <el-table-column label="对地面/空域的影响" width="250">
          <template #default="scope">
            <el-input type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" v-model="scope.row['对于地面/空域的影响']" @change="handleCellChange(scope.row)" placeholder="对地面/空域的影响"/>
          </template>
        </el-table-column>

        <el-table-column label="对地面控制组的影响" width="250">
          <template #default="scope">
            <el-input type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" v-model="scope.row['对于地面控制组的影响']" @change="handleCellChange(scope.row)" placeholder="对地面控制组的影响"/>
          </template>
        </el-table-column>

        <el-table-column label="危害性分类" width="200" fixed="right">
          <template #default="scope">
            <el-select
              v-model="scope.row.危害性分类"
              placeholder="请选择"
              @change="handleCellChange(scope.row)"
              style="width: 100%;"
            >
              <el-option
                v-for="item in store.config.arp4761_categories"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </template>
        </el-table-column>

        <el-table-column label="理由/备注" width="250" fixed="right">
          <template #default="scope">
            <el-input type="textarea" :autosize="{ minRows: 1, maxRows: 3 }" v-model="scope.row['理由/备注']" @change="handleCellChange(scope.row)" placeholder="理由/备注"/>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <FunctionalArchitectDialog v-if="architectDialogVisible" v-model="architectDialogVisible" @confirm="createProject"/>
    <AnalysisWizard v-if="wizardDialogVisible" v-model="wizardDialogVisible" :source-data="selectedRowForWizard" @confirm="runWizard"/>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'; // **关键修正：移除了 onMounted, onUnmounted**
import { useFhaStore } from '@/store/fha';
import { ElMessage, ElMessageBox } from 'element-plus';
import FunctionalArchitectDialog from './FunctionalArchitectDialog.vue';
import AnalysisWizard from './AnalysisWizard.vue';
import { DocumentAdd, Upload, Download, Plus, Delete, MagicStick } from '@element-plus/icons-vue';
import api from '@/api';

const store = useFhaStore();
const tableRef = ref(null);
const selectedRows = ref([]);

const architectDialogVisible = ref(false);
const wizardDialogVisible = ref(false);

const selectedRowForWizard = computed(() => {
  if (selectedRows.value.length === 1) { return selectedRows.value[0]; }
  return null;
});

const handleSelectionChange = (val) => { selectedRows.value = val; };
const newProject = () => { architectDialogVisible.value = true; };

const createProject = async (skeleton) => {
    architectDialogVisible.value = false;
    if (!skeleton || skeleton.length === 0) { ElMessage.info('未选择任何功能与阶段的组合，创建了一个空项目。'); }
    await store.handleApiCall(api.createNewProject, skeleton);
};

const handleImport = (file) => {
  store.handleApiCall(api.importFromExcel, file);
  return false;
};

const addRow = async () => {
    await store.handleApiCall(api.addRow);
    await nextTick();
    const tableEl = tableRef.value;
    if (tableEl) {
      // 获取外层滚动容器
      const wrapper = tableEl.$el.parentElement;
      wrapper.scrollTop = wrapper.scrollHeight;
    }
};

const deleteSelectedRows = () => {
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedRows.value.length} 行吗？此操作不可撤销。`, '确认删除', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
  ).then(() => {
    const indices = selectedRows.value.map(row => row.originalIndex);
    store.handleApiCall(api.deleteRows, indices);
  }).catch(() => {});
};

const startAnalysis = () => {
  if (selectedRows.value.length !== 1) { ElMessage.warning("请先在'FHA总表'中选择一个待分析的行。"); return; }
  wizardDialogVisible.value = true;
};

const runWizard = (results) => {
    wizardDialogVisible.value = false;
    if (selectedRowForWizard.value) { store.handleApiCall(api.runWizard, selectedRowForWizard.value.originalIndex, results); }
};

const handleCellChange = (row) => {
    const { originalIndex, ...dataToUpdate } = row;
    store.updateCellData(originalIndex, dataToUpdate);
};
</script>

<style scoped>
.fha-table-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 15px;
  box-sizing: border-box;
}
.toolbar {
  padding: 8px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.table-wrapper {
  /* 这个外层容器会撑满剩余空间 */
  flex-grow: 1;
  /* 关键：让这个容器负责所有滚动 */
  overflow: auto;
  will-change: transform;
}

:deep(.el-table .el-input__wrapper) {
  box-shadow: none;
  background-color: transparent;
}
:deep(.el-table .el-textarea__inner) {
  box-shadow: none;
  background-color: transparent;
  resize: none;
}
:deep(.el-table td.el-table__cell) {
  padding: 4px 0;
}
</style>
