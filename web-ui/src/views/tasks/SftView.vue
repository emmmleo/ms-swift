<template>
  <el-container class="layout-container">
    <el-header class="page-header">
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <div class="header-content">
            <span class="text-large font-600 mr-3">🚀 指令监督微调 (SFT / PT)</span>
            <el-tag type="success" effect="plain" round>Supervised Fine-tuning</el-tag>
          </div>
        </template>
      </el-page-header>
    </el-header>
    
    <el-main>
      <div class="content-wrapper">
        <!-- Configuration Area -->
        <el-card class="config-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="title">🛠️ 参数配置</span>
              <div class="actions">
                <el-button v-if="!showLogs && (currentLogFile || runningPid)" @click="showLogs = true" size="large" round>
                  📜 查看日志
                </el-button>
                <el-button type="primary" size="large" @click="handleLaunch" :loading="launching" round>
                  🚀 开始训练
                </el-button>
              </div>
            </div>
          </template>
          
          <el-tabs v-model="activeTab" class="config-tabs">
            <!-- 基础配置 -->
            <el-tab-pane label="基础配置 (Basic)" name="basic">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-form-item label="模型 ID / 路径">
                  <el-select 
                    v-model="form.model_id" 
                    filterable 
                    allow-create 
                    default-first-option 
                    placeholder="选择或输入模型 ID"
                    style="width: 100%"
                  >
                    <el-option v-for="item in modelOptions" :key="item" :label="item" :value="item" />
                  </el-select>
                  <div class="form-tip">支持 HuggingFace 模型 ID 或本地模型目录</div>
                </el-form-item>
                
                <el-form-item label="数据集">
                  <el-select 
                    v-model="form.dataset" 
                    multiple 
                    filterable 
                    allow-create 
                    default-first-option 
                    placeholder="选择或输入数据集"
                    style="width: 100%"
                  >
                    <el-option v-for="item in datasetOptions" :key="item" :label="item" :value="item" />
                  </el-select>
                  <div class="form-tip">多个数据集用逗号分隔，支持本地路径</div>
                </el-form-item>
                
                <el-form-item label="输出目录">
                  <el-input v-model="form.output_dir" />
                </el-form-item>
                
                <el-form-item label="微调类型">
                  <el-radio-group v-model="form.tuner_type">
                    <el-radio-button label="lora">LoRA</el-radio-button>
                    <el-radio-button label="full">Full (全量)</el-radio-button>
                    <el-radio-button label="adalora">AdaLoRA</el-radio-button>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="训练方式">
                  <el-radio-group v-model="form.task_type">
                    <el-radio-button label="sft">SFT (监督微调)</el-radio-button>
                    <el-radio-button label="pt">PT (预训练)</el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 训练参数 -->
            <el-tab-pane label="训练参数 (Training)" name="train">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="学习率 (LR)">
                      <el-input v-model="form.learning_rate" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="训练轮数 (Epochs)">
                      <el-input-number v-model="form.num_train_epochs" :min="1" :max="1000" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="Batch Size">
                      <el-input-number v-model="form.per_device_train_batch_size" :min="1" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="梯度累积步数">
                      <el-input-number v-model="form.gradient_accumulation_steps" :min="1" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="最大长度 (Max Length)">
                      <el-input-number v-model="form.max_length" :min="128" :step="128" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="随机种子 (Seed)">
                  <el-input-number v-model="form.seed" />
                </el-form-item>
                
                <el-form-item label="精度 (Dtype)">
                  <el-select v-model="form.torch_dtype">
                    <el-option label="bf16" value="bf16" />
                    <el-option label="fp16" value="fp16" />
                    <el-option label="fp32" value="fp32" />
                  </el-select>
                </el-form-item>

                <el-form-item label="使用梯度检查点">
                  <el-switch v-model="form.gradient_checkpointing" />
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- LoRA / Tuner -->
            <el-tab-pane label="LoRA / Tuner" name="lora">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="LoRA Rank">
                      <el-input-number v-model="form.lora_rank" :min="1" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="LoRA Alpha">
                      <el-input-number v-model="form.lora_alpha" :min="1" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="LoRA Dropout">
                  <el-input v-model="form.lora_dropout" />
                </el-form-item>
                
                <el-form-item label="Target Modules">
                  <el-input v-model="form.target_modules" placeholder="all-linear" />
                  <div class="form-tip">默认为 all-linear，也可指定如 q_proj,v_proj</div>
                </el-form-item>

                <el-form-item label="使用 RSLoRA">
                  <el-switch v-model="form.use_rslora" />
                </el-form-item>
                
                <el-form-item label="使用 DoRA">
                  <el-switch v-model="form.use_dora" />
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 高级参数 -->
            <el-tab-pane label="高级参数 (Advanced)" name="advanced">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-form-item label="DeepSpeed">
                  <el-input v-model="form.deepspeed" placeholder="path/to/ds_config.json" />
                </el-form-item>
                
                <el-form-item label="其他参数">
                  <el-input 
                    type="textarea"
                    v-model="form.more_params" 
                    :rows="4"
                    placeholder="输入额外的命令行参数，例如: --optim adamw_torch --warmup_ratio 0.05" 
                  />
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <!-- Log Viewer (Collapsible Drawer) -->
        <transition name="slide-up">
          <div class="log-drawer" v-show="showLogs" :class="{ minimized: isMinimized }">
            <div class="log-content">
              <LogViewer 
                :log-file="currentLogFile" 
                :output-dir="form.output_dir"
                :minimized="isMinimized"
                :pid="runningPid" 
                @update:pid="runningPid = $event"
                @toggle-minimize="isMinimized = !isMinimized"
                @close="showLogs = false"
              />
            </div>
          </div>
        </transition>
      </div>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { launchTraining, getModels, getDatasets } from '../../api'
import { ElMessage } from 'element-plus'
import LogViewer from '../../components/LogViewer.vue'

const activeTab = ref('basic')
const launching = ref(false)
const showLogs = ref(false)
const isMinimized = ref(false)
const currentLogFile = ref('')
const runningPid = ref(null)

const modelOptions = ref([])
const datasetOptions = ref([])

const form = ref({
  // Basic
  model_id: 'qwen/Qwen-7B-Chat',
  output_dir: 'output/sft_' + Date.now(),
  dataset: ['AI-ModelScope/alpaca-gpt4-data-zh'],
  tuner_type: 'lora', // This maps to --train_type
  task_type: 'sft', // This determines the command (swift sft)
  
  // Training
  learning_rate: '1e-4',
  num_train_epochs: 1,
  per_device_train_batch_size: 1,
  gradient_accumulation_steps: 16,
  max_length: 2048,
  seed: 42,
  torch_dtype: 'bfloat16',
  gradient_checkpointing: true,
  
  // LoRA
  lora_rank: 8,
  lora_alpha: 32,
  lora_dropout: 0.05,
  target_modules: 'all-linear',
  use_rslora: false,
  use_dora: false,
  
  // Advanced
  deepspeed: '',
  more_params: ''
})

onMounted(async () => {
  try {
    const [mRes, dRes] = await Promise.all([getModels(), getDatasets()])
    modelOptions.value = mRes.data.models || []
    datasetOptions.value = dRes.data.datasets || []
  } catch (e) {
    console.error('Failed to load options', e)
  }
})

const handleLaunch = async () => {
  launching.value = true
  try {
    const command = ['swift', form.value.task_type] // sft or pt
    
    // Manual mapping for tuner_type -> --train_type (lora/full)
    command.push('--train_type', form.value.tuner_type)

    // Parameter mapping
    const fields = [
      'model_id', 'output_dir',
      'learning_rate', 'num_train_epochs', 'per_device_train_batch_size',
      'gradient_accumulation_steps', 'max_length',
      'seed', 'torch_dtype',
      'lora_rank', 'lora_alpha', 'lora_dropout', 'target_modules',
      'deepspeed'
    ]
    
    fields.forEach(f => {
      if (form.value[f] !== '' && form.value[f] !== null) {
        const argName = f === 'model_id' ? 'model' : f
        command.push(`--${argName}`, String(form.value[f]))
      }
    })

    // Handle dataset
    if (Array.isArray(form.value.dataset) && form.value.dataset.length > 0) {
      command.push('--dataset', form.value.dataset.join(','))
    } else if (typeof form.value.dataset === 'string' && form.value.dataset) {
      command.push('--dataset', form.value.dataset)
    }

    // Boolean flags
    if (form.value.gradient_checkpointing) command.push('--gradient_checkpointing', 'true')
    if (form.value.use_rslora) command.push('--use_rslora', 'true')
    if (form.value.use_dora) command.push('--use_dora', 'true')

    // Extra params
    if (form.value.more_params) {
      command.push(...form.value.more_params.trim().split(/\s+/))
    }

    const logFile = `${form.value.output_dir}/sft.log`
    
    const res = await launchTraining({
      command,
      env: {},
      log_file: logFile
    })
    
    ElMessage.success('任务已成功提交，开始训练！')
    currentLogFile.value = res.data.log_file
    runningPid.value = res.data.pid
    showLogs.value = true 
    isMinimized.value = false
    
  } catch (error) {
    ElMessage.error('启动失败: ' + error.message)
  } finally {
    launching.value = false
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background-color: #f5f7fa;
}

.page-header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  height: 100%;
}

.config-card {
  border-radius: 8px;
  border: 1px solid #ebeef5;
  background: #fff;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.config-tabs :deep(.el-tabs__nav-wrap) {
  padding-left: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 4px;
}

/* Log Drawer Styles */
.log-drawer {
  position: fixed;
  bottom: 0;
  left: 220px; /* Adjust based on sidebar width */
  right: 0;
  height: 400px;
  background: #1e1e1e;
  border-top: 1px solid #333;
  box-shadow: 0 -4px 12px rgba(0,0,0,0.15);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  transition: height 0.3s ease;
}

.log-drawer.minimized {
  height: 40px; /* Only toolbar visible */
  overflow: hidden;
}

.log-content {
  flex: 1;
  overflow: hidden;
  position: relative;
  height: 100%;
}

/* Transitions */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}

.ml-2 { margin-left: 8px; }
</style>
