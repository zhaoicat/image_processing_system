/**
 * 全局配置文件
 * 包含后端API地址和其他环境相关配置
 */

// 判断是否为开发环境
const isDevelopment = import.meta.env.DEV

// 环境配置
const config = {
  // 开发环境配置
  development: {
    API_BASE_URL: '/api',
    MEDIA_URL: '/media',
    BACKEND_HOST: 'http://localhost:8888'
  },
  // 生产环境配置
  production: {
    API_BASE_URL: '/api',
    MEDIA_URL: '/media',
    BACKEND_HOST: import.meta.env.VITE_BACKEND_HOST || 'http://localhost:8888'
  }
}

// 获取当前环境配置
const currentConfig = isDevelopment ? config.development : config.production

// 后端API基础URL
export const API_BASE_URL = currentConfig.API_BASE_URL

// 媒体文件URL
export const MEDIA_URL = currentConfig.MEDIA_URL

// 后端主机地址（用于直接访问，如登录等）
export const BACKEND_HOST = currentConfig.BACKEND_HOST

// 报告文件URL
export const REPORTS_URL = `${MEDIA_URL}/reports`

// 获取完整的API URL
export const getApiUrl = (path) => {
  return `${API_BASE_URL}${path}`
}

// 获取后端完整URL（用于直接访问）
export const getBackendUrl = (path) => {
  return `${BACKEND_HOST}${path}`
}

// 获取媒体文件URL
export const getMediaUrl = (path) => {
  return `${MEDIA_URL}/${path}`
}

// 获取报告URL
export const getReportUrl = (taskId, imgIndex, filename) => {
  return `${REPORTS_URL}/task_${taskId}/img_${imgIndex}/task_${taskId}_img_${imgIndex}/${filename}`
}

// 获取图片URL（修复版本 - 正确处理Django文件路径）
export const getImageUrl = (filePath) => {
  if (!filePath) {
    return ''
  }
  
  // 如果已经是完整的URL，直接返回
  if (filePath.startsWith('http')) {
    return filePath
  }
  
  // 如果已经包含/media/前缀，直接返回
  if (filePath.startsWith('/media/')) {
    return filePath
  }
  
  // Django的ImageField返回的路径格式：images/YYYY/MM/DD/filename.ext
  // 我们需要在前面添加/media/前缀
  return `${MEDIA_URL}/${filePath}`
}

// 获取图片文件名（从完整路径中提取）
export const getImageFilename = (filePath) => {
  if (!filePath) return ''
  return filePath.split('/').pop()
}

export default {
  API_BASE_URL,
  MEDIA_URL,
  BACKEND_HOST,
  REPORTS_URL,
  getApiUrl,
  getBackendUrl,
  getMediaUrl,
  getReportUrl,
  getImageUrl,
  getImageFilename
} 