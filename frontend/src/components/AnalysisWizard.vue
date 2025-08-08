<template>
  <el-dialog
    v-model="dialogVisible"
    title="引导式失效分析向导"
    width="60%"
    :before-close="handleClose"
    :close-on-click-modal="false"
  >
    <el-steps :active="activeStep" finish-status="success" simple style="margin-bottom: 20px;">
      <el-step title="选择失效模式" />
      <el-step title="分析影响" />
      <el-step title="评估危害" />
    </el-steps>

    <div v-if="activeStep === 0">
      <h3>第一步：选择失效模式</h3>
      <p>为功能 <strong>{{ sourceData['一级功能'] }} / {{ sourceData['二级功能'] }}</strong> (类型: {{ sourceData['功能类型'] }}) 选择一个或多个可能的失效模式。</p>
      <el-checkbox-group v-model="selectedModes">
        <el-checkbox v-for="mode in availableModes" :key="mode" :label="mode" border style="margin: 5px;" />
      </el-checkbox-group>
    </div>

    <div v-if="activeStep === 1">
      <h3>第二步：分析影响 ({{ currentModeIndex + 1 }} / {{ selectedModes.length }})</h3>
      <p>当前分析的失效模式: <strong>{{ selectedModes[currentModeIndex] }}</strong></p>
      <el-form label-position="top">
        <el-form-item label="对于飞行器的影响:">
          <el-input type="textarea" :rows="3" v-model="analyses[currentModeIndex].aircraft_effect" />
        </el-form-item>
        <el-form-item label="对于地面/空域的影响:">
          <el-input type="textarea" :rows="3" v-model="analyses[currentModeIndex].airspace_effect" />
        </el-form-item>
        <el-form-item label="对于地面控制组的影响:">
          <el-input type="textarea" :rows="3" v-model="analyses[currentModeIndex].gcs_effect" />
        </el-form-item>
      </el-form>
    </div>

    <div v-if="activeStep === 2">
      <h3>第三步：评估危害等级 ({{ currentModeIndex + 1 }} / {{ selectedModes.length }})</h3>
      <p>当前评估的失效模式: <strong>{{ selectedModes[currentModeIndex] }}</strong></p>
      <el-card shadow="never" style="margin-bottom: 20px;">
        <template #header>影响汇总 (只读)</template>
        <div><strong>对飞行器:</strong> {{ analyses[currentModeIndex].aircraft_effect || '无' }}</div>
        <div><strong>对空域:</strong> {{ analyses[currentModeIndex].airspace_effect || '无' }}</div>
        <div><strong>对控制组:</strong> {{ analyses[currentModeIndex].gcs_effect || '无' }}</div>
      </el-card>
       <el-form label-position="top">
        <el-form-item label="最终危害性分类:">
          <el-select v-model="analyses[currentModeIndex].hazard_category" placeholder="请选择危害等级" style="width: 100%;">
            <el-option v-for="cat in store.config.arp4761_categories" :key="cat" :label="cat" :value="cat"/>
          </el-select>
        </el-form-item>
        <el-form-item label="理由/备注:">
          <el-input type="textarea" :rows="3" v-model="analyses[currentModeIndex].reason" />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="prevStep" :disabled="activeStep === 0">上一步</el-button>
        <el-button type="primary" @click="nextStep" v-if="activeStep < 2">下一步</el-button>
        <el-button type="success" @click="finish" v-if="activeStep === 2">完成分析</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, reactive } from 'vue';
import { useFhaStore } from '@/store/fha';
import { ElMessage } from 'element-plus';

const props = defineProps({
  modelValue: Boolean,
  sourceData: Object,
});
const emit = defineEmits(['update:modelValue', 'confirm']);

const store = useFhaStore();
const dialogVisible = ref(props.modelValue);

const activeStep = ref(0);
const currentModeIndex = ref(0);
const selectedModes = ref([]);
const analyses = ref([]);

const availableModes = computed(() => {
  const funcType = props.sourceData?.功能类型 || '通用';
  const generalModes = store.config.failure_mode_library['通用'] || [];
  const specificModes = store.config.failure_mode_library[funcType] || [];
  return [...new Set([...generalModes, ...specificModes])].sort();
});

watch(() => props.modelValue, (val) => {
  dialogVisible.value = val;
  if (val) {
    // Reset state when dialog opens
    activeStep.value = 0;
    currentModeIndex.value = 0;
    selectedModes.value = [];
    analyses.value = [];
  }
});

const handleClose = () => {
  emit('update:modelValue', false);
};

const prevStep = () => {
    if(activeStep.value === 1 || activeStep.value === 2) {
        if(currentModeIndex.value > 0) {
            currentModeIndex.value--;
        } else {
            activeStep.value--;
        }
    }
};

const nextStep = () => {
  if (activeStep.value === 0) {
    if (selectedModes.value.length === 0) {
      ElMessage.warning('请至少选择一个失效模式！');
      return;
    }
    // Initialize analysis objects
    analyses.value = selectedModes.value.map(() => reactive({
      aircraft_effect: '',
      airspace_effect: '',
      gcs_effect: '',
      hazard_category: '',
      reason: ''
    }));
    activeStep.value++;
  } else if (activeStep.value === 1 || activeStep.value === 2) {
    if (currentModeIndex.value < selectedModes.value.length - 1) {
      currentModeIndex.value++;
    } else {
      activeStep.value++;
      currentModeIndex.value = 0; // Reset for next step
    }
  }
};

const finish = () => {
    // Final check for the last item in step 3
    if (currentModeIndex.value < selectedModes.value.length - 1) {
        currentModeIndex.value++;
        return;
    }

    const results = [];
    for (let i = 0; i < selectedModes.value.length; i++) {
        const analysis = analyses.value[i];
        if(!analysis.hazard_category) {
            ElMessage.warning(`请为失效模式 "${selectedModes.value[i]}" 选择一个危害性分类`);
            activeStep.value = 2;
            currentModeIndex.value = i;
            return;
        }
        results.push({
            '失效状态': selectedModes.value[i],
            '对于飞行器的影响': analysis.aircraft_effect,
            '对于地面/空域的影响': analysis.airspace_effect,
            '对于地面控制组的影响': analysis.gcs_effect,
            '危害性分类': analysis.hazard_category,
            '理由/备注': analysis.reason,
        });
    }

  emit('confirm', results);
  handleClose();
};

</script>