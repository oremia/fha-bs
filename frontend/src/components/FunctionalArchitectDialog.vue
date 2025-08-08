<template>
  <el-dialog
    v-model="dialogVisible"
    title="新建FHA项目 - 功能架构与任务剖析向导"
    width="80%"
    :before-close="handleClose"
  >
    <div class="dialog-content">
      <div class="func-ops">
        <el-input v-model="funcNameInput" placeholder="输入功能名称..." style="width: 200px; margin-right: 8px;"/>
        <el-select v-model="funcTypeInput" placeholder="选择功能类型" style="width: 150px; margin-right: 8px;">
          <el-option v-for="item in store.config.function_types" :key="item" :label="item" :value="item" />
        </el-select>
        <el-button-group>
          <el-button type="primary" @click="addTopLevelFunction">添加顶层功能</el-button>
          <el-button type="success" @click="addSubFunction">添加子功能</el-button>
          <el-button type="danger" @click="deleteFunction">删除选中</el-button>
        </el-button-group>
      </div>

      <div class="main-content">
        <div class="tree-panel">
          <el-tree
            :data="treeData"
            :props="treeProps"
            node-key="id"
            default-expand-all
            highlight-current
            @node-click="handleNodeClick"
            ref="treeRef"
          >
             <template #default="{ node, data }">
                <span>{{ node.label }} ({{ data.type }})</span>
            </template>
          </el-tree>
        </div>
        <div class="matrix-panel">
          <el-table :data="matrixData" border style="width: 100%">
            <el-table-column label="功能路径" prop="path" width="250" />
            <el-table-column
              v-for="phase in store.config.mission_phases"
              :key="phase"
              :label="phase"
              align="center"
              width="100"
            >
              <template #default="scope">
                <el-checkbox v-model="scope.row.phases[phase]" />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="handleConfirm">确定创建</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'; // 移除了 nextTick
import { useFhaStore } from '@/store/fha';
import { ElMessage } from 'element-plus';

const props = defineProps({
  modelValue: Boolean,
});
const emit = defineEmits(['update:modelValue', 'confirm']);

const store = useFhaStore();
const dialogVisible = ref(props.modelValue);
const treeRef = ref(null);

let nextId = 1;
const funcNameInput = ref('');
const funcTypeInput = ref(store.config.function_types[0] || '');
const treeData = ref([]);
const treeProps = { children: 'children', label: 'name' };

watch(() => props.modelValue, (val) => {
  dialogVisible.value = val;
  if (val) {
    // 重置状态
    treeData.value = [];
    funcNameInput.value = '';
    funcTypeInput.value = store.config.function_types[0] || '';
    nextId = 1;
  }
});

const handleClose = () => {
  emit('update:modelValue', false);
};

const addTopLevelFunction = () => {
  if (!funcNameInput.value.trim()) {
    ElMessage.warning('功能名称不能为空！');
    return;
  }
  treeData.value.push({
    id: nextId++,
    name: funcNameInput.value,
    type: funcTypeInput.value,
    children: [],
  });
  funcNameInput.value = '';
};

const addSubFunction = () => {
  const selectedNode = treeRef.value?.getCurrentNode();
  if (!selectedNode) {
    ElMessage.info('请先在左侧的功能树中选择一个父功能。');
    return;
  }
  if (!funcNameInput.value.trim()) {
    ElMessage.warning('功能名称不能为空！');
    return;
  }
  const newNode = {
    id: nextId++,
    name: funcNameInput.value,
    type: funcTypeInput.value,
    children: [],
  };
  if (!selectedNode.children) {
    selectedNode.children = [];
  }
  selectedNode.children.push(newNode);
  funcNameInput.value = '';
};

const deleteFunction = () => {
  const selectedKey = treeRef.value?.getCurrentKey();
  if (!selectedKey) {
    ElMessage.info('请先选择要删除的功能。');
    return;
  }
  const removeNode = (nodes, id) => {
    for (let i = 0; i < nodes.length; i++) {
        if (nodes[i].id === id) {
            nodes.splice(i, 1);
            return true;
        }
        if (nodes[i].children && removeNode(nodes[i].children, id)) {
            return true;
        }
    }
    return false;
  };
  removeNode(treeData.value, selectedKey);
};

// 矩阵数据生成
const matrixData = computed(() => {
    const leaves = [];
    const findLeaves = (nodes, path = []) => {
        nodes.forEach(node => {
            const currentPath = [...path, {name: node.name, type: node.type}];
            if (!node.children || node.children.length === 0) {
                leaves.push({
                    path: currentPath.map(p => p.name).join(' / '),
                    type: node.type,
                    fullPath: currentPath,
                    phases: store.config.mission_phases.reduce((acc, phase) => ({ ...acc, [phase]: false }), {})
                });
            } else {
                findLeaves(node.children, currentPath);
            }
        });
    };
    findLeaves(treeData.value);
    return leaves;
});

const handleNodeClick = () => { // 移除了未使用的 (data, node) 参数
  // 可以保留用于未来扩展，例如同步矩阵滚动
};

const handleConfirm = () => {
  const skeleton = [];
  matrixData.value.forEach(row => {
    Object.entries(row.phases).forEach(([phase, checked]) => {
      if (checked) {
        const path = row.fullPath;
        skeleton.push({
          '一级功能': path[0]?.name || '',
          '二级功能': path[1]?.name || '',
          '三级功能': path[2]?.name || '',
          '功能类型': row.type,
          '飞行阶段': phase,
        });
      }
    });
  });
  emit('confirm', skeleton);
  handleClose();
};

</script>

<style scoped>
.dialog-content {
  height: 60vh;
  display: flex;
  flex-direction: column;
}
.func-ops {
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 16px;
}
.main-content {
  display: flex;
  flex-grow: 1;
  overflow: hidden;
}
.tree-panel {
  width: 30%;
  border-right: 1px solid #e4e7ed;
  padding-right: 16px;
  overflow-y: auto;
}
.matrix-panel {
  width: 70%;
  padding-left: 16px;
  overflow: auto;
}
</style>