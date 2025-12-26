<template>
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
        <el-button type="success" @click="openService" v-if="serviceUrl">打开服务</el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch, onUnmounted, nextTick } from 'vue'
import { getLog, killTask } from '../api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  logFile: String,
  outputDir: String,
  pid: Number,
  serviceUrl: String
})

const emit = defineEmits(['update:pid'])

const logs = ref('')
const logOffset = ref(0)
const timer = ref(null)
const runningPid = ref(props.pid)

watch(() => props.pid, (newVal) => {
  runningPid.value = newVal
  if (newVal) {
    startPolling()
  } else {
    stopPolling()
  }
})

watch(() => props.logFile, (newVal) => {
  if (newVal) {
    logs.value = ''
    logOffset.value = 0
    refreshLog()
  }
})

const startPolling = () => {
  if (timer.value) clearInterval(timer.value)
  timer.value = setInterval(refreshLog, 2000)
}

const stopPolling = () => {
  if (timer.value) clearInterval(timer.value)
  timer.value = null
}

const refreshLog = async () => {
  if (!props.logFile) return
  try {
    const res = await getLog(props.logFile, logOffset.value)
    if (res.data.content) {
      logs.value += res.data.content
      logOffset.value += res.data.length
      nextTick(() => {
        const container = document.querySelector('.log-container')
        if (container) container.scrollTop = container.scrollHeight
      })
    }
  } catch (e) {
    // console.error('Fetch log error', e)
  }
}

const handleStop = async () => {
  if (!runningPid.value) return
  try {
    await killTask(runningPid.value, props.outputDir)
    ElMessage.success('任务已停止')
    runningPid.value = null
    emit('update:pid', null)
    stopPolling()
  } catch (e) {
    ElMessage.error('停止失败: ' + e.message)
  }
}

const openService = () => {
  if (props.serviceUrl) {
    window.open(props.serviceUrl, '_blank')
  }
}

onUnmounted(() => {
  stopPolling()
})

// Expose refresh for parent if needed
defineExpose({ refreshLog })
</script>

<style scoped>
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
