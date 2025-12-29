<template>
  <div class="terminal-wrapper">
    <!-- Terminal Toolbar -->
    <div class="terminal-toolbar">
      <div class="left-section">
        <div class="status-indicator">
          <span class="status-dot" :class="{ 'running': runningPid }"></span>
          <span class="status-text">{{ runningPid ? `RUNNING (PID: ${runningPid})` : 'STOPPED' }}</span>
        </div>
      </div>
      
      <div class="right-section">
        <el-tooltip content="Auto-scroll to bottom" placement="top">
          <div class="action-btn" :class="{ active: autoScroll }" @click="toggleAutoScroll">
            <i class="scroll-icon">⬇</i>
          </div>
        </el-tooltip>
        
        <el-divider direction="vertical" class="divider" />
        
        <el-button 
          type="danger" 
          size="small" 
          link 
          @click="handleStop" 
          :disabled="!runningPid"
          class="stop-btn"
        >
          ⏹ 停止
        </el-button>
        
        <el-button 
          type="primary" 
          size="small" 
          link 
          @click="openService" 
          v-if="serviceUrl"
        >
          🌐 服务
        </el-button>
        
        <el-button size="small" link @click="copyLogs">
          📋 复制
        </el-button>
        
        <el-button size="small" link @click="clearLogs">
          🗑️ 清空
        </el-button>

        <el-divider direction="vertical" class="divider" />

        <div class="window-controls">
          <div class="control-btn minimize" @click="$emit('toggle-minimize')">
            <span v-if="minimized">□</span>
            <span v-else>_</span>
          </div>
          <div class="control-btn close" @click="$emit('close')">
            ✕
          </div>
        </div>
      </div>
    </div>

    <!-- Terminal Content -->
    <div class="terminal-content" ref="logContainer" @scroll="handleScroll">
      <pre class="log-text" v-if="logs">{{ logs }}</pre>
      <div v-else class="empty-state">等待日志输出...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted, nextTick, computed } from 'vue'
import { getLog, killTask } from '../api'
import { ElMessage } from 'element-plus'

const props = defineProps({
  logFile: String,
  outputDir: String,
  pid: Number,
  serviceUrl: String,
  minimized: Boolean
})

const emit = defineEmits(['update:pid', 'toggle-minimize', 'close'])

const logs = ref('')
const logOffset = ref(0)
const timer = ref(null)
const runningPid = ref(props.pid)
const logContainer = ref(null)
const autoScroll = ref(true)

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
    clearLogs()
    refreshLog()
  }
})

const startPolling = () => {
  if (timer.value) clearInterval(timer.value)
  // Faster polling (1s) for real-time feel
  timer.value = setInterval(refreshLog, 1000)
}

const stopPolling = () => {
  if (timer.value) clearInterval(timer.value)
  timer.value = null
}

const refreshLog = async () => {
  if (!props.logFile) return
  try {
    // Fetch larger chunks
    const res = await getLog(props.logFile, logOffset.value, 102400)
    if (res.data.content) {
      logs.value += res.data.content
      logOffset.value += res.data.length
      
      // Prevent memory explosion: keep last 500k chars
      if (logs.value.length > 500000) {
        logs.value = logs.value.slice(-500000)
      }

      if (autoScroll.value) {
        scrollToBottom()
      }
    }
  } catch (e) {
    // Silent fail for polling
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

const handleScroll = () => {
  if (!logContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = logContainer.value
  // If user scrolls up, disable auto-scroll
  if (scrollHeight - scrollTop - clientHeight > 50) {
    autoScroll.value = false
  } else {
    autoScroll.value = true
  }
}

const toggleAutoScroll = () => {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) scrollToBottom()
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

const copyLogs = async () => {
  try {
    await navigator.clipboard.writeText(logs.value)
    ElMessage.success('日志已复制')
  } catch (e) {
    ElMessage.error('复制失败')
  }
}

const clearLogs = () => {
  logs.value = ''
  logOffset.value = 0
}

onUnmounted(() => {
  stopPolling()
})

defineExpose({ refreshLog })
</script>

<style scoped>
.terminal-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #1e1e1e;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
  border: 1px solid #333;
}

.terminal-toolbar {
  height: 40px;
  background-color: #252526;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 12px;
  flex-shrink: 0;
}

.left-section {
  display: flex;
  align-items: center;
}

.right-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #ccc;
  font-family: 'Segoe UI', sans-serif;
  font-weight: 600;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #666;
  transition: all 0.3s ease;
}

.status-dot.running {
  background-color: #4caf50;
  box-shadow: 0 0 8px rgba(76, 175, 80, 0.6);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.divider {
  border-color: #444;
  height: 16px;
  margin: 0 4px;
}

.action-btn {
  cursor: pointer;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  color: #888;
  transition: all 0.2s;
}

.action-btn:hover {
  background-color: #3e3e42;
  color: #fff;
}

.action-btn.active {
  color: #4caf50;
}

.scroll-icon {
  font-style: normal;
  font-size: 14px;
}

.terminal-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #d4d4d4;
  scroll-behavior: smooth;
}

.log-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.empty-state {
  color: #666;
  text-align: center;
  margin-top: 40px;
  font-style: italic;
}

/* Scrollbar styling */
.terminal-content::-webkit-scrollbar {
  width: 10px;
}

.terminal-content::-webkit-scrollbar-track {
  background: #1e1e1e;
}

.terminal-content::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 5px;
  border: 2px solid #1e1e1e;
}

.terminal-content::-webkit-scrollbar-thumb:hover {
  background: #505050;
}

.window-controls {
  display: flex;
  gap: 8px;
  margin-left: 8px;
}

.control-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 4px;
  color: #ccc;
  font-size: 14px;
  transition: background 0.2s;
}

.control-btn:hover {
  background: #3e3e42;
  color: #fff;
}

.control-btn.close:hover {
  background: #c42b1c;
}
</style>
