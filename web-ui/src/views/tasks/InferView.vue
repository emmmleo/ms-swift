<template>
  <el-container class="layout-container">
    <el-header>
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <span class="text-large font-600 mr-3"> 推理部署 (Inference) </span>
        </template>
      </el-page-header>
    </el-header>
    <el-main>
      <el-row :gutter="20">
        <el-col :span="14">
          <el-card>
            <el-tabs v-model="activeTab" class="demo-tabs">
              <el-tab-pane label="服务配置 (Service)" name="service">
                <el-form :model="form" label-width="140px">
                  <el-form-item label="模型 ID">
                    <el-input v-model="form.model_id" placeholder="e.g. qwen/Qwen-7B-Chat" />
                  </el-form-item>
                  <el-form-item label="Checkpoint 目录">
                    <el-input v-model="form.ckpt_dir" placeholder="微调后的 checkpoint 路径 (可选)" />
                  </el-form-item>
                  <el-form-item label="服务端口">
                    <el-input-number v-model="form.port" :min="1024" :max="65535" />
                  </el-form-item>
                  <el-form-item label="Host">
                    <el-input v-model="form.host" placeholder="0.0.0.0" />
                  </el-form-item>
                </el-form>
              </el-tab-pane>

              <el-tab-pane label="生成参数 (Generation)" name="generation">
                <el-form :model="form" label-width="140px">
                  <el-form-item label="Max New Tokens">
                    <el-input-number v-model="form.max_new_tokens" :min="1" :step="128" />
                  </el-form-item>
                  <el-form-item label="Temperature">
                    <el-input-number v-model="form.temperature" :min="0" :step="0.1" :max="2" />
                  </el-form-item>
                  <el-form-item label="Top K">
                    <el-input-number v-model="form.top_k" :min="0" />
                  </el-form-item>
                  <el-form-item label="Top P">
                    <el-input-number v-model="form.top_p" :min="0" :max="1" :step="0.05" />
                  </el-form-item>
                </el-form>
              </el-tab-pane>
            </el-tabs>

            <div class="action-bar">
              <el-form :model="form" label-width="140px">
                <el-form-item label="高级参数">
                  <el-input 
                    v-model="form.more_params" 
                    placeholder='额外参数 (e.g. --dtype bf16)' 
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" size="large" @click="handleLaunch" :loading="launching">
                    🚀 启动推理服务
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </el-col>

        <el-col :span="10">
          <LogViewer 
            :log-file="currentLogFile" 
            :output-dir="'logs/deploy'"
            :service-url="serviceUrl"
            v-model:pid="runningPid" 
          />
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { launchTraining } from '../../api'
import { ElMessage } from 'element-plus'
import LogViewer from '../../components/LogViewer.vue'

const activeTab = ref('service')
const launching = ref(false)
const currentLogFile = ref('')
const runningPid = ref(null)
const serviceUrl = ref('')

const form = ref({
  model_id: 'qwen/Qwen-7B-Chat',
  ckpt_dir: '',
  port: 8000,
  host: '0.0.0.0',
  max_new_tokens: 2048,
  temperature: 0.3,
  top_k: 20,
  top_p: 0.7,
  more_params: ''
})

const handleLaunch = async () => {
  launching.value = true
  try {
    const command = ['swift', 'deploy']
    
    const fields = [
      'model_id', 'ckpt_dir', 'port', 'host',
      'max_new_tokens', 'temperature', 'top_k', 'top_p'
    ]
    
    fields.forEach(f => {
      if (form.value[f] !== '' && form.value[f] !== null) {
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
    
    // Construct service URL (assuming localhost for browser access if host is 0.0.0.0)
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
.layout-container { height: 100vh; }
.action-bar { margin-top: 20px; border-top: 1px solid #eee; padding-top: 20px; }
</style>
