<template>
  <el-container class="layout-container">
    <el-header>
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <span class="text-large font-600 mr-3"> 人类偏好对齐 (RLHF / DPO) </span>
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
                  <el-form-item label="对齐算法">
                    <el-select v-model="form.rlhf_type">
                      <el-option label="DPO (直接偏好优化)" value="dpo" />
                      <el-option label="CPO" value="cpo" />
                      <el-option label="ORPO" value="orpo" />
                      <el-option label="SimPO" value="simpo" />
                      <el-option label="KTO" value="kto" />
                      <el-option label="PPO (近端策略优化)" value="ppo" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="模型 ID / 路径">
                    <el-input v-model="form.model_id" placeholder="SFT 后的模型路径" />
                  </el-form-item>
                  <el-form-item label="数据集">
                    <el-input v-model="form.dataset" placeholder="偏好数据集 (e.g. dpo-mix-7k)" />
                  </el-form-item>
                  <el-form-item label="输出目录">
                    <el-input v-model="form.output_dir" />
                  </el-form-item>
                </el-form>
              </el-tab-pane>

              <el-tab-pane label="高级配置 (Advanced)" name="advanced">
                <el-form :model="form" label-width="140px">
                  <el-form-item label="参考模型 (Ref Model)">
                    <el-input v-model="form.ref_model_id" placeholder="可选，默认与模型ID一致" />
                  </el-form-item>
                  <el-form-item label="学习率">
                    <el-input v-model="form.learning_rate" />
                  </el-form-item>
                  <el-form-item label="训练轮数">
                    <el-input-number v-model="form.num_train_epochs" :min="1" />
                  </el-form-item>
                  <el-form-item label="Beta / KL Coeff">
                    <el-input-number v-model="form.beta" :step="0.1" />
                  </el-form-item>
                </el-form>
              </el-tab-pane>
            </el-tabs>

            <div class="action-bar">
              <el-form :model="form" label-width="140px">
                <el-form-item label="高级参数">
                  <el-input 
                    v-model="form.more_params" 
                    placeholder='额外参数 (e.g. --max_length 1024)' 
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" size="large" @click="handleLaunch" :loading="launching">
                    🚀 开始对齐训练
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
  rlhf_type: 'dpo',
  model_id: 'qwen/Qwen-7B-Chat',
  dataset: '',
  output_dir: 'output/rlhf_' + Date.now(),
  ref_model_id: '',
  learning_rate: '5e-6',
  num_train_epochs: 1,
  beta: 0.1,
  more_params: ''
})

const handleLaunch = async () => {
  launching.value = true
  try {
    const command = ['swift', 'rlhf']
    
    const fields = [
      'rlhf_type', 'model_id', 'dataset', 'output_dir',
      'ref_model_id', 'learning_rate', 'num_train_epochs', 'beta'
    ]
    
    fields.forEach(f => {
      if (form.value[f]) command.push(`--${f}`, String(form.value[f]))
    })

    if (form.value.more_params) {
      command.push(...form.value.more_params.trim().split(/\s+/))
    }

    const logFile = `${form.value.output_dir}/rlhf.log`
    
    const res = await launchTraining({
      command,
      env: {},
      log_file: logFile
    })
    
    ElMessage.success('RLHF 任务已启动!')
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
