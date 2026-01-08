<template>
  <el-container class="layout-container">
    <el-header class="page-header">
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <div class="header-content">
            <span class="text-large font-600 mr-3">🧠 强化学习 (Reinforcement Learning)</span>
            <el-tag type="warning" effect="plain" round>RLHF / DPO / GRPO</el-tag>
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
                  🚀 开始 RL 训练
                </el-button>
              </div>
            </div>
          </template>
          
          <el-tabs v-model="activeTab" class="config-tabs">
            <!-- 基础配置 -->
            <el-tab-pane label="基础配置 (Basic)" name="basic">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-form-item label="RL 算法">
                  <el-radio-group v-model="form.rlhf_type">
                    <el-radio-button label="dpo">DPO</el-radio-button>
                    <el-radio-button label="cpo">CPO</el-radio-button>
                    <el-radio-button label="orpo">ORPO</el-radio-button>
                    <el-radio-button label="simpo">SimPO</el-radio-button>
                    <el-radio-button label="kto">KTO</el-radio-button>
                    <el-radio-button label="ppo">PPO</el-radio-button>
                    <el-radio-button label="grpo">GRPO</el-radio-button>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="模型 ID / 路径">
                  <el-select 
                    v-model="form.model_id" 
                    filterable 
                    allow-create 
                    default-first-option 
                    placeholder="选择或输入模型 ID (通常是 SFT 后的模型)"
                    style="width: 100%"
                  >
                    <el-option v-for="item in modelOptions" :key="item" :label="item" :value="item" />
                  </el-select>
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
                  <div class="form-tip">支持本地路径，多个数据集用逗号分隔</div>
                </el-form-item>
                
                <el-form-item label="输出目录">
                  <el-input v-model="form.output_dir" />
                </el-form-item>

                <!-- GRPO Specific: Reward Functions -->
                <el-form-item label="奖励函数 (Reward)" v-if="form.rlhf_type === 'grpo'">
                  <el-select 
                    v-model="form.reward_funcs" 
                    multiple 
                    allow-create 
                    filterable 
                    default-first-option
                    placeholder="选择奖励函数"
                  >
                    <el-option label="Accuracy" value="accuracy" />
                    <el-option label="Format" value="format" />
                    <el-option label="Cosine" value="cosine" />
                    <el-option label="Levenshtein" value="levenshtein" />
                  </el-select>
                  <div class="form-tip">自定义奖励函数或内置函数</div>
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
                    <el-form-item label="梯度累积步数" v-if="form.rlhf_type !== 'grpo'">
                      <el-input-number v-model="form.gradient_accumulation_steps" :min="1" />
                    </el-form-item>
                    <!-- GRPO uses num_generations, maybe distinct from grad acc? Keeping generic if not conflicting -->
                  </el-col>
                </el-row>

                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="最大长度 (Max Length)" v-if="form.rlhf_type !== 'grpo'">
                      <el-input-number v-model="form.max_length" :min="128" :step="128" />
                    </el-form-item>
                    <el-form-item label="最大生成长度" v-if="form.rlhf_type === 'grpo'">
                      <el-input-number v-model="form.max_completion_length" :min="128" :step="128" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Beta / KL Coeff" v-if="form.rlhf_type !== 'grpo'">
                      <el-input-number v-model="form.beta" :step="0.1" />
                      <div class="form-tip">KL 惩罚系数 (DPO/PPO)</div>
                    </el-form-item>
                    <el-form-item label="生成数量 (Num Gens)" v-if="form.rlhf_type === 'grpo'">
                      <el-input-number v-model="form.num_generations" :min="1" />
                      <div class="form-tip">每个提示生成的回复数量</div>
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

                <el-form-item label="使用梯度检查点" v-if="form.rlhf_type !== 'grpo'">
                  <el-switch v-model="form.gradient_checkpointing" />
                </el-form-item>

                <el-form-item label="使用 VLLM 加速" v-if="form.rlhf_type === 'grpo'">
                  <el-switch v-model="form.use_vllm" />
                  <div class="form-tip">使用 vLLM 进行加速生成</div>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- LoRA / Tuner -->
            <el-tab-pane label="LoRA / Tuner" name="lora">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-form-item label="使用 LoRA">
                  <el-switch v-model="form.use_lora" />
                  <div class="form-tip">使用 LoRA 进行参数高效微调</div>
                </el-form-item>

                <template v-if="form.use_lora">
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
                    <el-input v-model="form.target_modules" placeholder="ALL" />
                  </el-form-item>
                </template>
              </el-form>
            </el-tab-pane>

            <!-- 高级参数 -->
            <el-tab-pane label="高级参数 (Advanced)" name="advanced">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-form-item label="参考模型 (Ref Model)" v-if="form.rlhf_type !== 'grpo'">
                  <el-input v-model="form.ref_model" placeholder="可选，默认与模型ID一致" />
                  <div class="form-tip">用于计算 KL 散度的参考模型</div>
                </el-form-item>

                <el-form-item label="DeepSpeed">
                  <el-input v-model="form.deepspeed" placeholder="path/to/ds_config.json" />
                </el-form-item>
                
                <el-form-item label="其他参数">
                  <el-input 
                    type="textarea"
                    v-model="form.more_params" 
                    :rows="4"
                    placeholder="输入额外的命令行参数" 
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
  rlhf_type: 'dpo',
  model_id: 'qwen/Qwen-7B-Chat',
  dataset: [], 
  output_dir: 'output/rlhf_' + Date.now(),
  
  // GRPO specific
  reward_funcs: ['accuracy'],
  
  // Training
  learning_rate: '5e-6',
  num_train_epochs: 1,
  per_device_train_batch_size: 1,
  gradient_accumulation_steps: 16,
  max_length: 2048,
  beta: 0.1,
  seed: 42,
  torch_dtype: 'bfloat16',
  gradient_checkpointing: true,
  
  // GRPO Training specific
  num_generations: 4,
  max_completion_length: 1024,
  use_vllm: false,

  // LoRA
  use_lora: true,
  lora_rank: 8,
  lora_alpha: 32,
  lora_dropout: 0.05,
  target_modules: 'all-linear',

  // Advanced
  ref_model: '',
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
    const command = ['swift', 'rlhf']
    
    // Common fields
    const commonFields = [
      'rlhf_type', 'model_id', 'output_dir',
      'learning_rate', 'num_train_epochs', 'per_device_train_batch_size',
      'seed', 'torch_dtype', 'deepspeed'
    ]
    
    commonFields.forEach(f => {
      if (form.value[f] !== '' && form.value[f] !== null) {
        const argName = f === 'model_id' ? 'model' : f
        command.push(`--${argName}`, String(form.value[f]))
      }
    })

    // Conditional fields based on type
    if (form.value.rlhf_type === 'grpo') {
      // GRPO specific
      if (form.value.reward_funcs && form.value.reward_funcs.length > 0) {
        command.push('--reward_funcs', ...form.value.reward_funcs)
      }
      command.push('--num_generations', String(form.value.num_generations))
      command.push('--max_completion_length', String(form.value.max_completion_length))
      if (form.value.use_vllm) command.push('--use_vllm', 'true')
    } else {
      // Standard RLHF (DPO/PPO etc)
      command.push('--gradient_accumulation_steps', String(form.value.gradient_accumulation_steps))
      command.push('--max_length', String(form.value.max_length))
      command.push('--beta', String(form.value.beta))
      if (form.value.gradient_checkpointing) command.push('--gradient_checkpointing', 'true')
      if (form.value.ref_model) command.push('--ref_model', form.value.ref_model)
    }

    // Handle dataset (array -> comma separated string)
    if (Array.isArray(form.value.dataset) && form.value.dataset.length > 0) {
      command.push('--dataset', form.value.dataset.join(','))
    } else if (typeof form.value.dataset === 'string' && form.value.dataset) {
      command.push('--dataset', form.value.dataset)
    }

    // LoRA params
    if (form.value.use_lora) {
        command.push('--train_type', 'lora')
        command.push('--lora_rank', String(form.value.lora_rank))
        command.push('--lora_alpha', String(form.value.lora_alpha))
        command.push('--lora_dropout', String(form.value.lora_dropout))
        command.push('--target_modules', form.value.target_modules)
    } else {
        command.push('--train_type', 'full')
    }

    // Extra params
    if (form.value.more_params) {
      command.push(...form.value.more_params.trim().split(/\s+/))
    }

    const logFile = `${form.value.output_dir}/rl.log`
    
    const res = await launchTraining({
      command,
      env: {},
      log_file: logFile
    })
    
    ElMessage.success('RL 任务已启动!')
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
  left: 220px;
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
