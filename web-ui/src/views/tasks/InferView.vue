<template>
  <el-container class="layout-container">
    <el-header class="page-header">
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <div class="header-content">
            <span class="text-large font-600 mr-3">🤖 推理部署 (Inference / Deploy)</span>
            <el-tag type="primary" effect="plain" round>Model Serving & Inference</el-tag>
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
                  🚀 启动推理服务
                </el-button>
              </div>
            </div>
          </template>
          
          <el-tabs v-model="activeTab" class="config-tabs">
            <!-- 基础配置 -->
            <el-tab-pane label="服务配置 (Service)" name="service">
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
                  <el-input v-model="form.ckpt_dir" placeholder="微调后的 checkpoint 路径 (可选，覆盖模型ID)" />
                </el-form-item>

                <el-form-item label="推理后端">
                  <el-select v-model="form.infer_backend" placeholder="自动选择">
                    <el-option label="Auto" value="" />
                    <el-option label="vLLM" value="vllm" />
                    <el-option label="Pt (PyTorch)" value="pt" />
                    <el-option label="LMDeploy" value="lmdeploy" />
                  </el-select>
                </el-form-item>

                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="服务端口 (Port)">
                      <el-input-number v-model="form.port" :min="1024" :max="65535" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Host">
                      <el-input v-model="form.host" placeholder="0.0.0.0" />
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </el-tab-pane>

            <!-- 生成参数 -->
            <el-tab-pane label="生成参数 (Generation)" name="generation">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="Max New Tokens">
                      <el-input-number v-model="form.max_new_tokens" :min="1" :step="128" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Temperature">
                      <el-input-number v-model="form.temperature" :min="0" :step="0.1" :max="2" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-row :gutter="24">
                  <el-col :span="12">
                    <el-form-item label="Top K">
                      <el-input-number v-model="form.top_k" :min="0" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Top P">
                      <el-input-number v-model="form.top_p" :min="0" :max="1" :step="0.05" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="Repetition Penalty">
                  <el-input-number v-model="form.repetition_penalty" :step="0.1" :min="1" />
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 高级参数 -->
            <el-tab-pane label="高级参数 (Advanced)" name="advanced">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-form-item label="精度 (Dtype)">
                  <el-select v-model="form.torch_dtype">
                    <el-option label="Auto" value="" />
                    <el-option label="bf16" value="bfloat16" />
                    <el-option label="fp16" value="float16" />
                    <el-option label="fp32" value="float32" />
                  </el-select>
                </el-form-item>

                <el-form-item label="Max Model Length">
                  <el-input-number v-model="form.max_model_len" :min="0" :step="1024" placeholder="Auto" />
                  <div class="form-tip">vLLM 显存分配的关键参数，留空则自动</div>
                </el-form-item>

                <el-form-item label="GPU Utilisation">
                   <el-input-number v-model="form.gpu_memory_utilization" :min="0.1" :max="1.0" :step="0.05" />
                   <div class="form-tip">vLLM GPU 显存占用比例 (默认 0.9)</div>
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
                :output-dir="'logs/deploy'" 
                :service-url="serviceUrl"
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
import { launchTraining, getModels } from '../../api'
import { ElMessage } from 'element-plus'
import LogViewer from '../../components/LogViewer.vue'

const activeTab = ref('service')
const launching = ref(false)
const showLogs = ref(false)
const isMinimized = ref(false)
const currentLogFile = ref('')
const runningPid = ref(null)
const serviceUrl = ref('')

const modelOptions = ref([])

const form = ref({
  // Service
  model_id: 'qwen/Qwen-7B-Chat',
  ckpt_dir: '',
  port: 8000,
  host: '0.0.0.0',
  infer_backend: '',
  
  // Generation
  max_new_tokens: 2048,
  temperature: 0.3,
  top_k: 20,
  top_p: 0.7,
  repetition_penalty: 1.05,
  
  // Advanced
  torch_dtype: '',
  max_model_len: undefined,
  gpu_memory_utilization: 0.9,
  more_params: ''
})

onMounted(async () => {
  try {
    const mRes = await getModels()
    modelOptions.value = mRes.data.models || []
  } catch (e) {
    console.error('Failed to load options', e)
  }
})

const handleLaunch = async () => {
  launching.value = true
  try {
    const command = ['swift', 'deploy']
    
    // Parameter mapping
    const fields = [
      'model_id', 'ckpt_dir', 'port', 'host', 'infer_backend',
      'max_new_tokens', 'temperature', 'top_k', 'top_p', 'repetition_penalty',
      'torch_dtype', 'max_model_len', 'gpu_memory_utilization'
    ]
    
    fields.forEach(f => {
      if (form.value[f] !== '' && form.value[f] !== null && form.value[f] !== undefined) {
        command.push(`--${f}`, String(form.value[f]))
      }
    })

    if (form.value.more_params) {
      command.push(...form.value.more_params.trim().split(/\s+/))
    }

    const logFile = `logs/deploy_${Date.now()}.log`
    
    const res = await launchTraining({
      command,
      env: {},
      log_file: logFile
    })
    
    ElMessage.success('推理服务已启动!')
    currentLogFile.value = res.data.log_file
    runningPid.value = res.data.pid
    showLogs.value = true
    isMinimized.value = false
    
    // Construct service URL
    const hostname = window.location.hostname
    serviceUrl.value = `http://${hostname}:${form.value.port}`
    
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
