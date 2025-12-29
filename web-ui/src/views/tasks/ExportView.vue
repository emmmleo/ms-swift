<template>
  <el-container class="layout-container">
    <el-header class="page-header">
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <div class="header-content">
            <span class="text-large font-600 mr-3">📦 模型导出 (Export)</span>
            <el-tag type="info" effect="plain" round>Model Export & Quantization</el-tag>
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
                  🚀 开始导出
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

                <el-form-item label="输出目录">
                  <el-input v-model="form.output_dir" />
                </el-form-item>

                <el-form-item label="导出类型">
                  <el-select v-model="form.export_type" placeholder="选择导出类型">
                    <el-option label="Merge LoRA (合并权重)" value="merge_lora" />
                    <el-option label="Quantization (量化)" value="quant" />
                    <el-option label="Ollama (GGUF)" value="ollama" />
                  </el-select>
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 量化配置 -->
            <el-tab-pane label="量化配置 (Quantization)" name="quant" v-if="form.export_type === 'quant'">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-form-item label="量化方法">
                  <el-select v-model="form.quant_method">
                    <el-option label="AWQ" value="awq" />
                    <el-option label="GPTQ" value="gptq" />
                    <el-option label="BnB (BitsAndBytes)" value="bnb" />
                  </el-select>
                </el-form-item>

                <el-form-item label="量化位数">
                  <el-select v-model="form.quant_bits">
                    <el-option label="4-bit" :value="4" />
                    <el-option label="8-bit" :value="8" />
                  </el-select>
                </el-form-item>

                <el-form-item label="量化数据集">
                  <el-input v-model="form.dataset" placeholder="用于校准的数据集 (e.g. alpaca-zh)" />
                </el-form-item>
                
                <el-form-item label="量化样本数">
                  <el-input-number v-model="form.quant_n_samples" :min="1" />
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <!-- 高级参数 -->
            <el-tab-pane label="高级参数 (Advanced)" name="advanced">
              <el-form :model="form" label-width="160px" label-position="left">
                <el-form-item label="Push to Hub">
                  <el-switch v-model="form.push_to_hub" />
                  <div class="form-tip">导出后自动上传到 HuggingFace / ModelScope</div>
                </el-form-item>

                <el-form-item label="Hub Token">
                  <el-input v-model="form.hub_token" placeholder="Optional" />
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
import { launchTraining, getModels } from '../../api'
import { ElMessage } from 'element-plus'
import LogViewer from '../../components/LogViewer.vue'

const activeTab = ref('basic')
const launching = ref(false)
const showLogs = ref(false)
const isMinimized = ref(false)
const currentLogFile = ref('')
const runningPid = ref(null)

const modelOptions = ref([])

const form = ref({
  // Basic
  model_id: 'qwen/Qwen-7B-Chat',
  ckpt_dir: '',
  output_dir: 'output/export_' + Date.now(),
  export_type: 'merge_lora', // merge_lora, quant, onnx, ollama
  
  // Quant
  quant_method: 'awq',
  quant_bits: 4,
  dataset: '',
  quant_n_samples: 256,
  
  // Advanced
  push_to_hub: false,
  hub_token: '',
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
    const command = ['swift', 'export']
    
    // Logic for combining model_id or ckpt_dir
    if (form.value.ckpt_dir) {
      command.push('--ckpt_dir', form.value.ckpt_dir)
    }
    if (form.value.model_id) {
      command.push('--model_id', form.value.model_id)
    }
    
    command.push('--output_dir', form.value.output_dir)
    
    if (form.value.export_type === 'merge_lora') {
      command.push('--merge_lora', 'true')
    } else if (form.value.export_type === 'quant') {
      command.push('--quant_method', form.value.quant_method)
      command.push('--quant_bits', String(form.value.quant_bits))
      if (form.value.dataset) {
        command.push('--dataset', form.value.dataset)
      }
      command.push('--quant_n_samples', String(form.value.quant_n_samples))
    } else if (form.value.export_type === 'ollama') {
      command.push('--to_ollama', 'true')
    }

    if (form.value.push_to_hub) {
      command.push('--push_to_hub', 'true')
      if (form.value.hub_token) {
        command.push('--hub_token', form.value.hub_token)
      }
    }

    if (form.value.more_params) {
      command.push(...form.value.more_params.trim().split(/\s+/))
    }

    const logFile = `${form.value.output_dir}/export.log`
    
    const res = await launchTraining({
      command,
      env: {},
      log_file: logFile
    })
    
    ElMessage.success('导出任务已启动!')
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
