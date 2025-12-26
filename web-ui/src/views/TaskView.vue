<template>
  <el-container class="layout-container">
    <el-header>
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <span class="text-large font-600 mr-3"> {{ titleMap[type] || type }} </span>
        </template>
      </el-page-header>
    </el-header>
    <el-main>
      <el-row :gutter="20">
        <el-col :span="14">
          <el-card>
            <el-tabs v-model="activeTab" class="demo-tabs">
              <!-- Dynamically render tabs based on schema -->
              <el-tab-pane 
                v-for="tab in currentSchema" 
                :key="tab.name" 
                :label="tab.label" 
                :name="tab.name"
              >
                <el-form :model="form" label-width="140px" size="default">
                  <div class="scroll-form">
                    <template v-for="field in tab.fields" :key="field.prop">
                      <el-form-item 
                        v-if="!field.if || field.if(form)"
                        :label="field.label"
                      >
                        <!-- Text Input -->
                        <el-input 
                          v-if="field.type === 'text'" 
                          v-model="form[field.prop]" 
                          :placeholder="field.placeholder" 
                        />
                        
                        <!-- Number Input -->
                        <el-input-number 
                          v-else-if="field.type === 'number'" 
                          v-model="form[field.prop]" 
                          :min="field.min" 
                          :max="field.max" 
                          :step="field.step"
                        />
                        
                        <!-- Select -->
                        <el-select 
                          v-else-if="field.type === 'select'" 
                          v-model="form[field.prop]"
                          :multiple="field.multiple"
                          placeholder="Select"
                        >
                          <el-option 
                            v-for="opt in field.options" 
                            :key="opt.value" 
                            :label="opt.label" 
                            :value="opt.value" 
                          />
                        </el-select>

                        <!-- Switch -->
                        <el-switch 
                          v-else-if="field.type === 'switch'" 
                          v-model="form[field.prop]" 
                        />
                        
                        <!-- Textarea -->
                        <el-input 
                          v-else-if="field.type === 'textarea'" 
                          type="textarea"
                          v-model="form[field.prop]" 
                          :rows="4"
                          :placeholder="field.placeholder"
                        />
                        
                        <div v-if="field.desc" class="form-desc">{{ field.desc }}</div>
                      </el-form-item>
                    </template>
                  </div>
                </el-form>
              </el-tab-pane>
            </el-tabs>

            <div class="action-bar">
              <el-form :model="form" label-width="140px">
                <el-form-item label="Advanced Params">
                  <el-input 
                    v-model="form.more_params" 
                    placeholder='Additional args in JSON (e.g. {"beta": 0.5}) or CLI format (--beta 0.5)' 
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" size="large" @click="handleLaunch" :loading="launching">
                    {{ launchButtonText }}
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </el-col>

        <el-col :span="10">
          <el-card class="log-card">
            <template #header>
              <div class="card-header">
                <span>📄 运行日志 (Runtime Logs)</span>
                <div>
                   <el-tag v-if="runningPid" type="success">Running: {{ runningPid }}</el-tag>
                   <el-tag v-else type="info">Idle</el-tag>
                </div>
              </div>
            </template>
            <div class="log-container" ref="logContainer">
              <pre>{{ logs }}</pre>
            </div>
            <div class="log-actions">
                <el-button @click="refreshLog">刷新日志</el-button>
                <el-button type="danger" @click="handleStop" :disabled="!runningPid">停止任务</el-button>
                <el-button type="success" @click="openService" v-if="type === 'infer' && serviceUrl">打开服务</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { launchTraining, getLog, killTask } from '../api'
import { ElMessage } from 'element-plus'

// --- State ---
const route = useRoute()
const type = ref(route.params.type)
const activeTab = ref('basic')
const launching = ref(false)
const logs = ref('')
const currentLogFile = ref('')
const logOffset = ref(0)
const timer = ref(null)
const runningPid = ref(null)
const serviceUrl = ref('')

// --- Default Form Data ---
const form = ref({
  // Common
  model_id: 'qwen/Qwen-7B-Chat',
  dataset: 'alpaca-zh',
  output_dir: 'output/run_' + Date.now(),
  more_params: '',
  
  // SFT/PT
  sft_type: 'lora',
  learning_rate: '1e-4',
  num_train_epochs: 1,
  batch_size: 1,
  gradient_accumulation_steps: 16,
  max_length: 2048,
  
  // Tuner
  lora_rank: 8,
  lora_alpha: 32,
  lora_dropout: 0.05,
  lora_target_modules: 'ALL',
  
  // RLHF
  rlhf_type: 'dpo',
  ref_model_id: '',
  
  // Infer
  ckpt_dir: '',
  port: 8000,
  max_new_tokens: 2048,
  temperature: 0.3,
  top_k: 20,
  top_p: 0.7,
  
  // Export
  quant_bits: 0,
  export_format: 'awq',
  push_to_hub: false,
  
  // Eval
  eval_dataset: ['ceval', 'mmlu'],
  eval_limit: 10,
  
  // Sample
  num_return_sequences: 1
})

// --- Schemas ---
const commonFields = [
  { prop: 'model_id', label: 'Model ID / Path', type: 'text', placeholder: 'e.g. qwen/Qwen-7B-Chat' },
  { prop: 'output_dir', label: 'Output Dir', type: 'text' },
]

const sftSchema = [
  {
    name: 'basic', label: 'Basic Config',
    fields: [
      ...commonFields,
      { prop: 'dataset', label: 'Dataset', type: 'text', placeholder: 'e.g. alpaca-zh, msm8k' },
      { prop: 'sft_type', label: 'SFT Type', type: 'select', options: [{label: 'LoRA', value: 'lora'}, {label: 'Full', value: 'full'}, {label: 'AdaLoRA', value: 'adalora'}] },
    ]
  },
  {
    name: 'train', label: 'Training',
    fields: [
      { prop: 'learning_rate', label: 'Learning Rate', type: 'text' },
      { prop: 'num_train_epochs', label: 'Epochs', type: 'number', min: 1, max: 100 },
      { prop: 'batch_size', label: 'Batch Size', type: 'number', min: 1 },
      { prop: 'gradient_accumulation_steps', label: 'Grad Acc Steps', type: 'number', min: 1 },
      { prop: 'max_length', label: 'Max Length', type: 'number', min: 128, step: 128 },
    ]
  },
  {
    name: 'lora', label: 'LoRA / Tuner',
    fields: [
      { prop: 'lora_rank', label: 'LoRA Rank', type: 'number', min: 1 },
      { prop: 'lora_alpha', label: 'LoRA Alpha', type: 'number', min: 1 },
      { prop: 'lora_dropout', label: 'LoRA Dropout', type: 'text' },
      { prop: 'lora_target_modules', label: 'Target Modules', type: 'text', placeholder: 'ALL or q_proj,v_proj' },
    ]
  }
]

const rlhfSchema = [
  {
    name: 'basic', label: 'Basic Config',
    fields: [
      ...commonFields,
      { prop: 'rlhf_type', label: 'RLHF Type', type: 'select', options: [
        {label: 'DPO', value: 'dpo'}, 
        {label: 'CPO', value: 'cpo'}, 
        {label: 'ORPO', value: 'orpo'}, 
        {label: 'SimPO', value: 'simpo'}, 
        {label: 'PPO', value: 'ppo'}, 
        {label: 'KTO', value: 'kto'}
      ]},
      { prop: 'dataset', label: 'Dataset', type: 'text' },
    ]
  },
  {
    name: 'advanced', label: 'Advanced',
    fields: [
      { prop: 'ref_model_id', label: 'Ref Model ID', type: 'text', placeholder: 'Optional reference model' },
      { prop: 'learning_rate', label: 'Learning Rate', type: 'text' },
      { prop: 'num_train_epochs', label: 'Epochs', type: 'number', min: 1 },
    ]
  }
]

const inferSchema = [
  {
    name: 'basic', label: 'Service Config',
    fields: [
      { prop: 'model_id', label: 'Model ID', type: 'text' },
      { prop: 'ckpt_dir', label: 'Checkpoint Dir', type: 'text', placeholder: 'Path to fine-tuned checkpoint' },
      { prop: 'port', label: 'Port', type: 'number', min: 1024, max: 65535 },
    ]
  },
  {
    name: 'generation', label: 'Generation',
    fields: [
      { prop: 'max_new_tokens', label: 'Max New Tokens', type: 'number', min: 1 },
      { prop: 'temperature', label: 'Temperature', type: 'text' },
      { prop: 'top_k', label: 'Top K', type: 'number' },
      { prop: 'top_p', label: 'Top P', type: 'text' },
    ]
  }
]

const exportSchema = [
  {
    name: 'basic', label: 'Export Config',
    fields: [
      { prop: 'model_id', label: 'Model ID', type: 'text' },
      { prop: 'ckpt_dir', label: 'Checkpoint Dir', type: 'text' },
      { prop: 'output_dir', label: 'Output Dir', type: 'text' },
      { prop: 'export_format', label: 'Format', type: 'select', options: [
        {label: 'AWQ', value: 'awq'}, 
        {label: 'GPTQ', value: 'gptq'}, 
        {label: 'ONNX', value: 'onnx'},
        {label: 'Ollama', value: 'ollama'},
      ]},
      { prop: 'quant_bits', label: 'Quant Bits', type: 'select', options: [{label: '0 (None)', value: 0}, {label: '4', value: 4}, {label: '8', value: 8}] },
      { prop: 'push_to_hub', label: 'Push to Hub', type: 'switch' },
    ]
  }
]

const evalSchema = [
  {
    name: 'basic', label: 'Eval Config',
    fields: [
      { prop: 'model_id', label: 'Model ID', type: 'text' },
      { prop: 'ckpt_dir', label: 'Checkpoint Dir', type: 'text' },
      { prop: 'eval_dataset', label: 'Datasets', type: 'select', multiple: true, options: [
        {label: 'CEval', value: 'ceval'}, 
        {label: 'MMLU', value: 'mmlu'}, 
        {label: 'GSM8K', value: 'gsm8k'}, 
        {label: 'ARC', value: 'arc'}, 
      ]},
      { prop: 'eval_limit', label: 'Limit', type: 'number', desc: 'Sample limit for quick evaluation' },
    ]
  }
]

const schemas = {
  sft: sftSchema,
  pt: sftSchema, // Reuse sft schema for pt
  rlhf: rlhfSchema,
  dpo: rlhfSchema, // Alias
  grpo: rlhfSchema, // Reuse structure, maybe different params later
  infer: inferSchema,
  export: exportSchema,
  eval: evalSchema,
  sample: sftSchema, // Placeholder
}

const titleMap = {
  sft: '指令监督微调 (SFT)',
  rlhf: '人类偏好对齐 (RLHF)',
  grpo: 'GRPO 训练',
  infer: '推理部署 (Inference)',
  export: '模型导出 (Export)',
  eval: '模型评测 (Evaluation)',
  sample: '数据集采样 (Sample)'
}

const currentSchema = computed(() => schemas[type.value] || [])
const launchButtonText = computed(() => {
  const map = {
    infer: '🚀 启动服务',
    export: '📦 开始导出',
    eval: '📊 开始评测',
    sample: '🔍 开始采样'
  }
  return map[type.value] || '🚀 开始训练'
})

// --- Watchers ---
watch(() => route.params.type, (newType) => {
  type.value = newType
  activeTab.value = 'basic'
  logs.value = ''
  currentLogFile.value = ''
  runningPid.value = null
})

// --- Methods ---
const handleLaunch = async () => {
  launching.value = true
  try {
    let command = ['swift']
    
    // Command mapping
    const cmdMap = {
      sft: 'sft', pt: 'pt',
      rlhf: 'rlhf', dpo: 'rlhf', grpo: 'rlhf',
      infer: 'deploy',
      export: 'export',
      eval: 'eval',
      sample: 'sample' // Assuming sample command exists or handled
    }
    
    command.push(cmdMap[type.value] || type.value)
    
    // Append fields
    currentSchema.value.forEach(tab => {
      tab.fields.forEach(field => {
        const val = form.value[field.prop]
        if (val === undefined || val === '' || val === null) return
        
        // Skip special fields handled differently or not CLI args
        if (field.prop === 'more_params') return
        
        // Handle boolean switches
        if (field.type === 'switch') {
          if (val) command.push(`--${field.prop}`)
        } 
        // Handle list/select multiple
        else if (Array.isArray(val)) {
          command.push(`--${field.prop}`, ...val)
        }
        else {
          command.push(`--${field.prop}`, String(val))
        }
      })
    })
    
    // Handle generic more_params
    if (form.value.more_params) {
        // Simple splitting by space, ideally should parse better
        // Check if it looks like JSON
        if (form.value.more_params.trim().startsWith('{')) {
             // Pass as is? Backend agent might need update to handle this if we want to support raw json config
             // For now assume CLI args string
             const extras = form.value.more_params.trim().split(/\s+/)
             command.push(...extras)
        } else {
             const extras = form.value.more_params.trim().split(/\s+/)
             command.push(...extras)
        }
    }

    // Determine log file
    const logDir = (type.value === 'infer' || type.value === 'eval') ? 'logs' : form.value.output_dir
    const logFile = `${logDir}/${type.value}_${Date.now()}.log`

    const res = await launchTraining({
      command: command,
      env: {},
      log_file: logFile,
      work_dir: null
    })
    
    ElMessage.success('任务已启动!')
    currentLogFile.value = res.data.log_file
    runningPid.value = res.data.pid
    logOffset.value = 0
    logs.value = ''
    
    if (type.value === 'infer') {
      serviceUrl.value = `http://${window.location.hostname}:${form.value.port}`
    }
    
    startPolling()
    
  } catch (error) {
    ElMessage.error('启动失败: ' + error.message)
  } finally {
    launching.value = false
  }
}

const startPolling = () => {
  if (timer.value) clearInterval(timer.value)
  timer.value = setInterval(refreshLog, 2000)
}

const refreshLog = async () => {
  if (!currentLogFile.value) return
  try {
    const res = await getLog(currentLogFile.value, logOffset.value)
    if (res.data.content) {
      logs.value += res.data.content
      logOffset.value += res.data.length
      const container = document.querySelector('.log-container')
      if (container) container.scrollTop = container.scrollHeight
    }
  } catch (e) {
    // console.error('Fetch log error', e)
  }
}

const handleStop = async () => {
  if (!runningPid.value) return
  try {
    await killTask(runningPid.value, form.value.output_dir)
    ElMessage.success('任务已停止')
    runningPid.value = null
    clearInterval(timer.value)
  } catch (e) {
    ElMessage.error('停止失败: ' + e.message)
  }
}

const openService = () => {
  window.open(serviceUrl.value, '_blank')
}

onUnmounted(() => {
  if (timer.value) clearInterval(timer.value)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.scroll-form {
  height: calc(100vh - 300px);
  overflow-y: auto;
  padding-right: 10px;
}
.form-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
  margin-top: 4px;
}
.action-bar {
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 20px;
}
.log-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.log-container {
  background: #1e1e1e;
  color: #fff;
  padding: 10px;
  height: calc(100vh - 250px);
  overflow-y: auto;
  border-radius: 4px;
  font-family: monospace;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.log-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}
pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
