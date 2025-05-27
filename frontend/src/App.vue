<script setup>
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import axios from 'axios'

const authStore = useAuthStore()

onMounted(() => {
  // 确保清除旧的token状态
  delete axios.defaults.headers.common['Authorization']
  
  // 如果有token，为axios设置默认Authorization头，只使用Bearer前缀
  if (authStore.token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`
    console.log('应用启动时设置Authorization头:', `Bearer ${authStore.token}`)
  } else {
    console.log('应用启动时无Token')
  }
  
  // 设置axios拦截器处理token过期
  authStore.setupAxiosInterceptors()
})
</script>

<template>
  <div class="app-container">
    <RouterView />
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: #f5f5f5;
  color: #333;
}

.page-container {
  padding: 20px;
}

.section-title {
  margin-bottom: 20px;
  font-size: 24px;
  color: #1890ff;
}

.card {
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.btn-primary {
  background-color: #1890ff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #40a9ff;
}

.btn-danger {
  background-color: #f5222d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-danger:hover {
  background-color: #ff4d4f;
}
</style>
