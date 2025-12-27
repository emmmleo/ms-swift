<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo">🚀</div>
        <h1>Swift 训练平台</h1>
        <p>让大模型训练更简单、更高效</p>
      </div>
      
      <el-card class="login-card" shadow="hover">
        <el-form :model="form" @submit.prevent="handleLogin" size="large">
          <el-form-item>
            <el-input 
              v-model="form.username" 
              placeholder="请输入用户名" 
              :prefix-icon="User"
            />
          </el-form-item>
          <el-form-item>
            <el-input 
              v-model="form.password" 
              type="password" 
              placeholder="请输入密码" 
              :prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" class="login-btn" @click="handleLogin" :loading="loading" round>
              立即登录
            </el-button>
          </el-form-item>
        </el-form>
        
        <div class="login-footer">
          <span class="tips">默认账号: admin / swift</span>
        </div>
      </el-card>

      <div class="copyright">
        © {{ new Date().getFullYear() }} AI Intelligent Cloud Team. All Rights Reserved.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const form = ref({
  username: '',
  password: ''
})
const loading = ref(false)

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  
  loading.value = true
  try {
    const res = await login(form.value.username, form.value.password)
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('username', res.data.username)
    ElMessage.success('登录成功，欢迎回来！')
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error('登录失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

/* Background decoration */
.login-container::before {
  content: '';
  position: absolute;
  top: -10%;
  left: -10%;
  width: 50%;
  height: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%);
  border-radius: 50%;
}

.login-box {
  width: 420px;
  padding: 20px;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
  color: white;
}

.logo {
  font-size: 48px;
  margin-bottom: 10px;
  animation: float 3s ease-in-out infinite;
}

.login-header h1 {
  font-size: 28px;
  margin: 10px 0;
  font-weight: 600;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.login-header p {
  font-size: 14px;
  opacity: 0.9;
  margin: 0;
}

.login-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 8px 30px rgba(0,0,0,0.2) !important;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 20px 10px;
}

.login-btn {
  width: 100%;
  font-weight: bold;
  font-size: 16px;
  height: 45px;
  background: linear-gradient(to right, #667eea, #764ba2);
  border: none;
  transition: transform 0.2s;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(118, 75, 162, 0.3);
}

.login-footer {
  text-align: center;
  margin-top: 15px;
}

.tips {
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  padding: 4px 12px;
  border-radius: 12px;
}

.copyright {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  margin-top: 30px;
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}
</style>
