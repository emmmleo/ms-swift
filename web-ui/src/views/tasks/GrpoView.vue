<template>
  <el-container class="layout-container">
    <el-header>
      <el-page-header @back="$router.push('/dashboard')">
        <template #content>
          <span class="text-large font-600 mr-3"> GRPO 训练 </span>
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
                  <el-form-item label="模型 ID">
                    <el-input v-model="form.model_id" placeholder="e.g. qwen/Qwen-7B-Chat" />
                  </el-form-item>
                  <el-form-item label="数据集">
                    <el-input v-model="form.dataset" placeholder="e.g. gsm8k" />
                  </el-form-item>
                  <el-form-item label="输出目录">
                    <el-input v-model="form.output_dir" />
                  </el-form-item>
                  <el-form-item label="训练轮数">
                    <el-input-number v-model="form.num_train_epochs" :min="1" />
                  </el-form-item>
                  <el-form-item label="学习率">
                    <el-input v-model="form.learning_rate" />
                  </el-form-item>
                </el-form>
              </el-tab-pane>

              <el-tab-pane label="GRPO 参数" name="grpo">
                <el-form :model="form" label-width="140px">
                  <el-form-item label="奖励函数 (Reward)">
                    <el-select v-model="form.reward_funcs" multiple placeholder="Select reward functions">
                      <el-option label="Accuracy" value="accuracy" />
                      <el-option label="Format" value="format" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="生成数量 (Num Gens)">
                    <el-input-number v-model="form.num_generations" :min="1" />
                  </el-form-item>
                  <el-form-item label="Max Completion Length">
                    <el-input-number v-model="form.max_completion_length" :min="128" :step="128" />
                  </el-form-item>
                  <el-form-item label="Use VLLM">
                    <el-switch v-model="form.use_vllm" />
                  </el-form-item>
                </el-form>
              </el-tab-pane>
            </el-tabs>

            <div class="action-bar">
              <el-form :model="form" label-width="140px">
                <el-form-item label="高级参数">
                  <el-input 
                    v-model="form.more_params" 
                    placeholder='额外参数 (e.g. --beta 0.01)' 
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" size="large" @click="handleLaunch" :loading="launching">
                    🚀 开始 GRPO 训练
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
  dataset: 'gsm8k',
  output_dir: 'output/grpo_' + Date.now(),
  learning_rate: '1e-5',
  num_train_epochs: 1,
  reward_funcs: ['accuracy'],
  num_generations: 4,
  max_completion_length: 1024,
  use_vllm: false,
  more_params: ''
})

const handleLaunch = async () => {
  launching.value = true
  try {
    const command = ['swift', 'rlhf', '--rlhf_type', 'grpo']
    
    const fields = [
      'model_id', 'dataset', 'output_dir', 'learning_rate', 'num_train_epochs',
      'num_generations', 'max_completion_length'
    ]
    
    fields.forEach(f => {
      if (form.value[f]) command.push(`--${f}`, String(form.value[f]))
    })

    if (form.value.reward_funcs && form.value.reward_funcs.length > 0) {
      command.push('--reward_funcs', ...form.value.reward_funcs)
    }

    if (form.value.use_vllm) {
      command.push('--use_vllm', 'true')
    }

    if (form.value.more_params) {
      command.push(...form.value.more_params.trim().split(/\s+/))
    }

    const logFile = `${form.value.output_dir}/grpo.log`
    
    const res = await launchTraining({
      command,
      env: {},
      log_file: logFile
    })
    
    ElMessage.success('GRPO 任务已启动!')
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
