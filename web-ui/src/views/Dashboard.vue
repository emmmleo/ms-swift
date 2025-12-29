<template>
  <el-container class="layout-container">
    <el-aside width="220px">
      <el-menu
        default-active="1"
        class="el-menu-vertical-demo"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Menu /></el-icon>
          <span>首页 (Home)</span>
        </el-menu-item>
        
        <el-menu-item-group title="训练 (Training)">
          <el-menu-item index="/training/sft">
            <el-icon><Edit /></el-icon>
            <span>预训练/微调 (SFT/PT)</span>
          </el-menu-item>
          <el-menu-item index="/training/rl">
            <el-icon><Aim /></el-icon>
            <span>强化学习 (RL)</span>
          </el-menu-item>
        </el-menu-item-group>

        <el-menu-item-group title="推理与评估 (Infer & Eval)">
          <el-menu-item index="/training/infer">
            <el-icon><Monitor /></el-icon>
            <span>推理部署 (Inference)</span>
          </el-menu-item>
          <el-menu-item index="/training/eval">
            <el-icon><DataLine /></el-icon>
            <span>模型评测 (Evaluation)</span>
          </el-menu-item>
        </el-menu-item-group>

        <el-menu-item-group title="工具 (Tools)">
          <el-menu-item index="/training/export">
            <el-icon><Box /></el-icon>
            <span>模型导出 (Export)</span>
          </el-menu-item>
          <el-menu-item index="/training/sample">
            <el-icon><ChatDotSquare /></el-icon>
            <span>数据集采样 (Sample)</span>
          </el-menu-item>
        </el-menu-item-group>

      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="text-align: right; font-size: 12px">
        <el-dropdown @command="handleCommand">
          <el-icon style="margin-right: 8px; margin-top: 1px"><Setting /></el-icon>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <span>{{ username }}</span>
      </el-header>
      <el-main>
        <el-row :gutter="20">
          <el-col :span="6" v-for="item in menuItems" :key="item.path">
            <el-card shadow="hover" @click="$router.push(item.path)" class="box-card">
              <template #header>
                <div class="card-header">
                  <span>{{ item.icon }} {{ item.title }}</span>
                </div>
              </template>
              <div class="text item">
                {{ item.desc }}
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref(localStorage.getItem('username') || 'User')

const menuItems = [
  { path: '/training/sft', title: 'SFT / PT', desc: '指令监督微调 / 预训练', icon: '🚀' },
  { path: '/training/rl', title: 'Reinforcement Learning', desc: '强化学习 (RLHF / DPO / GRPO)', icon: '🧠' },
  { path: '/training/infer', title: 'Inference', desc: '模型推理与Web部署', icon: '🤖' },
  { path: '/training/eval', title: 'Evaluation', desc: '模型能力评测 (CEval, MMLU...)', icon: '📊' },
  { path: '/training/export', title: 'Export', desc: '模型导出与量化 (AWQ, GPTQ)', icon: '📦' },
  { path: '/training/sample', title: 'Sample', desc: '数据集采样与查看', icon: '🔍' },
]

const handleCommand = (command) => {
  if (command === 'logout') {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.el-header {
  background-color: #fff;
  color: var(--el-text-color-primary);
  line-height: 60px;
  border-bottom: 1px solid #e6e6e6;
}
.el-aside {
  color: var(--el-text-color-primary);
  background: #fff;
  border-right: 1px solid #e6e6e6;
}
.box-card {
  cursor: pointer;
  height: 200px;
}
.card-header {
  font-weight: bold;
}
</style>
