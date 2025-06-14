<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { imageService, taskService, reportService } from '../services/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const images = ref([])
const tasks = ref([])
const reports = ref([])
const loading = ref({
  images: false,
  tasks: false,
  reports: false
})

// 添加缓存机制
const dataCache = ref({
  images: null,
  tasks: null,
  reports: null,
  lastFetchTime: null
})
const CACHE_DURATION = 3 * 60 * 1000 // 3分钟缓存（仪表盘数据更新频率可以高一些）

// 时间格式化函数
const formatDateTime = (dateString) => {
  if (!dateString) return '未知时间'
  
  try {
    const date = new Date(dateString)
    if (isNaN(date.getTime())) {
      console.warn('无效的日期格式:', dateString)
      return '时间格式错误'
    }
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    console.error('日期格式化错误:', error, dateString)
    return '时间解析失败'
  }
}

// 检查缓存是否有效
const isCacheValid = () => {
  if (!dataCache.value.lastFetchTime) return false
  return Date.now() - dataCache.value.lastFetchTime < CACHE_DURATION
}

onMounted(async () => {
  await fetchData()
})

const fetchData = async () => {
  // 如果缓存有效，使用缓存数据
  if (isCacheValid() && dataCache.value.images && dataCache.value.tasks && dataCache.value.reports) {
    images.value = dataCache.value.images
    tasks.value = dataCache.value.tasks
    reports.value = dataCache.value.reports
    console.log('使用缓存的仪表盘数据')
    return
  }

  console.log('开始获取仪表盘数据...')
  
  // 并行获取所有数据
  const fetchPromises = [
    fetchImages(),
    fetchTasks(),
    fetchReports()
  ]
  
  try {
    await Promise.all(fetchPromises)
    
    // 更新缓存
    dataCache.value = {
      images: images.value,
      tasks: tasks.value,
      reports: reports.value,
      lastFetchTime: Date.now()
    }
    
    console.log('仪表盘数据加载完成')
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
    ElMessage.error('部分数据加载失败，请刷新页面重试')
  }
}

const fetchImages = async () => {
  loading.value.images = true
  try {
    const response = await imageService.getAll()
    images.value = response.data || []
  } catch (error) {
    console.error('获取图片失败:', error)
    ElMessage.error('获取图片数据失败')
    images.value = []
  } finally {
    loading.value.images = false
  }
}

const fetchTasks = async () => {
  loading.value.tasks = true
  try {
    const response = await taskService.getAll()
    tasks.value = response.data || []
  } catch (error) {
    console.error('获取任务失败:', error)
    ElMessage.error('获取任务数据失败')
    tasks.value = []
  } finally {
    loading.value.tasks = false
  }
}

const fetchReports = async () => {
  loading.value.reports = true
  try {
    const response = await reportService.getAll()
    reports.value = response.data || []
  } catch (error) {
    console.error('获取报告失败:', error)
    ElMessage.error('获取报告数据失败')
    reports.value = []
  } finally {
    loading.value.reports = false
  }
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const navigateTo = (path) => {
  router.push(path)
}
</script>

<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>图像处理系统</h1>
      <div class="user-info">
        <span v-if="authStore.user">{{ authStore.user.username }}</span>
        <button class="logout-button" @click="logout">退出登录</button>
      </div>
    </header>
    
    <div class="dashboard-content">
      <div class="dashboard-nav">
        <div class="nav-item" @click="navigateTo('/dashboard')">
          <span class="nav-icon">📊</span>
          <span class="nav-text">仪表盘</span>
        </div>
        <div class="nav-item" @click="navigateTo('/images')">
          <span class="nav-icon">🖼️</span>
          <span class="nav-text">图片管理</span>
        </div>
        <div class="nav-item" @click="navigateTo('/tasks')">
          <span class="nav-icon">📋</span>
          <span class="nav-text">任务管理</span>
        </div>
        <div class="nav-item" @click="navigateTo('/reports')">
          <span class="nav-icon">📝</span>
          <span class="nav-text">报告管理</span>
        </div>
      </div>
      
      <div class="dashboard-main">
        <div class="dashboard-overview">
          <div class="stat-card">
            <h3>图片总数</h3>
            <div class="stat-value">
              <span v-if="loading.images">加载中...</span>
              <span v-else>{{ images.length }}</span>
            </div>
            <button class="card-action" @click="navigateTo('/images')">查看图片</button>
          </div>
          
          <div class="stat-card">
            <h3>任务总数</h3>
            <div class="stat-value">
              <span v-if="loading.tasks">加载中...</span>
              <span v-else>{{ tasks.length }}</span>
            </div>
            <button class="card-action" @click="navigateTo('/tasks')">查看任务</button>
          </div>
          
          <div class="stat-card">
            <h3>报告总数</h3>
            <div class="stat-value">
              <span v-if="loading.reports">加载中...</span>
              <span v-else>{{ reports.length }}</span>
            </div>
            <button class="card-action" @click="navigateTo('/reports')">查看报告</button>
          </div>
        </div>
        
        <div class="dashboard-recent">
          <div class="recent-section">
            <h3>最近任务</h3>
            <div v-if="loading.tasks" class="loading">加载中...</div>
            <div v-else-if="tasks.length === 0" class="empty-message">暂无任务数据</div>
            <div v-else class="recent-list">
              <div 
                v-for="task in tasks.slice(0, 3)" 
                :key="task.id" 
                class="recent-item"
              >
                <div class="recent-item-name">{{ task.name }}</div>
                <div class="recent-item-info">
                  <span 
                    class="status-badge" 
                    :class="`status-${task.status}`"
                  >
                    {{ task.status_display }}
                  </span>
                  <span class="date">{{ formatDateTime(task.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="recent-section">
            <h3>最近报告</h3>
            <div v-if="loading.reports" class="loading">加载中...</div>
            <div v-else-if="reports.length === 0" class="empty-message">暂无报告数据</div>
            <div v-else class="recent-list">
              <div 
                v-for="report in reports.slice(0, 3)" 
                :key="report.id" 
                class="recent-item"
              >
                <div class="recent-item-name">{{ report.title }}</div>
                <div class="recent-item-info">
                  <span class="date">{{ formatDateTime(report.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.dashboard-header {
  background-color: #1890ff;
  padding: 16px 20px;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logout-button {
  background: transparent;
  border: 1px solid white;
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.logout-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.dashboard-content {
  display: flex;
  flex: 1;
  height: calc(100vh - 64px);
  overflow: hidden;
}

.dashboard-nav {
  width: 220px;
  background-color: #001529;
  padding: 20px 0;
}

.nav-item {
  padding: 16px 24px;
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
}

.nav-item:hover {
  color: white;
  background-color: #1890ff;
}

.nav-icon {
  font-size: 18px;
  margin-right: 12px;
}

.dashboard-main {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background-color: #f0f2f5;
}

.dashboard-overview {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background-color: white;
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.stat-card h3 {
  margin: 0 0 16px 0;
  color: #8c8c8c;
  font-size: 16px;
}

.stat-value {
  font-size: 30px;
  font-weight: bold;
  color: #1890ff;
  margin-bottom: 16px;
}

.card-action {
  background-color: transparent;
  color: #1890ff;
  border: 1px solid #1890ff;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.card-action:hover {
  background-color: #1890ff;
  color: white;
}

.dashboard-recent {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.recent-section {
  background-color: white;
  border-radius: 4px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.recent-section h3 {
  margin: 0 0 16px 0;
  color: #000000;
  font-size: 18px;
}

.loading, .empty-message {
  color: #bfbfbf;
  text-align: center;
  padding: 20px 0;
}

.recent-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-item {
  padding: 12px;
  border-radius: 4px;
  background-color: #f9f9f9;
  border-left: 3px solid #1890ff;
}

.recent-item-name {
  font-weight: bold;
  margin-bottom: 8px;
}

.recent-item-info {
  display: flex;
  justify-content: space-between;
  color: #8c8c8c;
  font-size: 12px;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.status-pending {
  background-color: #faad14;
  color: white;
}

.status-processing {
  background-color: #1890ff;
  color: white;
}

.status-completed {
  background-color: #52c41a;
  color: white;
}

.status-failed {
  background-color: #f5222d;
  color: white;
}

.date {
  color: #8c8c8c;
}
</style> 