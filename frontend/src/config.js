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
    BACKEND_HOST: 'http://127.0.0.1:8888'
  },
  // 生产环境配置
  production: {
    API_BASE_URL: '/api',
    MEDIA_URL: '/media',
    BACKEND_HOST: import.meta.env.VITE_BACKEND_HOST || 'http://127.0.0.1:8888'
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

// 获取图片URL（增强调试版本）
export const getImageUrl = (filePath) => {
  console.log('🔍 getImageUrl 调试信息:')
  console.log('  输入路径:', filePath)
  console.log('  路径类型:', typeof filePath)
  console.log('  MEDIA_URL:', MEDIA_URL)
  
  if (!filePath) {
    console.log('  ❌ 文件路径为空')
    return ''
  }
  
  // 如果已经是完整的URL，直接返回
  if (filePath.startsWith('http')) {
    console.log('  ✅ 已是完整URL，直接返回')
    return filePath
  }
  
  // 如果已经包含/media/前缀，直接返回
  if (filePath.startsWith('/media/')) {
    console.log('  ✅ 已包含/media/前缀，直接返回')
    return filePath
  }
  
  // Django的ImageField返回的路径格式：images/YYYY/MM/DD/filename.ext
  try {
    // 分割路径和文件名
    const pathParts = filePath.split('/')
    const fileName = pathParts.pop() // 获取文件名
    const dirPath = pathParts.join('/') // 获取目录路径
    
    console.log('  📁 目录路径:', dirPath)
    console.log('  📄 文件名:', fileName)
    
    // 对文件名进行URL编码，但保留目录路径不变
    const encodedFileName = encodeURIComponent(fileName)
    console.log('  🔗 编码后文件名:', encodedFileName)
    
    const fullPath = dirPath ? `${dirPath}/${encodedFileName}` : encodedFileName
    const finalUrl = `${MEDIA_URL}/${fullPath}`
    
    console.log('  🎯 最终URL:', finalUrl)
    return finalUrl
  } catch (error) {
    console.error('  ❌ URL编码错误:', error)
    // 如果编码失败，回退到原始方法
    const fallbackUrl = `${MEDIA_URL}/${filePath}`
    console.log('  🔄 回退URL:', fallbackUrl)
    return fallbackUrl
  }
}

// 获取图片文件名（从完整路径中提取）
export const getImageFilename = (filePath) => {
  if (!filePath) return ''
  return filePath.split('/').pop()
}

// 处理图片加载错误（增强调试版本）
const handleImageError = (event) => {
  const originalSrc = event.target.src
  console.log('🚨 图片加载失败详细信息:')
  console.log('  失败的URL:', originalSrc)
  console.log('  图片元素:', event.target)
  
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
    })
  
  console.log('  🔄 使用默认占位图片')
  event.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iI2VlZWVlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNHB4IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSIgZmlsbD0iIzk5OTk5OSI+图片加载失败</dGV4dD48L3N2Zz4='
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