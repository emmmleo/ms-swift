<template>
  <el-container class="layout-container">
    <el-header>
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <span class="text-large font-600 mr-3"> 指令监督微调 / 预训练 (SFT / PT) </span>
        </template>
      </el-page-header>
    </el-header>
    <el-main>
      <el-row :gutter="20">
        <el-col :span="14">
          <el-card>
            <el-tabs v-model="activeTab" class="demo-tabs">
              <el-tab-pane label="基础配置 (Basic)" name="basic">
                <el-form :model="form" label-width="140px">
                  <el-form-item label="模型 ID / 路径">
                    <el-input v-model="form.model_id" placeholder="e.g. qwen/Qwen-7B-Chat" />
                  </el-form-item>
                  <el-form-item label="输出目录">
                    <el-input v-model="form.output_dir" />
                  </el-form-item>
                  <el-form-item label="数据集">
                    <el-input v-model="form.dataset" placeholder="e.g. alpaca-zh, msm8k" />
                  </el-form-item>
                  <el-form-item label="微调类型">
                    <el-select v-model="form.sft_type">
                      <el-option label="LoRA" value="lora" />
                      <el-option label="Full (全量)" value="full" />
                      <el-option label="AdaLoRA" value="adalora" />
                    </el-select>
                  </el-form-item>
                </el-form>
              </el-tab-pane>

              <el-tab-pane label="训练参数 (Training)" name="train">
                <el-form :model="form" label-width="140px">
                  <el-form-item label="学习率">
                    <el-input v-model="form.learning_rate" />
                  </el-form-item>
                  <el-form-item label="训练轮数 (Epochs)">
                    <el-input-number v-model="form.num_train_epochs" :min="1" :max="100" />
                  </el-form-item>
                  <el-form-item label="Batch Size">
                    <el-input-number v-model="form.batch_size" :min="1" />
                  </el-form-item>
                  <el-form-item label="梯度累积步数">
                    <el-input-number v-model="form.gradient_accumulation_steps" :min="1" />
                  </el-form-item>
                  <el-form-item label="最大长度">
                    <el-input-number v-model="form.max_length" :min="128" :step="128" />
                  </el-form-item>
                </el-form>
              </el-tab-pane>

              <el-tab-pane label="LoRA / Tuner" name="lora">
                <el-form :model="form" label-width="140px">
                  <el-form-item label="LoRA Rank">
                    <el-input-number v-model="form.lora_rank" :min="1" />
                  </el-form-item>
                  <el-form-item label="LoRA Alpha">
                    <el-input-number v-model="form.lora_alpha" :min="1" />
                  </el-form-item>
                  <el-form-item label="LoRA Dropout">
                    <el-input v-model="form.lora_dropout" />
                  </el-form-item>
                  <el-form-item label="Target Modules">
                    <el-input v-model="form.lora_target_modules" placeholder="ALL or q_proj,v_proj" />
                  </el-form-item>
                </el-form>
              </el-tab-pane>
            </el-tabs>

            <div class="action-bar">
              <el-form :model="form" label-width="140px">
                <el-form-item label="高级参数">
                  <el-input 
                    v-model="form.more_params" 
                    placeholder='额外参数 (e.g. --beta 0.5)' 
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" size="large" @click="handleLaunch" :loading="launching">
                    🚀 开始 SFT 训练
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

const activeTab = ref('basic')
const launching = ref(false)
const currentLogFile = ref('')
const runningPid = ref(null)

const form = ref({
  model_id: 'qwen/Qwen-7B-Chat',
  output_dir: 'output/sft_' + Date.now(),
  dataset: 'alpaca-zh',
  sft_type: 'lora',
  learning_rate: '1e-4',
  num_train_epochs: 1,
  batch_size: 1,
  gradient_accumulation_steps: 16,
  max_length: 2048,
  lora_rank: 8,
  lora_alpha: 32,
  lora_dropout: 0.05,
  lora_target_modules: 'ALL',
  more_params: ''
})

const handleLaunch = async () => {
  launching.value = true
  try {
    const command = ['swift', 'sft']
    
    // Explicit mapping for SFT
    const fields = [
      'model_id', 'output_dir', 'dataset', 'sft_type',
      'learning_rate', 'num_train_epochs', 'batch_size',
      'gradient_accumulation_steps', 'max_length',
      'lora_rank', 'lora_alpha', 'lora_dropout', 'lora_target_modules'
    ]
    
    fields.forEach(f => {
      if (form.value[f]) command.push(`--${f}`, String(form.value[f]))
    })

    if (form.value.more_params) {
      command.push(...form.value.more_params.trim().split(/\s+/))
    }

    const logFile = `${form.value.output_dir}/sft.log`
    
    const res = await launchTraining({
      command,
      env: {},
      log_file: logFile
    })
    
    ElMessage.success('SFT 任务已启动!')
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
