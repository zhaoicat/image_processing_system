<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { imageService } from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getImageUrl, getBackendUrl } from '../config'

const router = useRouter()
const authStore = useAuthStore()

const images = ref([])
const loading = ref(false)
const uploadFiles = ref([])
const showUploadDialog = ref(false)
const uploadLoading = ref(false)
// 分页参数
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 批量删除相关状态
const selectedImages = ref([])
const isDeleteLoading = ref(false)

onMounted(async () => {
  console.log('组件挂载，首次获取图片')
  await fetchImages()
})

const fetchImages = async () => {
  loading.value = true
  try {
    console.log('开始获取图片列表...')
    const response = await imageService.getAll()
    console.log('获取图片列表成功，数据:', response.data)
    
    // 处理所有图片数据，去除哈希值重复的图片
    const allImageData = response.data
    const hashMap = new Map()
    const uniqueImages = []
    
    // 对图片进行去重，对于每个哈希值只保留第一个图片
    allImageData.forEach(image => {
      // 如果图片没有哈希值或者该哈希值还没有被处理过，则保留
      if (!image.image_hash || !hashMap.has(image.image_hash)) {
        if (image.image_hash) {
          hashMap.set(image.image_hash, true)
        }
        uniqueImages.push(image)
      }
    })
    
    console.log(`图片总数: ${allImageData.length}, 去重后: ${uniqueImages.length}`)
    
    // 设置总数为去重后的图片数量
    total.value = uniqueImages.length
    
    // 在前端进行分页
    const startIndex = (currentPage.value - 1) * pageSize.value
    const endIndex = startIndex + pageSize.value
    images.value = uniqueImages.slice(startIndex, endIndex)
  } catch (error) {
    console.error('获取图片失败:', error)
    ElMessage.error('获取图片数据失败')
  } finally {
    loading.value = false
  }
}

// 切换页码时执行
const handlePageChange = (page) => {
  currentPage.value = page
  fetchImages()
}

const handleFileChange = (event) => {
  uploadFiles.value = Array.from(event.target.files)
}

const uploadImages = async () => {
  if (uploadFiles.value.length === 0) {
    ElMessage.warning('请选择要上传的图片')
    return
  }
  
  uploadLoading.value = true
  console.log('开始上传图片，文件数量:', uploadFiles.value.length)
  
  const formData = new FormData()
  uploadFiles.value.forEach(file => {
    console.log('添加文件到formData:', file.name, '类型:', file.type, '大小:', file.size)
    formData.append('files', file)
  })
  
  try {
    console.log('发送上传请求...')
    const response = await imageService.uploadMultiple(formData)
    console.log('上传成功，响应:', response)
    ElMessage.success('图片上传成功')
    showUploadDialog.value = false
    uploadFiles.value = []
    
    console.log('上传完成，准备刷新图片列表')
    // 延迟三秒后刷新，确保后端处理完成
    setTimeout(async () => {
      console.log('开始延迟刷新图片列表')
      await fetchImages()
    }, 3000)
  } catch (error) {
    console.error('上传图片失败:', error)
    ElMessage.error(`上传图片失败: ${error.message || '未知错误'}`)
  } finally {
    uploadLoading.value = false
  }
}

// 单个图片删除
const deleteImage = async (imageId) => {
  try {
    await ElMessageBox.confirm('确定要删除这张图片吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await imageService.delete(imageId)
    ElMessage.success('图片删除成功')
    // 从选择列表中移除已删除的图片
    selectedImages.value = selectedImages.value.filter(id => id !== imageId)
    await fetchImages()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除图片失败:', error)
      ElMessage.error('删除图片失败')
    }
  }
}

// 批量删除选中的图片
const deleteSelectedImages = async () => {
  if (selectedImages.value.length === 0) {
    ElMessage.warning('请选择要删除的图片')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedImages.value.length} 张图片吗？`, 
      '批量删除', 
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    isDeleteLoading.value = true
    const deletePromises = selectedImages.value.map(id => imageService.delete(id))
    
    try {
      await Promise.all(deletePromises)
      ElMessage.success(`成功删除 ${selectedImages.value.length} 张图片`)
      selectedImages.value = [] // 清空选择
      await fetchImages()
    } catch (error) {
      console.error('批量删除图片失败:', error)
      ElMessage.error('部分图片删除失败，请刷新页面重试')
    } finally {
      isDeleteLoading.value = false
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('确认删除对话框错误:', error)
    }
  }
}

// 选择/取消选择单张图片
const toggleSelectImage = (imageId) => {
  const index = selectedImages.value.indexOf(imageId)
  if (index === -1) {
    selectedImages.value.push(imageId)
  } else {
    selectedImages.value.splice(index, 1)
  }
}

// 检查图片是否被选中
const isImageSelected = (imageId) => {
  return selectedImages.value.includes(imageId)
}

// 全选/取消全选当前页的图片
const toggleSelectAll = () => {
  if (selectedImages.value.length === images.value.length) {
    // 如果当前页全部已选中，则取消全选
    selectedImages.value = []
  } else {
    // 否则全选当前页
    selectedImages.value = images.value.map(image => image.id)
  }
}

// 检查当前页是否全部选中
const isAllSelected = () => {
  return images.value.length > 0 && selectedImages.value.length === images.value.length
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const navigateTo = (path) => {
  router.push(path)
}

// 处理图片加载错误（增强调试版本）
const handleImageError = (event) => {
  const originalSrc = event.target.src
  console.log('🚨 图片加载失败详细信息:')
  console.log('  失败的URL:', originalSrc)
  console.log('  图片元素:', event.target)
  
  // 检查是否是跨域问题
  if (originalSrc.startsWith('http://127.0.0.1:8888') || originalSrc.startsWith('http://localhost:8888')) {
    console.log('  ⚠️  检测到跨域请求！应该使用相对路径')
    console.log('  🔧 尝试转换为相对路径')
    
    try {
      const url = new URL(originalSrc)
      const relativePath = url.pathname
      console.log('  🔄 转换后的相对路径:', relativePath)
      
      // 尝试使用相对路径重新加载
      event.target.src = relativePath
      return // 不设置默认图片，让它重新尝试加载
    } catch (error) {
      console.error('  ❌ URL转换失败:', error)
    }
  }
  
  // 尝试直接访问图片URL进行调试
  fetch(originalSrc)
    .then(response => {
      console.log('  📡 HTTP响应状态:', response.status)
      console.log('  📡 HTTP响应文本:', response.statusText)
      if (!response.ok) {
        if (response.status === 404) {
          console.log('  ❌ 图片文件不存在或路径错误 (404)')
        } else if (response.status === 403) {
          console.log('  ❌ 图片访问被拒绝，权限问题 (403)')
        } else if (response.status === 500) {
          console.log('  ❌ 服务器内部错误 (500)')
        } else {
          console.log('  ❌ 其他HTTP错误:', response.status)
        }
      }
    })
    .catch(error => {
      console.log('  🌐 网络请求错误:', error.message)
      console.log('  🌐 错误类型:', error.name)
      if (error.message.includes('CORS')) {
        console.log('  🚫 确认是CORS跨域问题')
      }
    })
  
  console.log('  🔄 使用默认占位图片')
  event.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI2VlZWVlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNHB4IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSIgZmlsbD0iIzk5OTk5OSI+图片加载失败</dGV4dD48L3N2Zz4='
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
        <div class="nav-item active" @click="navigateTo('/images')">
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
        <div class="page-header">
          <h2>图片管理</h2>
          <div class="header-actions">
            <button 
              v-if="selectedImages.length > 0" 
              class="delete-selected-button" 
              @click="deleteSelectedImages"
              :disabled="isDeleteLoading"
            >
              {{ isDeleteLoading ? '删除中...' : `删除选中(${selectedImages.length})` }}
            </button>
            <button class="upload-button" @click="showUploadDialog = true">上传图片</button>
          </div>
        </div>
        
        <div v-if="loading" class="loading-container">
          <div class="loading-text">加载中...</div>
        </div>
        
        <div v-else-if="images.length === 0" class="empty-message">
          暂无图片，请上传一些图片
        </div>
        
        <div v-else>
          <div class="batch-actions">
            <label class="select-all-container">
              <input 
                type="checkbox" 
                :checked="isAllSelected()" 
                @change="toggleSelectAll"
              />
              <span class="select-all-label">{{ isAllSelected() ? '取消全选' : '全选' }}</span>
            </label>
          </div>
          
          <div class="image-grid">
            <div v-for="image in images" :key="image.id" class="image-card" :class="{'selected': isImageSelected(image.id)}">
              <div class="selection-overlay" @click="toggleSelectImage(image.id)">
                <div class="checkbox-container">
                  <input 
                    type="checkbox" 
                    :checked="isImageSelected(image.id)" 
                    @change="toggleSelectImage(image.id)"
                    @click.stop
                  />
                </div>
              </div>
              <div class="image-card-header">
                <div class="image-title-container">
                  <div class="image-title" :title="image.title">{{ image.title }}</div>
                  <span v-if="image.is_duplicate" class="duplicate-tag">重复</span>
                </div>
                <div class="image-actions">
                  <button class="action-button delete-button" @click="deleteImage(image.id)" title="删除图片">
                    <span class="action-icon">🗑️</span>
                  </button>
                </div>
              </div>
              <div class="image-thumbnail">
                <img :src="getImageUrl(image.file)" :alt="image.title" @error="handleImageError">
              </div>
              <div class="image-details">
                <div class="image-meta">
                  <div class="meta-item">
                    <span class="meta-label">上传时间:</span>
                    <span class="meta-value">{{ new Date(image.uploaded_at).toLocaleString() }}</span>
                  </div>
                  <div class="meta-item" v-if="image.image_hash">
                    <span class="meta-label">哈希值:</span>
                    <span class="meta-value hash-value">{{ image.image_hash.substring(0, 8) }}...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="pagination-container" v-if="total > pageSize">
          <div class="pagination">
            <button 
              class="pagination-button" 
              :disabled="currentPage === 1" 
              @click="handlePageChange(currentPage - 1)"
            >
              上一页
            </button>
            <span class="page-info">{{ currentPage }} / {{ Math.ceil(total / pageSize) }}</span>
            <button 
              class="pagination-button" 
              :disabled="currentPage >= Math.ceil(total / pageSize)" 
              @click="handlePageChange(currentPage + 1)"
            >
              下一页
            </button>
          </div>
        </div>
        
        <div v-if="showUploadDialog" class="upload-dialog-overlay">
          <div class="upload-dialog">
            <div class="dialog-header">
              <h3>上传图片</h3>
              <button class="close-button" @click="showUploadDialog = false" :disabled="uploadLoading">×</button>
            </div>
            <div class="dialog-body">
              <div class="file-input-container">
                <input type="file" id="file-input" multiple accept="image/*" @change="handleFileChange">
                <label for="file-input" class="file-input-label">
                  选择图片文件
                </label>
                <div v-if="uploadFiles.length > 0" class="selected-files">
                  已选择 {{ uploadFiles.length }} 个文件:
                  <ul class="file-list">
                    <li v-for="(file, index) in uploadFiles" :key="index">
                      {{ file.name }} ({{ (file.size / 1024).toFixed(2) }} KB)
                    </li>
                  </ul>
                </div>
              </div>
            </div>
            <div class="dialog-footer">
              <button class="cancel-button" @click="showUploadDialog = false" :disabled="uploadLoading">取消</button>
              <button class="confirm-button" @click="uploadImages" :disabled="uploadLoading">
                {{ uploadLoading ? '上传中...' : '上传' }}
              </button>
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

.nav-item:hover, .nav-item.active {
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

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #000000;
}

.upload-button {
  background-color: #1890ff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.upload-button:hover {
  background-color: #40a9ff;
}

.loading-container, .empty-message {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
  color: #8c8c8c;
  font-size: 18px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

/* 图片网格布局 */
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.image-card {
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s, box-shadow 0.3s, border 0.2s;
  display: flex;
  flex-direction: column;
  position: relative;
  border: 2px solid transparent;
}

.image-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
}

.image-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background-color: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.image-title-container {
  display: flex;
  align-items: center;
  max-width: 80%;
}

.image-title {
  font-weight: bold;
  font-size: 16px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #333;
}

.image-actions {
  display: flex;
  gap: 8px;
}

.action-button {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.delete-button {
  color: #ff4d4f;
}

.delete-button:hover {
  background-color: rgba(255, 77, 79, 0.1);
}

.action-icon {
  font-size: 18px;
}

.image-thumbnail {
  width: 100%;
  height: 200px;
  overflow: hidden;
  position: relative;
}

.image-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s;
}

.image-card:hover .image-thumbnail img {
  transform: scale(1.05);
}

.image-details {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.image-meta {
  color: #8c8c8c;
  font-size: 14px;
}

.meta-item {
  margin-bottom: 8px;
  display: flex;
  flex-wrap: wrap;
}

.meta-label {
  font-weight: 500;
  margin-right: 6px;
  color: #666;
}

.meta-value {
  color: #333;
}

.hash-value {
  font-weight: 500;
  color: #1890ff;
}

.duplicate-tag {
  background-color: #ff4d4f;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  margin-left: 8px;
}

/* 分页样式 */
.pagination-container {
  margin-top: 24px;
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 16px;
  background-color: white;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
}

.pagination-button {
  background-color: #1890ff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
  font-weight: 500;
}

.pagination-button:hover:not(:disabled) {
  background-color: #40a9ff;
}

.pagination-button:disabled {
  background-color: #bfbfbf;
  cursor: not-allowed;
}

.page-info {
  font-size: 16px;
  color: #333;
  font-weight: 500;
}

/* 批量操作样式 */
.header-actions {
  display: flex;
  gap: 12px;
}

.delete-selected-button {
  background-color: #ff4d4f;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  font-weight: 500;
}

.delete-selected-button:hover:not(:disabled) {
  background-color: #ff7875;
}

.delete-selected-button:disabled {
  background-color: #ffcccb;
  cursor: not-allowed;
}

.batch-actions {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.select-all-container {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  background-color: white;
  padding: 8px 16px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.select-all-label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.selection-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  background-color: rgba(0, 0, 0, 0.02);
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
}

.image-card:hover .selection-overlay,
.image-card.selected .selection-overlay {
  opacity: 1;
}

.checkbox-container {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 2;
  height: 22px;
  width: 22px;
}

.checkbox-container input[type="checkbox"] {
  height: 20px;
  width: 20px;
  cursor: pointer;
}

.image-card.selected {
  border: 2px solid #1890ff;
  box-shadow: 0 3px 16px rgba(24, 144, 255, 0.2);
}

.upload-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.upload-dialog {
  background-color: white;
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dialog-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-button {
  background: transparent;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #8c8c8c;
}

.dialog-body {
  padding: 24px;
}

.file-input-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

#file-input {
  display: none;
}

.file-input-label {
  padding: 32px;
  border: 2px dashed #d9d9d9;
  border-radius: 4px;
  text-align: center;
  cursor: pointer;
  width: 100%;
  transition: border-color 0.3s;
}

.file-input-label:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.selected-files {
  margin-top: 16px;
  color: #1890ff;
}

.file-list {
  margin-top: 8px;
  padding-left: 20px;
  list-style-type: disc;
  color: #333;
  text-align: left;
}

.file-list li {
  margin-bottom: 4px;
}

.dialog-footer {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-button, .confirm-button {
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.cancel-button {
  background-color: white;
  border: 1px solid #d9d9d9;
  color: rgba(0, 0, 0, 0.65);
}

.cancel-button:hover {
  border-color: #40a9ff;
  color: #40a9ff;
}

.confirm-button {
  background-color: #1890ff;
  border: 1px solid #1890ff;
  color: white;
}

.confirm-button:hover {
  background-color: #40a9ff;
  border-color: #40a9ff;
}

.confirm-button:disabled, .cancel-button:disabled {
  background-color: #d9d9d9;
  border-color: #d9d9d9;
  color: rgba(0, 0, 0, 0.25);
  cursor: not-allowed;
}
</style> 