<template>
  <el-container class="layout-container">
    <el-header class="page-header">
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <div class="header-content">
            <span class="text-large font-600 mr-3">📊 模型评测 (Evaluation)</span>
            <el-tag type="info" effect="plain" round>Model Evaluation & Benchmarking</el-tag>
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
                  🚀 开始评测
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
                
                <el-form-item label="Checkpoint 目录">
                  <el-input v-model="form.ckpt_dir" placeholder="可选: 微调后的 checkpoint 路径 (优先使用)" />
                </el-form-item>

                <el-form-item label="评测数据集">
                  <el-select 
                    v-model="form.eval_dataset" 
                    multiple 
                    filterable 
                    allow-create 
                    default-first-option 
                    placeholder="选择评测数据集 (e.g. ceval, mmlu)"
                    style="width: 100%"
                  >
                    <el-option v-for="item in commonEvalDatasets" :key="item" :label="item" :value="item" />
                    <el-option v-for="item in datasetOptions" :key="item" :label="item" :value="item" />
                  </el-select>
                  <div class="form-tip">支持多选，输入即可搜索</div>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 高级参数 -->
            <el-tab-pane label="高级参数 (Advanced)" name="advanced">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="采样数量 (Limit)">
                      <el-input-number v-model="form.eval_limit" :min="0" />
                      <div class="form-tip">每个数据集的样本数 (0 为全量)</div>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Batch Size">
                      <el-input-number v-model="form.eval_batch_size" :min="1" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="评测后端">
                   <el-select v-model="form.eval_backend" placeholder="Default">
                     <el-option label="Native" value="Native" />
                     <el-option label="OpenCompass" value="OpenCompass" />
                     <el-option label="VLMEvalKit" value="VLMEvalKit" />
                   </el-select>
                </el-form-item>

                <el-form-item label="Temperature">
                  <el-input-number v-model="form.temperature" :min="0" :step="0.1" />
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
                <span>📄 实时评测日志</span>
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
                :output-dir="'logs/eval'"
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
const commonEvalDatasets = ['ceval', 'mmlu', 'gsm8k', 'arc', 'bbh', 'truthfulqa', 'human-eval', 'mbpp']

const form = ref({
  // Basic
  model_id: 'qwen/Qwen-7B-Chat',
  ckpt_dir: '',
  eval_dataset: ['ceval', 'mmlu'],
  
  // Advanced
  eval_limit: 10,
  eval_batch_size: 4,
  eval_backend: 'Native',
  temperature: 0,
  more_params: ''
})

onMounted(async () => {
  try {
    const [mRes, dRes] = await Promise.all([getModels(), getDatasets()])
    modelOptions.value = mRes.data.models || []
    // Filter dataset options to avoid overwhelming the list, or just show all
    datasetOptions.value = dRes.data.datasets || []
  } catch (e) {
    console.error('Failed to load options', e)
  }
})

const handleLaunch = async () => {
  launching.value = true
  try {
    const command = ['swift', 'eval']
    
    // Parameter mapping
    const fields = [
      'model_id', 'ckpt_dir', 'eval_batch_size', 'eval_backend', 'temperature'
    ]
    
    fields.forEach(f => {
      if (form.value[f] !== '' && form.value[f] !== null) {
        command.push(`--${f}`, String(form.value[f]))
      }
    })

    // Handle datasets
    if (form.value.eval_dataset && form.value.eval_dataset.length > 0) {
      command.push('--eval_dataset', ...form.value.eval_dataset)
    }

    // Handle limit (0 means no limit, but usually swift expects explicit flag or omission)
    if (form.value.eval_limit > 0) {
      command.push('--eval_limit', String(form.value.eval_limit))
    }

    if (form.value.more_params) {
      command.push(...form.value.more_params.trim().split(/\s+/))
    }

    const logFile = `logs/eval_${Date.now()}.log`
    
    const res = await launchTraining({
      command,
      env: {},
      log_file: logFile
    })
    
    ElMessage.success('评测任务已启动!')
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
