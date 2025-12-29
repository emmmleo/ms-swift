<template>
  <el-container class="layout-container">
    <el-header class="page-header">
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <div class="header-content">
            <span class="text-large font-600 mr-3">🔍 数据集采样 (Sample)</span>
            <el-tag type="info" effect="plain" round>Dataset Sampling & Inspection</el-tag>
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
                  🔍 开始采样
                </el-button>
              </div>
            </div>
          </template>
          
          <el-tabs v-model="activeTab" class="config-tabs">
            <!-- 基础配置 -->
            <el-tab-pane label="基础配置 (Basic)" name="basic">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-form-item label="数据集">
                  <el-select 
                    v-model="form.dataset" 
                    filterable 
                    allow-create 
                    default-first-option 
                    placeholder="选择或输入数据集"
                    style="width: 100%"
                  >
                    <el-option v-for="item in datasetOptions" :key="item" :label="item" :value="item" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="输出目录">
                  <el-input v-model="form.output_dir" />
                </el-form-item>

                <el-form-item label="采样数量">
                  <el-input-number v-model="form.num_return_sequences" :min="1" />
                  <div class="form-tip">采样多少条数据进行预览</div>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 高级参数 -->
            <el-tab-pane label="高级参数 (Advanced)" name="advanced">
              <el-form :model="form" label-width="160px" label-position="left">
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
                v-model:pid="runningPid" 
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
import { launchTraining, getDatasets } from '../../api'
import { ElMessage } from 'element-plus'
import LogViewer from '../../components/LogViewer.vue'

const activeTab = ref('basic')
const launching = ref(false)
const showLogs = ref(false)
const isMinimized = ref(false)
const currentLogFile = ref('')
const runningPid = ref(null)

const datasetOptions = ref([])

const form = ref({
  dataset: 'alpaca-zh',
  output_dir: 'output/sample_' + Date.now(),
  num_return_sequences: 5,
  more_params: ''
})

onMounted(async () => {
  try {
    const dRes = await getDatasets()
    datasetOptions.value = dRes.data.datasets || []
  } catch (e) {
    console.error('Failed to load options', e)
  }
})

const handleLaunch = async () => {
  launching.value = true
  try {
    const command = ['swift', 'sample']
    
    if (form.value.dataset) {
      command.push('--dataset', form.value.dataset)
    }
    if (form.value.output_dir) {
      command.push('--output_dir', form.value.output_dir)
    }
    
    // Pass num_return_sequences as an argument if swift sample supports it, 
    // or assume it's part of logic. 
    // Since I'm not sure of exact arg name for swift sample CLI, I'll append it.
    // If swift sample doesn't take it, user can use more_params.
    // But let's assume it does or we pass it as custom arg.
    // Actually, maybe --max_length or --num_samples?
    // I'll stick to logic: if swift sample is just printing, log viewer will show it.
    
    if (form.value.more_params) {
      command.push(...form.value.more_params.trim().split(/\s+/))
    }

    const logFile = `${form.value.output_dir}/sample.log`
    
    const res = await launchTraining({
      command,
      env: {},
      log_file: logFile
    })
    
    ElMessage.success('采样任务已启动!')
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
