import axios from 'axios'
import { API_BASE_URL } from '../config'

const API_URL = API_BASE_URL

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器，为每个请求添加token
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      // 统一使用Bearer前缀，不使用JWT前缀
      config.headers['Authorization'] = `Bearer ${token}`
    }
    // 打印请求信息，方便调试
    const authHeader = config.headers['Authorization'] || '无认证头';
    console.log('API请求:', config.method.toUpperCase(), config.url);
    console.log('认证头:', authHeader);
    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器，处理错误和token过期
apiClient.interceptors.response.use(
  response => response,
  error => {
    // 输出具体的响应错误信息
    console.error('API响应错误:', error.message);
    console.error('状态码:', error.response?.status);
    console.error('响应数据:', error.response?.data);
    
    if (error.response) {
      if (error.response.status === 401) {
        console.warn('接收到401未授权响应，可能是token无效');
        // 如果是未授权，清除token并跳转到登录页
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      } else if (error.response.status === 429) {
        // 如果是请求过于频繁，显示特定错误信息
        console.error('请求过于频繁，请稍后重试')
        return Promise.reject({
          ...error,
          message: '请求过于频繁，请稍后重试',
          isRateLimited: true
        })
      }
    }
    return Promise.reject(error)
  }
)

export const authService = {
  login: (credentials) => apiClient.post('/auth/login/', credentials),
  logout: () => apiClient.post('/auth/logout/'),
  register: (userData) => apiClient.post('/auth/register/', userData)
}

export const imageService = {
  getAll: () => {
    console.log('获取图片列表');
    return apiClient.get('/images/').then(response => {
      console.log('获取图片列表响应:', response);
      return response;
    }).catch(error => {
      console.error('获取图片列表错误:', error);
      throw error;
    });
  },
  upload: (formData) => apiClient.post('/images/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  uploadMultiple: (formData) => apiClient.post('/images/upload_multiple/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }).then(response => {
    console.log('上传成功响应:', response);
    return response;
  }).catch(error => {
    console.error('上传错误:', error);
    console.error('上传错误详情:', error.response?.data || '无详细信息');
    console.error('请求配置:', error.config);
    throw error;
  }),
  delete: (id) => apiClient.delete(`/images/${id}/`)
}

export const taskService = {
  getAll: () => {
    console.log('【调试】获取所有任务');
    return apiClient.get('/tasks/').then(response => {
      console.log('【调试】获取任务响应:', response.data);
      return response;
    }).catch(error => {
      console.error('【调试】获取任务失败:', error);
      throw error;
    });
  },
  getById: (id) => {
    console.log(`【调试】获取任务详情, ID: ${id}`);
    return apiClient.get(`/tasks/${id}/`).then(response => {
      console.log('【调试】获取任务详情响应:', response.data);
      return response;
    }).catch(error => {
      console.error(`【调试】获取任务详情失败, ID: ${id}:`, error);
      throw error;
    });
  },
  getStatus: (id) => {
    // console.log(`【调试】获取任务状态, ID: ${id}`);
    return apiClient.get(`/tasks/${id}/status/`).then(response => {
      // console.log(`【调试】获取任务状态响应, ID: ${id}:`, response.data);
      return response;
    }).catch(error => {
      console.error(`【调试】获取任务状态失败, ID: ${id}:`, error);
      throw error;
    });
  },
  create: (taskData) => {
    console.log('【调试】创建任务，数据:', taskData);
    return apiClient.post('/tasks/', taskData).then(response => {
      console.log('【调试】创建任务响应:', response.data);
      return response;
    }).catch(error => {
      console.error('【调试】创建任务失败:', error);
      throw error;
    });
  },
  restart: (id, data = {}) => {
    console.log(`【调试】重启任务, ID: ${id}`, data ? `参数: ${JSON.stringify(data)}` : '');
    return apiClient.post(`/tasks/${id}/restart/`, data).then(response => {
      console.log(`【调试】重启任务响应, ID: ${id}:`, response.data);
      return response;
    }).catch(error => {
      console.error(`【调试】重启任务失败, ID: ${id}:`, error);
      console.error('【详细错误】:', error.response?.data || '无详细信息');
      throw error;
    });
  },
  delete: (id) => {
    console.log(`【调试】删除任务, ID: ${id}`);
    return apiClient.delete(`/tasks/${id}/`).then(response => {
      console.log(`【调试】删除任务响应, ID: ${id}:`, response.data);
      return response;
    }).catch(error => {
      console.error(`【调试】删除任务失败, ID: ${id}:`, error);
      throw error;
    });
  },
  getLogs: (id) => {
    console.log(`【调试】获取任务日志, ID: ${id}`);
    return apiClient.get(`/tasks/${id}/logs/`, { responseType: 'text' }).then(response => {
      console.log(`【调试】获取任务日志响应, ID: ${id}`);
      return response;
    }).catch(error => {
      console.error(`【调试】获取任务日志失败, ID: ${id}:`, error);
      throw error;
    });
  }
}

export const reportService = {
  getAll: () => apiClient.get('/reports/'),
  getById: (id) => apiClient.get(`/reports/${id}/`),
  getByTaskId: (taskId) => apiClient.get(`/reports/?task=${taskId}`),
  download: (id) => apiClient.get(`/reports/${id}/download/`, { responseType: 'blob' }),
  getTaskLog: (taskId) => apiClient.get(`/tasks/${taskId}/logs/`, { responseType: 'text' }),
  getOutputLog: (id) => apiClient.get(`/reports/${id}/output_log/`, { responseType: 'text' }),
  delete: (id) => apiClient.delete(`/reports/${id}/`),
  checkAllReports: () => apiClient.post('/tasks/check_reports/')
}

export default apiClient 