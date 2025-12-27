<template>
  <el-container class="layout-container">
    <el-header class="page-header">
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <div class="header-content">
            <span class="text-large font-600 mr-3">🔢 GRPO 训练</span>
            <el-tag type="info" effect="plain" round>Group Relative Policy Optimization</el-tag>
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
                <el-button type="primary" size="large" @click="handleLaunch" :loading="launching" round>
                  🚀 开始 GRPO 训练
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
                </el-form-item>
                
                <el-form-item label="数据集">
                  <el-select 
                    v-model="form.dataset" 
                    multiple 
                    filterable 
                    allow-create 
                    default-first-option 
                    placeholder="选择或输入数据集 (e.g. gsm8k)"
                    style="width: 100%"
                  >
                    <el-option v-for="item in datasetOptions" :key="item" :label="item" :value="item" />
                  </el-select>
                  <div class="form-tip">支持本地路径，多个数据集用逗号分隔</div>
                </el-form-item>
                
                <el-form-item label="输出目录">
                  <el-input v-model="form.output_dir" />
                </el-form-item>

                <el-form-item label="奖励函数 (Reward)">
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
                    <el-form-item label="生成数量 (Num Gens)">
                      <el-input-number v-model="form.num_generations" :min="1" />
                      <div class="form-tip">每个提示生成的回复数量</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="最大生成长度">
                      <el-input-number v-model="form.max_completion_length" :min="128" :step="128" />
                    </el-form-item>
                  </el-col>
                </el-row>
                
                <el-form-item label="Batch Size">
                    <el-input-number v-model="form.batch_size" :min="1" />
                </el-form-item>

                <el-form-item label="使用 VLLM 加速">
                  <el-switch v-model="form.use_vllm" />
                  <div class="form-tip">使用 vLLM 进行加速生成</div>
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
                    placeholder="输入额外的命令行参数" 
                  />
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <!-- Log Viewer (Drawer Style) -->
        <transition name="slide-up">
          <div class="log-drawer" v-if="showLogs || runningPid">
            <div class="log-header">
              <div class="log-title">
                <span>📄 实时训练日志</span>
                <el-tag v-if="runningPid" type="success" effect="dark" size="small" class="ml-2">Running: {{ runningPid }}</el-tag>
                <el-tag v-else type="info" effect="dark" size="small" class="ml-2">Stopped</el-tag>
              </div>
              <div class="log-controls">
                <el-button link @click="showLogs = false" v-if="!runningPid">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="log-content">
              <LogViewer 
                :log-file="currentLogFile" 
                :output-dir="form.output_dir"
                v-model:pid="runningPid" 
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
import { Close } from '@element-plus/icons-vue'
import LogViewer from '../../components/LogViewer.vue'

const activeTab = ref('basic')
const launching = ref(false)
const showLogs = ref(false)
const currentLogFile = ref('')
const runningPid = ref(null)

const modelOptions = ref([])
const datasetOptions = ref([])

const form = ref({
  // Basic
  model_id: 'qwen/Qwen-7B-Chat',
  dataset: ['gsm8k'],
  output_dir: 'output/grpo_' + Date.now(),
  reward_funcs: ['accuracy'],
  
  // Training
  learning_rate: '1e-5',
  num_train_epochs: 1,
  batch_size: 1,
  num_generations: 4,
  max_completion_length: 1024,
  use_vllm: false,
  
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
    const command = ['swift', 'rlhf', '--rlhf_type', 'grpo']
    
    // Parameter mapping
    const fields = [
      'model_id', 'output_dir', 'learning_rate', 'num_train_epochs',
      'batch_size', 'num_generations', 'max_completion_length', 'deepspeed'
    ]
    
    fields.forEach(f => {
      if (form.value[f] !== '' && form.value[f] !== null) {
        command.push(`--${f}`, String(form.value[f]))
      }
    })

    // Handle dataset (array -> comma separated string)
    if (Array.isArray(form.value.dataset) && form.value.dataset.length > 0) {
      command.push('--dataset', form.value.dataset.join(','))
    } else if (typeof form.value.dataset === 'string' && form.value.dataset) {
      command.push('--dataset', form.value.dataset)
    }

    // Handle reward funcs
    if (form.value.reward_funcs && form.value.reward_funcs.length > 0) {
      command.push('--reward_funcs', ...form.value.reward_funcs)
    }

    if (form.value.use_vllm) {
      command.push('--use_vllm', 'true')
    }

    if (form.value.more_params) {
      command.push(...form.value.more_params.trim().split(/\s+/))
    }

    const logFile = `${form.value.output_dir}/grpo.log`
    
    const res = await launchTraining({
      command,
      env: {},
      log_file: logFile
    })
    
    ElMessage.success('GRPO 任务已启动!')
    currentLogFile.value = res.data.log_file
    runningPid.value = res.data.pid
    showLogs.value = true
    
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
}

.log-header {
  height: 40px;
  background: #252526;
  padding: 0 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #333;
}

.log-title {
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.log-content {
  flex: 1;
  overflow: hidden;
  position: relative;
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
