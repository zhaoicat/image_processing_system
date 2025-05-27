import { defineStore } from 'pinia'
import axios from 'axios'
import { API_BASE_URL } from '../config'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    refreshToken: localStorage.getItem('refreshToken') || null,
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
        const { access, refresh, user } = response.data
        
        this.token = access
        this.refreshToken = refresh
        this.user = user
        
        // 存储到localStorage
        localStorage.setItem('token', access)
        localStorage.setItem('refreshToken', refresh)
        localStorage.setItem('user', JSON.stringify(user))
        
        // 配置axios的默认Authorization头
        axios.defaults.headers.common['Authorization'] = `Bearer ${access}`
        
        console.log('登录成功，token已保存并设置为持久化')
        
        return true
      } catch (error) {
        console.error('登录失败:', error.response?.data || error.message)
        this.error = error.response?.data?.detail || '登录失败'
        return false
      } finally {
        this.loading = false
      }
    },
    
    async refreshAccessToken() {
      if (!this.refreshToken) {
        console.log('没有refresh token，无法刷新')
        return false
      }
      
      try {
        const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
          refresh: this.refreshToken
        })
        
        const { access, refresh } = response.data
        
        this.token = access
        if (refresh) {
          this.refreshToken = refresh
          localStorage.setItem('refreshToken', refresh)
        }
        
        localStorage.setItem('token', access)
        axios.defaults.headers.common['Authorization'] = `Bearer ${access}`
        
        console.log('Token刷新成功')
        return true
      } catch (error) {
        console.error('Token刷新失败:', error)
        this.logout()
        return false
      }
    },
    
    logout() {
      this.token = null
      this.refreshToken = null
      this.user = null
      
      // 清除存储
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
      
      // 移除axios的Authorization头
      delete axios.defaults.headers.common['Authorization']
      
      console.log('已登出并清理所有token')
    },
    
    // 设置全局请求拦截器处理401错误
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
        async error => {
          const originalRequest = error.config
          
          // 如果是401错误且还没有重试过
          if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true
            
            console.log('检测到401错误，尝试刷新token')
            
            // 尝试刷新token
            const refreshSuccess = await this.refreshAccessToken()
            
            if (refreshSuccess) {
              // 重新发送原始请求
              return axios(originalRequest)
            } else {
              // 刷新失败，跳转到登录页
              console.log('Token刷新失败，需要重新登录')
              // 这里可以触发路由跳转到登录页
              if (window.location.pathname !== '/login') {
                window.location.href = '/login'
              }
            }
          }
          
          return Promise.reject(error)
        }
      )
    }
  }
}) 