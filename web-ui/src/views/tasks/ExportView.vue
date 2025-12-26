<template>
  <el-container class="layout-container">
    <el-header>
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <span class="text-large font-600 mr-3"> 模型导出 (Export) </span>
        </template>
      </el-page-header>
    </el-header>
    <el-main>
      <el-row :gutter="20">
        <el-col :span="14">
          <el-card>
            <el-tabs v-model="activeTab" class="demo-tabs">
              <el-tab-pane label="导出配置 (Config)" name="config">
                <el-form :model="form" label-width="140px">
                  <el-form-item label="模型 ID">
                    <el-input v-model="form.model_id" placeholder="e.g. qwen/Qwen-7B-Chat" />
                  </el-form-item>
                  <el-form-item label="Checkpoint 目录">
                    <el-input v-model="form.ckpt_dir" placeholder="可选: 微调后的 checkpoint 路径" />
                  </el-form-item>
                  <el-form-item label="输出目录">
                    <el-input v-model="form.output_dir" />
                  </el-form-item>
                  <el-form-item label="导出格式">
                    <el-select v-model="form.export_format">
                      <el-option label="AWQ (量化)" value="awq" />
                      <el-option label="GPTQ (量化)" value="gptq" />
                      <el-option label="ONNX" value="onnx" />
                      <el-option label="Ollama (GGUF)" value="ollama" />
                      <el-option label="VLLM" value="vllm" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="量化位数" v-if="['awq', 'gptq'].includes(form.export_format)">
                    <el-select v-model="form.quant_bits">
                      <el-option label="4-bit" :value="4" />
                      <el-option label="8-bit" :value="8" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="Push to Hub">
                    <el-switch v-model="form.push_to_hub" />
                  </el-form-item>
                </el-form>
              </el-tab-pane>
            </el-tabs>

            <div class="action-bar">
              <el-form :model="form" label-width="140px">
                <el-form-item label="高级参数">
                  <el-input 
                    v-model="form.more_params" 
                    placeholder='额外参数 (e.g. --dataset alpaca-zh)' 
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" size="large" @click="handleLaunch" :loading="launching">
                    📦 开始导出
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </el-col>

        <el-col :span="10">
          <LogViewer 
            :log-file="currentLogFile" 
            :output-dir="form.output_dir"
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

const activeTab = ref('config')
const launching = ref(false)
const currentLogFile = ref('')
const runningPid = ref(null)

const form = ref({
  model_id: 'qwen/Qwen-7B-Chat',
  ckpt_dir: '',
  output_dir: 'output/export_' + Date.now(),
  export_format: 'awq',
  quant_bits: 4,
  push_to_hub: false,
  more_params: ''
})

const handleLaunch = async () => {
  launching.value = true
  try {
    const command = ['swift', 'export']
    
    // Logic for combining model_id or ckpt_dir
    // Swift export usually takes ckpt_dir as positional or --ckpt_dir
    if (form.value.ckpt_dir) {
      command.push('--ckpt_dir', form.value.ckpt_dir)
    }
    if (form.value.model_id) {
      command.push('--model_id', form.value.model_id)
    }
    
    command.push('--output_dir', form.value.output_dir)
    
    if (['awq', 'gptq'].includes(form.value.export_format)) {
      command.push('--quant_method', form.value.export_format)
      command.push('--quant_bits', String(form.value.quant_bits))
    } else if (form.value.export_format === 'onnx') {
      command.push('--to_onnx', 'true')
    } else if (form.value.export_format === 'ollama') {
      command.push('--to_ollama', 'true')
    }

    if (form.value.push_to_hub) {
      command.push('--push_to_hub', 'true')
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
