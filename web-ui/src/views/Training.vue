<template>
  <el-container class="layout-container">
    <el-header>
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <span class="text-large font-600 mr-3"> Training: {{ type }} </span>
        </template>
      </el-page-header>
    </el-header>
    <el-main>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <template #header>Configuration</template>
            <el-form :model="form" label-width="120px">
              <el-form-item label="Model ID">
                <el-input v-model="form.model_id" placeholder="e.g. qwen/Qwen-7B-Chat" />
              </el-form-item>
              <el-form-item label="Dataset">
                <el-input v-model="form.dataset" placeholder="e.g. alpaca-en" />
              </el-form-item>
              <el-form-item label="Learning Rate">
                <el-input v-model="form.learning_rate" />
              </el-form-item>
              <el-form-item label="Epochs">
                <el-input-number v-model="form.num_train_epochs" :min="1" :max="100" />
              </el-form-item>
              <el-form-item label="Output Dir">
                 <el-input v-model="form.output_dir" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleLaunch" :loading="launching">Start Training</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card>
            <template #header>Log Output</template>
            <div class="log-container" ref="logContainer">
              <pre>{{ logs }}</pre>
            </div>
            <div style="margin-top: 10px;">
                <el-button @click="refreshLog">Refresh Log</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { launchTraining, getLog } from '../api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const type = route.params.type
const launching = ref(false)
const logs = ref('')
const currentLogFile = ref('')
const logOffset = ref(0)
const timer = ref(null)

const form = ref({
  model_id: 'qwen/Qwen-7B-Chat',
  dataset: 'alpaca-en',
  learning_rate: '1e-4',
  num_train_epochs: 1,
  output_dir: 'output/demo_' + Date.now()
})

const handleLaunch = async () => {
  launching.value = true
  try {
    // Construct command list (Simplified for demo)
    const command = [
      'swift', 'sft',
      '--model_id', form.value.model_id,
      '--dataset', form.value.dataset,
      '--learning_rate', form.value.learning_rate,
      '--num_train_epochs', String(form.value.num_train_epochs),
      '--output_dir', form.value.output_dir
    ]
    
    const res = await launchTraining({
      command: command,
      env: {},
      log_file: `${form.value.output_dir}/run.log`,
      work_dir: null
    })
    
    ElMessage.success('Training started!')
    currentLogFile.value = res.data.log_file
    logOffset.value = 0
    logs.value = ''
    startPolling()
    
  } catch (error) {
    ElMessage.error('Failed to launch: ' + error.message)
  } finally {
    launching.value = false
  }
}

const refreshLog = async () => {
    if (!currentLogFile.value) return
    try {
        const res = await getLog(currentLogFile.value, logOffset.value)
        if (res.data.content) {
            logs.value += res.data.content
            logOffset.value += res.data.length
        }
    } catch (e) {
        console.error(e)
    }
}

const startPolling = () => {
    if (timer.value) clearInterval(timer.value)
    timer.value = setInterval(refreshLog, 2000)
}

onUnmounted(() => {
    if (timer.value) clearInterval(timer.value)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background-color: #f5f7fa;
}
.el-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
}
.log-container {
  height: 400px;
  background: #1e1e1e;
  color: #fff;
  padding: 10px;
  overflow-y: auto;
  border-radius: 4px;
}
pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
}
</style>
