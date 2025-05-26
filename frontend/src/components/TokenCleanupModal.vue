<template>
  <el-dialog
    title="登录会话已过期"
    v-model="visible"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    width="30%"
  >
    <div class="token-cleanup-content">
      <el-alert
        title="检测到您的登录会话已过期"
        type="warning"
        description="服务器可能已重启，需要重新登录。"
        :closable="false"
        show-icon
      />
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button type="primary" @click="handleCleanupAndRedirect">
          重新登录
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const visible = ref(false)

// 检查是否需要显示清理提示
onMounted(() => {
  // 如果有token，进行测试请求确认其有效性
  if (authStore.isAuthenticated) {
    // 这里可以调用一个简单的API端点来验证token
    // 简化起见，这里直接显示模态框
    visible.value = true
  }
})

// 清理token并重定向到登录页
const handleCleanupAndRedirect = () => {
  // 清理token
  authStore.clearInvalidToken()
  
  // 关闭对话框
  visible.value = false
  
  // 重定向到登录页
  router.push('/login')
}
</script>

<style scoped>
.token-cleanup-content {
  margin: 20px 0;
}
</style> 