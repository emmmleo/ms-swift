<template>
  <el-container class="layout-container">
    <el-header>
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <span class="text-large font-600 mr-3"> 模型评测 (Evaluation) </span>
        </template>
      </el-page-header>
    </el-header>
    <el-main>
      <el-row :gutter="20">
        <el-col :span="14">
          <el-card>
            <el-tabs v-model="activeTab" class="demo-tabs">
              <el-tab-pane label="评测配置 (Config)" name="config">
                <el-form :model="form" label-width="140px">
                  <el-form-item label="模型 ID">
                    <el-input v-model="form.model_id" placeholder="e.g. qwen/Qwen-7B-Chat" />
                  </el-form-item>
                  <el-form-item label="Checkpoint 目录">
                    <el-input v-model="form.ckpt_dir" placeholder="可选: 微调后的 checkpoint 路径" />
                  </el-form-item>
                  <el-form-item label="评测数据集">
                    <el-select v-model="form.eval_dataset" multiple placeholder="Select datasets">
                      <el-option label="CEval" value="ceval" />
                      <el-option label="MMLU" value="mmlu" />
                      <el-option label="GSM8K" value="gsm8k" />
                      <el-option label="ARC" value="arc" />
                      <el-option label="BBH" value="bbh" />
                      <el-option label="TruthfulQA" value="truthfulqa" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="采样数量限制">
                    <el-input-number v-model="form.eval_limit" :min="0" />
                    <div class="form-desc">每个子数据集的采样样本数，留空或0表示全量评测</div>
                  </el-form-item>
                  <el-form-item label="Batch Size">
                    <el-input-number v-model="form.eval_batch_size" :min="1" />
                  </el-form-item>
                </el-form>
              </el-tab-pane>
            </el-tabs>

            <div class="action-bar">
              <el-form :model="form" label-width="140px">
                <el-form-item label="高级参数">
                  <el-input 
                    v-model="form.more_params" 
                    placeholder='额外参数 (e.g. --temperature 0)' 
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" size="large" @click="handleLaunch" :loading="launching">
                    🚀 开始评测
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </el-col>

        <el-col :span="10">
          <LogViewer 
            :log-file="currentLogFile" 
            :output-dir="'logs/eval'"
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
  eval_dataset: ['ceval', 'mmlu'],
  eval_limit: 10,
  eval_batch_size: 4,
  more_params: ''
})

const handleLaunch = async () => {
  launching.value = true
  try {
    const command = ['swift', 'eval']
    
    if (form.value.model_id) command.push('--model_id', form.value.model_id)
    if (form.value.ckpt_dir) command.push('--ckpt_dir', form.value.ckpt_dir)
    if (form.value.eval_dataset && form.value.eval_dataset.length > 0) {
      command.push('--eval_dataset', ...form.value.eval_dataset)
    }
    if (form.value.eval_limit > 0) command.push('--eval_limit', String(form.value.eval_limit))
    if (form.value.eval_batch_size) command.push('--eval_batch_size', String(form.value.eval_batch_size))

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
    
  } catch (error) {
    ElMessage.error('启动失败: ' + error.message)
  } finally {
    launching.value = false
  }
}
</script>

<style scoped>
.layout-container { height: 100vh; }
.form-desc { font-size: 12px; color: #999; margin-top: 5px; }
.action-bar { margin-top: 20px; border-top: 1px solid #eee; padding-top: 20px; }
</style>
