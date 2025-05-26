import { defineStore } from 'pinia'
import axios from 'axios'
import { API_BASE_URL } from '../config'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
    loading: false,
    error: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    getUser: (state) => state.user
  },
  
  actions: {
    async login(credentials) {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.post(`${API_BASE_URL}/auth/login/`, credentials)
        const { token, user } = response.data
        
        this.token = token
        this.user = user
        
        // 清除旧的存储数据
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        
        // 存储新的数据
        localStorage.setItem('token', token)
        localStorage.setItem('user', JSON.stringify(user))
        
        // 配置axios的默认Authorization头，仅使用Bearer前缀
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        
        console.log('登录成功，已设置Authorization头:', `Bearer ${token}`)
        
        return true
      } catch (error) {
        console.error('登录失败:', error.response?.data || error.message)
        this.error = error.response?.data?.detail || '登录失败'
        return false
      } finally {
        this.loading = false
      }
    },
    
    logout() {
      this.token = null
      this.user = null
      
      // 清除存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // 移除axios的Authorization头
      delete axios.defaults.headers.common['Authorization']
      
      // 调用后端登出接口
      axios.post(`${API_BASE_URL}/auth/logout/`)
        .catch(error => console.error('登出时出错:', error))
    },
    
    // 新增：清理无效token
    clearInvalidToken() {
      this.token = null
      this.user = null
      
      // 清除存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // 移除axios的Authorization头
      delete axios.defaults.headers.common['Authorization']
      
      console.log('已清理可能无效的登录令牌')
    },
    
    // 新增：设置全局请求拦截器处理401错误
    setupAxiosInterceptors() {
      // 请求拦截器
      axios.interceptors.request.use(
        config => {
          const token = this.token
          if (token) {
            config.headers.Authorization = `Bearer ${token}`
          }
          return config
        },
        error => Promise.reject(error)
      )
      
      // 响应拦截器
      axios.interceptors.response.use(
        response => response,
        error => {
          // 捕获401未授权错误（令牌过期或无效）
          if (error.response && error.response.status === 401) {
            console.log('检测到无效令牌，正在清理...')
            this.clearInvalidToken()
          }
          return Promise.reject(error)
        }
      )
    }
  }
}) 