<script setup>
import { ref, onMounted, computed, reactive, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { taskService, imageService } from '../services/api'
import apiClient from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getImageUrl, getBackendUrl } from '../config'

const router = useRouter()
const authStore = useAuthStore()

const tasks = ref([])
const images = ref([])
const loading = ref(false)
const createDialogVisible = ref(false)
const expandedTaskIds = ref(new Set())  // 存储已展开的任务ID
const submittingTaskIds = ref(new Set())  // 存储正在提交的任务ID
const refreshInterval = ref(null) // 用于自动刷新的计时器
const processingTasks = ref(new Set()) // 存储正在处理中的任务ID

// 添加搜索参数
const searchParams = reactive({
  taskId: '',
  taskName: '',
  algorithmName: ''
})

// 自动刷新处理中任务的状态
const autoRefreshTaskStatus = async () => {
  try {
    // 检查是否有处理中的任务
    if (processingTasks.value.size === 0) {
      return
    }
    
    // 只刷新正在处理中的任务
    const processingTasksArray = Array.from(processingTasks.value)
    for (const taskId of processingTasksArray) {
      try {
        // 使用新的status API端点获取最新状态
        const response = await taskService.getStatus(taskId)
        
        // 更新任务状态
        const taskIndex = tasks.value.findIndex(t => t.id === taskId)
        if (taskIndex !== -1) {
          // 更新任务状态和进度
          tasks.value[taskIndex].status = response.data.status
          tasks.value[taskIndex].progress = response.data.progress
          
          // 如果任务已完成或失败，从监控列表中移除
          if (response.data.status === 'completed' || response.data.status === 'failed') {
            processingTasks.value.delete(taskId)
            
            // 显示任务完成通知
            if (response.data.status === 'completed') {
              ElMessage.success(`任务 #${taskId} 已完成`)
            } else {
              ElMessage.error(`任务 #${taskId} 处理失败: ${response.data.failure_reason || '未知错误'}`)
            }
          }
        }
      } catch (error) {
        console.error(`获取任务 ${taskId} 状态失败:`, error)
      }
    }
  } catch (error) {
    console.error('自动刷新任务状态失败:', error)
  }
}

// 在组件挂载时启动自动刷新
onMounted(async () => {
  await fetchData()
  
  // 每3秒刷新一次正在处理的任务状态
  refreshInterval.value = setInterval(autoRefreshTaskStatus, 3000)
})

// 在组件销毁前清除定时器
onBeforeUnmount(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
})

// 监视任务数据变化，识别处理中的任务
watch(tasks, (newTasks) => {
  // 清空当前监控的任务集合
  processingTasks.value.clear()
  
  // 将所有处理中或待处理的任务添加到监控列表
  newTasks.forEach(task => {
    if (task.status === 'processing' || task.status === 'pending') {
      processingTasks.value.add(task.id)
    }
  })
}, { deep: true, immediate: true })

// 添加即时搜索
const activeSearch = ref(false)
const debounceSearch = () => {
  activeSearch.value = true
  // 显示搜索正在生效
  if (searchParams.taskId || searchParams.taskName || searchParams.algorithmName) {
    console.log('搜索条件已更新，正在过滤结果')
  }
}

// 重置搜索
const resetSearch = () => {
  searchParams.taskId = ''
  searchParams.taskName = ''
  searchParams.algorithmName = ''
  
  // 重置后通知搜索状态已更新
  debounceSearch()
  ElMessage.success('已重置搜索条件')
}

// 根据搜索条件过滤任务数据
const filteredTasks = computed(() => {
  if (!searchParams.taskId && !searchParams.taskName && !searchParams.algorithmName) {
    return tasks.value
  }
  
  return tasks.value.filter(task => {
    let matches = true
    if (searchParams.taskId && !String(task.id).includes(searchParams.taskId)) {
      matches = false
    }
    if (searchParams.taskName && !(task.name || '').toLowerCase().includes(searchParams.taskName.toLowerCase())) {
      matches = false
    }
    if (searchParams.algorithmName) {
      // 获取任务所有算法名称
      const algorithmNames = getAlgorithmNames(task);
      // 检查是否有算法名称包含搜索关键词
      const hasMatchingAlgorithm = algorithmNames.some(name => 
        name.toLowerCase().includes(searchParams.algorithmName.toLowerCase())
      );
      if (!hasMatchingAlgorithm) {
        matches = false
      }
    }
    return matches
  })
})

const newTask = ref({
  name: '',
  algorithm: ['algorithm1'],
  images: []
})

// 算法名称映射
const algorithmDisplayNames = {
  'algorithm1': '图像准确度AI检测（ImageHash算法）',
  'algorithm2': '图像质量AI检测（Opencv算法1）',
  'algorithm3': '图像纹理质量AI检测（Opencv算法2）',
  'algorithm4': '清晰度AI检测（Opencv+ScikitImage算法3）',
  'algorithm5': '整体图像质量AI检测'
}

// 生成任务名称
const generateTaskName = () => {
  const now = new Date()
  const dateStr = `${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}`
  const timeStr = `${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}`
  // 获取所有选中算法的名称
  const selectedAlgorithms = newTask.value.algorithm.map(algo => algorithmDisplayNames[algo]).join('+')
  return `${selectedAlgorithms}任务-${dateStr}${timeStr}`
}
const createLoading = ref(false)

// 网络连接检测功能
const checkBackendConnection = async () => {
  try {
    console.log('检测后端连接状态...')
    const response = await apiClient.get('/tasks/', { timeout: 5000 })
    console.log('后端连接正常:', response.status)
    return true
  } catch (error) {
    console.error('后端连接检测失败:', error)
    if (error.code === 'ECONNREFUSED' || error.message.includes('ECONNREFUSED')) {
      ElMessage.error({
        message: '无法连接到后端服务器，请确认服务器已启动',
        duration: 8000,
        showClose: true
      })
    } else if (error.code === 'TIMEOUT' || error.message.includes('timeout')) {
      ElMessage.error({
        message: '连接后端服务器超时，请检查网络状态',
        duration: 8000,
        showClose: true
      })
    } else {
      ElMessage.error({
        message: `后端连接异常: ${error.message}`,
        duration: 8000,
        showClose: true
      })
    }
    return false
  }
}

onMounted(async () => {
  await fetchData()
})

const fetchData = async () => {
  loading.value = true
  try {
    const [tasksResponse, imagesResponse] = await Promise.all([
      taskService.getAll(),
      imageService.getAll()
    ])
    tasks.value = tasksResponse.data
    images.value = imagesResponse.data
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const createTask = async () => {
  if (!newTask.value.name) {
    ElMessage.warning('请输入任务名称')
    return
  }
  
  if (newTask.value.images.length === 0) {
    ElMessage.warning('请选择至少一张图片')
    return
  }
  
  if (newTask.value.algorithm.length === 0) {
    ElMessage.warning('请选择至少一种处理算法')
    return
  }
  
  createLoading.value = true
  
  try {
    // 首先检测后端连接
    const connectionOk = await checkBackendConnection()
    if (!connectionOk) {
      ElMessage.error('后端连接失败，无法创建任务')
      return
    }
  
    // 添加超时控制
    const timeout = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('请求超时，请检查网络连接')), 30000) // 30秒超时
    })
    
    // 将算法ID数组转换为带注释的单个算法ID
    // 当前选择的算法数字组合（如"12"代表算法1和2）
    const selectedAlgorithms = newTask.value.algorithm.map(algo => algo.replace('algorithm', '')).join('')
    
    // 创建任务数据 - 简化版
    const taskData = {
      name: newTask.value.name,
      // 保持原有的algorithm字段格式，只传第一个算法ID作为主算法
      algorithm: newTask.value.algorithm[0],
      // 简化描述，不再包含算法信息
      description: `${newTask.value.name}处理任务`,
      // 算法数组字段，直接保存所有选择的算法ID
      algorithms: newTask.value.algorithm.map(algo => algo.replace('algorithm', '')),
      images: newTask.value.images
    }
    
    console.log('发送创建任务请求:', taskData)
    
    // 显示正在创建的提示
    ElMessage.info({
      message: '正在创建任务，请稍候...',
      duration: 2000
    })
    
    // 使用Promise.race来实现超时控制
    await Promise.race([
      taskService.create(taskData),
      timeout
    ])
    
    ElMessage.success('任务创建成功')
    createDialogVisible.value = false
    resetNewTask()
    
    // 延迟一下再刷新数据，确保后端已经处理完成
    setTimeout(async () => {
      await fetchData()
    }, 500)
    
  } catch (error) {
    console.error('创建任务失败:', error)
    
    // 更详细的错误处理
    if (error.message === '请求超时，请检查网络连接') {
      ElMessage.error({
        message: '创建任务超时，请检查网络连接后重试',
        duration: 5000,
        showClose: true
      })
    } else if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
      ElMessage.error({
        message: '网络连接失败，请检查网络状态',
        duration: 5000,
        showClose: true
      })
    } else if (error.response) {
      // 服务器响应了错误
      const status = error.response.status
      const data = error.response.data
      
      if (status === 401) {
        ElMessage.error('认证失败，请重新登录')
        authStore.logout()
        router.push('/login')
      } else if (status === 403) {
        ElMessage.error('权限不足，无法创建任务')
      } else if (status === 500) {
        ElMessage.error({
          message: '服务器内部错误，请联系管理员',
          duration: 5000,
          showClose: true
        })
      } else {
        ElMessage.error({
          message: `创建任务失败 (${status}): ${JSON.stringify(data)}`,
          duration: 5000,
          showClose: true
        })
      }
    } else {
      // 其他未知错误
      ElMessage.error({
        message: `创建任务失败: ${error.message || '未知错误'}`,
        duration: 5000,
        showClose: true
      })
    }
  } finally {
    createLoading.value = false
  }
}

const restartTask = async (taskId) => {
  try {
    // 检查任务是否正在提交中
    if (submittingTaskIds.value.has(taskId)) {
      ElMessage.warning('任务正在提交中，请勿重复操作');
      return;
    }
    
    // 使用辅助函数检查任务状态
    if (!checkTaskStatus(taskId, ['failed', 'pending', 'processing'])) {
      const task = tasks.value.find(t => t.id === taskId);
      ElMessage.warning(`${task?.status_display || '当前'}状态的任务无法重新启动`);
      return;
    }
    
    await ElMessageBox.confirm('确定要重新启动此任务吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 添加到提交中的任务集合
    submittingTaskIds.value.add(taskId);
    
    // 显示正在处理的状态提示
    const taskIndex = tasks.value.findIndex(t => t.id === taskId);
    if (taskIndex !== -1) {
      tasks.value[taskIndex].statusMessage = '正在重启...'; 
    }
    
    try {
      await taskService.restart(taskId);
      ElMessage.success('任务已重新启动');
      await fetchData();
    } catch (apiError) {
      // 检查是否为重复提交错误
      if (apiError.isRateLimited || apiError.response?.status === 429) {
        ElMessage.warning('任务正在处理中，请勿重复提交');
      } else {
        console.error('重启任务失败:', apiError);
        console.error('错误详情:', apiError.response?.data);
        ElMessage.error(`重启任务失败: ${apiError.message || '未知错误'}`);
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重启任务失败:', error);
      ElMessage.error('重启任务失败');
    }
  } finally {
    // 从提交中的任务集合移除
    submittingTaskIds.value.delete(taskId);
  }
}

// 从任务获取选择的算法
const getSelectedAlgorithmsFromTask = (task) => {
   console.log('获取选择的算法:', task);
    // 检查算法数组是否存在
    if (task.algorithms && Array.isArray(task.algorithms) && task.algorithms.length > 0) {
        // 从数组中获取算法编号并返回字符串
        return task.algorithms.map(algo => String(algo)).join('');
    }
    return '';

}

// 获取任务的所有算法名称数组
const getAlgorithmNames = (task) => {
  const algorithmIds = getSelectedAlgorithmsFromTask(task).split('');
  return algorithmIds.map(id => algorithmDisplayNames[`algorithm${id}`] || `未知算法(${id})`);
}

// 获取短算法名称（用于标签显示，避免过长）
const getShortAlgorithmName = (fullName) => {
  // 提取算法名称中的关键部分
  const matches = fullName.match(/（(.+?)）/);
  if (matches && matches[1]) {
    return matches[1];
  }
  // 如果没有括号，截取前10个字符
  return fullName.length > 10 ? fullName.substring(0, 10) + '...' : fullName;
}

// 获取算法标签颜色
const getAlgorithmColor = (algorithmId) => {
  // 根据算法ID返回不同的颜色
  const colors = {
    '1': '#4caf50', // 图像准确度AI检测 - 绿色
    '2': '#2196f3', // 图像质量AI检测 - 蓝色
    '3': '#ff9800', // 图像纹理质量AI检测 - 橙色
    '4': '#9c27b0', // 清晰度AI检测 - 紫色
    '5': '#f44336'  // 整体图像质量AI检测 - 红色
  };
  
  // 从算法名提取ID
  const id = algorithmId.match(/algorithm(\d+)/)?.[1] || 
             algorithmId.match(/(\d+)/)?.[1];
             
  return colors[id] || '#757575'; // 默认灰色
}

// 添加运行任务方法
const runTask = async (taskId) => {
  console.log(`【调试】开始运行任务 ID: ${taskId}`);
  
  // 检查任务是否正在提交中
  if (submittingTaskIds.value.has(taskId)) {
    ElMessage.warning('任务正在提交中，请勿重复操作');
    return;
  }
  
  // 使用辅助函数检查任务状态
  if (!checkTaskStatus(taskId, ['pending'])) {
    const task = tasks.value.find(t => t.id === taskId);
    ElMessage.warning(`${task?.status_display || '当前'}状态的任务无法启动`);
    return;
  }
  
  // 添加到提交中的任务集合
  submittingTaskIds.value.add(taskId);
  
  // 先本地更新状态，提供更好的用户体验
  const taskIndex = tasks.value.findIndex(t => t.id === taskId);
  if (taskIndex !== -1) {
    tasks.value[taskIndex].statusMessage = '正在启动...'; 
  }
  
  try {
    // 获取当前任务对象
    const task = tasks.value.find(t => t.id === taskId);
    
    // 获取选择的算法列表
    const selectedAlgorithms = getSelectedAlgorithmsFromTask(task);
    console.log(`【调试】运行任务选择的算法: ${selectedAlgorithms}`);
    
    // 更详细记录API请求前的状态
    console.log(`【调试】运行前任务状态:`, task);
    
    console.log(`【调试】发送API请求运行任务 ID: ${taskId}，使用算法: ${selectedAlgorithms}`);
    
    // 使用try-catch明确捕获网络错误
    try {
      ElMessage.info('正在向后端提交任务...');
      
      // 添加算法选择参数
      const response = await taskService.restart(taskId, { 
        algorithm_choice: selectedAlgorithms 
      });
      
      console.log(`【调试】任务API响应:`, response);
      
      ElMessage.success('任务已成功提交到处理队列');
      await fetchData();
      console.log(`【调试】重新获取任务数据完成`);
      
      // 查找当前任务
      const currentTask = tasks.value.find(t => t.id === taskId);
      console.log(`【调试】当前任务状态:`, currentTask?.status);
      
      if (currentTask?.status === 'pending') {
        ElMessage.info({
          message: '任务已提交，正在排队处理，请稍候...（如长时间无响应请联系管理员）',
          duration: 5000
        });
        // 5秒后再次检查状态
        setTimeout(async () => {
          await fetchData();
        }, 5000);
      }
      
    } catch (networkError) {
      console.error('【调试】网络请求失败:', networkError);
      console.error('【调试】请求状态:', networkError.response?.status);
      console.error('【调试】请求详情:', networkError.response?.data);
      
      // 检查是否为重复提交错误
      if (networkError.isRateLimited || networkError.response?.status === 429) {
        ElMessage.warning({
          message: '任务正在处理中，请勿重复提交',
          duration: 3000
        });
      } else {
        ElMessage.error({
          message: `API请求失败: ${networkError.message || '未知错误'}`, 
          duration: 0,
          showClose: true
        });
      }
      return;
    }
    
    // 设置定时刷新，以获取最新进度
    console.log(`【调试】开始设置定时刷新进度`);
    const refreshInterval = setInterval(async () => {
      console.log(`【调试】定时刷新进度...`);
      await fetchData();
      
      // 检查任务是否已完成或失败，如果是，则停止刷新
      const task = tasks.value.find(t => t.id === taskId);
      console.log(`【调试】刷新后任务状态:`, task?.status, `进度:`, task?.progress);
      
      if (task && (task.status === 'completed' || task.status === 'failed')) {
        console.log(`【调试】任务${task.status === 'completed' ? '已完成' : '已失败'}，停止刷新`);
        clearInterval(refreshInterval);
        
        // 显示任务完成或失败的通知
        if (task.status === 'completed') {
          ElMessage.success({
            message: '任务已成功完成！',
            duration: 5000
          });
        } else {
          ElMessage.error({
            message: `任务执行失败: ${task.failure_reason || '未知错误'}`,
            duration: 0,
            showClose: true
          });
        }
      }
    }, 2000); // 每2秒刷新一次
    
    // 30分钟后自动停止刷新，防止无限刷新
    setTimeout(() => {
      console.log(`【调试】到达最大刷新时间，停止刷新`);
      clearInterval(refreshInterval);
    }, 30 * 60 * 1000);
    
  } catch (error) {
    console.error('【调试】运行任务失败:', error);
    console.error('【调试】错误类型:', error.constructor.name);
    console.error('【调试】详细错误信息:', error.response?.data || error.message || '无详细信息');
    ElMessage.error({
      message: `运行任务失败: ${error.message || '未知错误'}`,
      duration: 0,
      showClose: true
    });
  } finally {
    // 最后从提交中的任务集合移除
    submittingTaskIds.value.delete(taskId);
  }
}

const deleteTask = async (taskId) => {
  try {
    // 检查任务是否正在提交中
    if (submittingTaskIds.value.has(taskId)) {
      ElMessage.warning('任务正在提交中，请勿重复操作');
      return;
    }
    
    // 检查任务状态
    const task = tasks.value.find(t => t.id === taskId);
    if (task && task.status === 'processing') {
      ElMessage.warning('正在处理中的任务无法删除');
      return;
    }
    
    await ElMessageBox.confirm(
      `确定要删除任务 "${task?.name || `ID: ${taskId}`}" 吗？此操作不可恢复！`,
      '删除确认', 
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'delete-confirm',
        distinguishCancelAndClose: true
      }
    )
    
    // 添加到提交中的任务集合
    submittingTaskIds.value.add(taskId);
    
    try {
      await taskService.delete(taskId);
      ElMessage.success('任务删除成功');
      await fetchData();
    } catch (apiError) {
      console.error('删除任务失败:', apiError);
      ElMessage.error(`删除任务失败: ${apiError.message || '未知错误'}`);
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error);
      ElMessage.error('删除任务失败');
    }
  } finally {
    // 从提交中的任务集合移除
    submittingTaskIds.value.delete(taskId);
  }
}

const resetNewTask = () => {
  newTask.value = {
    name: '',
    algorithm: ['algorithm1'],
    images: []
  }
  // 自动生成任务名称
  newTask.value.name = generateTaskName()
}

const openCreateDialog = () => {
  resetNewTask()
  createDialogVisible.value = true
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const navigateTo = (path) => {
  router.push(path)
}

const getStatusClass = (status) => {
  return `status-${status}`
}

// 切换任务详情展开状态
const toggleTaskDetails = (taskId) => {
  if (expandedTaskIds.value.has(taskId)) {
    expandedTaskIds.value.delete(taskId)
  } else {
    expandedTaskIds.value.add(taskId)
  }
}

// 检查任务是否已展开
const isTaskExpanded = (taskId) => {
  return expandedTaskIds.value.has(taskId)
}

// 添加检查任务状态的辅助函数
const checkTaskStatus = (taskId, allowedStatuses = []) => {
  const task = tasks.value.find(t => t.id === taskId)
  if (!task) return false
  
  return allowedStatuses.includes(task.status)
}

// 直接通过axios发送请求测试
const testTaskRestart = async (taskId) => {
  console.log(`【测试】直接通过axios发送任务重启请求: ID=${taskId}`);
  try {
    const token = localStorage.getItem('token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    
    console.log(`【测试】请求URL: ${apiClient.defaults.baseURL}/tasks/${taskId}/restart/`);
    console.log(`【测试】请求头:`, headers);
    
    // 直接使用axios发送POST请求，绕过服务层
    const response = await apiClient.post(`/tasks/${taskId}/restart/`, {}, { headers });
    console.log(`【测试】直接请求成功:`, response.data);
    ElMessage.success('测试请求成功');
    await fetchData();
  } catch (error) {
    console.error(`【测试】直接请求失败:`, error);
    console.error(`【测试】请求状态:`, error.response?.status);
    console.error(`【测试】错误详情:`, error.response?.data);
    ElMessage.error(`测试请求失败: ${error.message}`);
  }
}

// 获取指定图片ID的URL
const getImageUrlById = (imageId) => {
  const image = images.value.find(img => img.id === imageId)
  if (image) {
    return getImageUrl(image.file)
  }
  return null
}

// 获取任务的第一张图片URL作为预览
const getFirstImageUrl = (task) => {
  if (task.images && task.images.length > 0) {
    const firstImageId = task.images[0]
    return getImageUrlById(firstImageId)
  }
  return null
}

// 获取任务的图片数量
const getTaskImagesCount = (task) => {
  return task.images ? task.images.length : 0
}

// 修改图片弹窗控制逻辑
const activePopupTaskId = ref(null)
const popupPosition = ref({ x: 0, y: 0 })

// 显示图片弹窗
const showImagesPopup = (taskId, event) => {
  activePopupTaskId.value = taskId
  
  // 计算弹窗位置，基于鼠标位置
  const mouseX = event.clientX
  const mouseY = event.clientY
  
  // 设置初始位置在鼠标附近
  popupPosition.value = {
    x: Math.max(10, Math.min(mouseX, window.innerWidth - 620)),
    y: Math.max(10, Math.min(mouseY, window.innerHeight - 500))
  }
}

// 隐藏图片弹窗
const hideImagesPopup = () => {
  activePopupTaskId.value = null
}

// 查看任务详情
const viewTaskDetails = (taskId) => {
  // 如果任务已展开，则折叠
  if (expandedTaskIds.value.has(taskId)) {
    expandedTaskIds.value.delete(taskId);
  } else {
    // 展开任务详情
    expandedTaskIds.value.add(taskId);
  }
}

// 显示更多任务信息
const showTaskInfo = (task) => {
  const algorithmInfo = getSelectedAlgorithmsFromTask(task);
  const selectedNames = algorithmInfo.split('').map(
    num => algorithmDisplayNames[`algorithm${num}`] || `未知算法(${num})`
  );
  
  // 简化算法选择来源
  let sourceInfo = (task && task.algorithms && Array.isArray(task.algorithms) && task.algorithms.length > 0)
    ? '任务算法数组' 
    : '默认配置';
  
  // 构建更丰富的算法信息
  let infoHTML = '<div style="text-align:left;">';
  infoHTML += `<h4 style="margin:5px 0;">任务使用的算法（${algorithmInfo.length}个）：</h4>`;
  infoHTML += '<div style="color:#999;font-size:12px;margin-bottom:8px;">算法来源: ' + sourceInfo + '</div>';
  infoHTML += '<ul style="margin:5px 0;padding-left:20px;">';
  
  selectedNames.forEach((name, index) => {
    const algorithmNumber = algorithmInfo[index];
    const color = getAlgorithmColor(`algorithm${algorithmNumber}`);
    infoHTML += `<li style="margin:3px 0;">
      <span style="display:inline-block;width:12px;height:12px;background-color:${color};border-radius:2px;margin-right:5px;"></span>
      ${name}
    </li>`;
  });
  
  infoHTML += '</ul>';
  
  // 添加任务信息
  if (task.description) {
    infoHTML += '<h4 style="margin:10px 0 5px;">任务描述：</h4>';
    infoHTML += `<div style="padding:8px;background:#f5f5f5;border-radius:4px;font-size:13px;">${task.description}</div>`;
  }
  
  infoHTML += '</div>';
  
  ElMessage({
    dangerouslyUseHTMLString: true,
    message: infoHTML,
    type: 'info',
    duration: 8000,
    showClose: true
  });
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
        <div class="nav-item active" @click="navigateTo('/tasks')">
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
          <h2>任务管理</h2>
          <div class="header-actions">
            <button 
              class="test-connection-button" 
              @click="checkBackendConnection"
              title="测试后端服务器连接状态"
            >
              测试连接
            </button>
            <button class="create-button" @click="openCreateDialog">创建任务</button>
          </div>
        </div>
        
        <!-- 添加搜索筛选区 -->
        <div class="search-filters">
          <div class="search-form">
            <div class="form-item">
              <label>任务ID</label>
              <input type="text" v-model="searchParams.taskId" placeholder="请输入任务ID" @input="debounceSearch" />
            </div>
            <div class="form-item">
              <label>任务名称</label>
              <input type="text" v-model="searchParams.taskName" placeholder="请输入任务名称" @input="debounceSearch" />
            </div>
            <div class="form-item">
              <label>算法名称</label>
              <input type="text" v-model="searchParams.algorithmName" placeholder="请输入算法名称" @input="debounceSearch" />
            </div>
            <div class="form-actions">
              <button class="reset-button" @click="resetSearch">重置</button>
              <button class="search-button">查询</button>
            </div>
          </div>
        </div>
        
        <div v-if="loading" class="loading-container">
          <div class="loading-text">加载中...</div>
        </div>
        
        <div v-else-if="filteredTasks.length === 0" class="empty-message">
          暂无任务，请创建新任务
        </div>
        
        <div v-else class="task-list">
          <table class="task-table">
            <thead>
              <tr>
                <th style="width: 5%"></th><!-- 三角符号列 -->
                <th>任务ID</th>
                <th>任务名称</th>
                <th>算法个数</th>
                <th>图片数量</th>
                <th>缩略图</th>
                <th>创建时间</th>
                <th>进度</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="task in filteredTasks" :key="task.id">
                <tr 
                  :class="{ 'processing-row': task.status === 'processing' }"
                  @click="toggleTaskDetails(task.id)"
                  class="clickable-row"
                >
                  <td class="expand-cell">
                    <div class="expand-icon">
                      {{ isTaskExpanded(task.id) ? '▼' : '▶' }}
                    </div>
                  </td>
                  <td>{{ task.id }}</td>
                  <td>
                    <div class="task-name">
                      {{ task.name }}
                    </div>
                  </td>
                  <td class="algorithm-cell">
                    <div 
                      class="algorithm-badge"
                      @click="showTaskInfo(task)"
                      title="点击查看所有算法"
                    >
                      {{ getSelectedAlgorithmsFromTask(task).length }}个
                      <span v-if="getSelectedAlgorithmsFromTask(task).length > 0" class="algorithm-tags">
                        <span 
                          v-for="(id, index) in getSelectedAlgorithmsFromTask(task).split('')" 
                          :key="index"
                          class="algorithm-mini-tag"
                          :style="{ backgroundColor: getAlgorithmColor(`algorithm${id}`) }"
                          :title="algorithmDisplayNames[`algorithm${id}`]"
                        ></span>
                      </span>
                    </div>
                  </td>
                  <td>
                    {{ getTaskImagesCount(task) }}
                  </td>
                  <td>
                    <a 
                      href="#" 
                      class="thumbnail-btn"
                      @click.prevent="showImagesPopup(task.id, $event)"
                    >
                      <div class="task-thumbnails-container">
                        <!-- 最多显示4个缩略图 -->
                        <div 
                          v-for="(imageId, index) in task.images.slice(0, 4)" 
                          :key="imageId" 
                          class="task-thumbnail"
                        >
                          <img 
                            :src="getImageUrlById(imageId)" 
                            :alt="images.find(img => img.id === imageId)?.title" 
                          />
                        </div>
                        <!-- 如果有更多图片，显示省略号 -->
                        <div v-if="task.images.length > 4" class="more-images-indicator">
                          +{{ task.images.length - 4 }}
                        </div>
                      </div>
                    </a>
                  </td>
                  <td>{{ new Date(task.created_at).toLocaleString() }}</td>
                  <td>
                    <div class="progress-container">
                      <div 
                        class="progress-bar" 
                        :class="{ 
                          'progress-success': task.status === 'completed',
                          'progress-warning': task.status === 'processing',
                          'progress-danger': task.status === 'failed'
                        }"
                        :style="{ width: `${task.progress || 0}%` }"
                      ></div>
                      <span class="progress-text">{{ Math.round(task.progress || 0) }}%</span>
                    </div>
                  </td>
                  <td>
                    <div class="action-buttons">
                      <button 
                        class="restart-button" 
                        @click="restartTask(task.id)"
                        :disabled="!checkTaskStatus(task.id, ['failed', 'pending', 'processing']) || submittingTaskIds.has(task.id)"
                        :title="
                          submittingTaskIds.has(task.id) ? '正在提交任务...' :
                          !checkTaskStatus(task.id, ['failed', 'pending', 'processing']) ? '只能重启失败、待处理或处理中的任务' : 
                          '重新启动任务'
                        "
                      >
                        {{ submittingTaskIds.has(task.id) ? '提交中...' : '重新启动' }}
                      </button>
                      <button 
                        class="delete-button" 
                        @click="deleteTask(task.id)"
                        :disabled="task.status === 'processing' || submittingTaskIds.has(task.id)"
                        :title="
                          submittingTaskIds.has(task.id) ? '操作进行中，无法删除' :
                          task.status === 'processing' ? '处理中的任务无法删除' : 
                          '删除此任务'
                        "
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
                <!-- 详情行 -->
                <tr v-if="isTaskExpanded(task.id)" class="task-details-row">
                  <td colspan="9" class="task-details">
                    <div class="detail-item">
                      <span class="detail-label">算法列表:</span>
                      <div class="detail-algorithms">
                        <span 
                          v-for="(algorithmName, index) in getAlgorithmNames(task)"
                          :key="index"
                          class="detail-algorithm-tag"
                          :style="{ backgroundColor: getAlgorithmColor(`algorithm${getSelectedAlgorithmsFromTask(task)[index]}`) }"
                        >
                          {{ algorithmName }}
                        </span>
                      </div>
                    </div>
                    <div class="detail-item" v-if="task.completed_at">
                      <span class="detail-label">完成时间:</span>
                      <span class="detail-value">{{ new Date(task.completed_at).toLocaleString() }}</span>
                    </div>
                    <div class="detail-item error" v-if="task.failure_reason">
                      <span class="detail-label">失败原因:</span>
                      <span class="detail-value">{{ task.failure_reason }}</span>
                    </div>
                    <div class="detail-item">
                      <span class="detail-label">处理图片:</span>
                      <span class="detail-value">{{ task.images.length }}张</span>
                    </div>
                    <div class="detail-images" v-if="task.images && task.images.length > 0">
                      <div v-for="imageId in task.images" :key="imageId" class="detail-image">
                        <img 
                          :src="getImageUrlById(imageId)" 
                          :alt="images.find(img => img.id === imageId)?.title" 
                        />
                        <div class="image-title">{{ images.find(img => img.id === imageId)?.title || '未命名图片' }}</div>
                      </div>
                      <div v-if="task.images.length > 10" class="more-images-note">
                        仅显示前10张图片...
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
        
        <!-- 创建任务对话框 -->
        <div v-if="createDialogVisible" class="dialog-overlay">
          <div class="dialog">
            <div class="dialog-header">
              <h3>创建新任务</h3>
              <button 
                class="close-button" 
                @click="createDialogVisible = false" 
                :disabled="createLoading"
              >
                ×
              </button>
            </div>
            
            <div class="dialog-body">
              <div class="form-group">
                <label for="task-name">任务名称</label>
                <input 
                  type="text" 
                  id="task-name" 
                  v-model="newTask.name" 
                  placeholder="请输入任务名称"
                  :disabled="createLoading"
                />
              </div>
              
              <div class="form-group">
                <label>处理算法</label>
                <div class="algorithm-table">
                  <div 
                    v-for="(displayName, value) in algorithmDisplayNames"
                    :key="value" 
                    class="algorithm-row"
                    :class="{ 'selected': newTask.algorithm.includes(value) }"
                    @click="() => {
                      if (newTask.algorithm.includes(value)) {
                        // 不允许取消选择唯一选中的算法
                        if (newTask.algorithm.length > 1) {
                          newTask.algorithm = newTask.algorithm.filter(a => a !== value);
                        }
                      } else {
                        newTask.algorithm.push(value);
                      }
                      newTask.name = generateTaskName();
                    }"
                  >
                    <div class="algorithm-checkbox-cell">
                      <input 
                        type="checkbox" 
                        :id="`algo-${value}`" 
                        :value="value"
                        v-model="newTask.algorithm"
                        :disabled="createLoading"
                        class="blue-checkbox"
                        @click.stop
                      />
                    </div>
                    <div class="algorithm-name-cell">
                      <label :for="`algo-${value}`">{{ displayName }}</label>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="form-group">
                <label>选择图片</label>
                <div v-if="images.length === 0" class="no-images">
                  暂无可选图片，请先上传图片
                </div>
                <div v-else class="image-selection">
                  <div 
                    v-for="image in images" 
                    :key="image.id"
                    class="image-option"
                    :class="{ selected: newTask.images.includes(image.id) }"
                    @click="() => {
                      if (newTask.images.includes(image.id)) {
                        newTask.images = newTask.images.filter(id => id !== image.id)
                      } else {
                        newTask.images.push(image.id)
                      }
                    }"
                  >
                    <div class="image-thumbnail">
                      <img :src="getImageUrlById(image.id)" :alt="image.title">
                    </div>
                    <div class="image-name">{{ image.title }}</div>
                    <div class="selection-indicator">✓</div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="dialog-footer">
              <button 
                class="cancel-button" 
                @click="createDialogVisible = false"
                :disabled="createLoading"
              >
                取消
              </button>
              <button 
                class="confirm-button" 
                @click="createTask"
                :disabled="createLoading || images.length === 0"
              >
                {{ createLoading ? '创建中...' : '创建' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 弹窗组件 -->
  <div 
    v-if="activePopupTaskId" 
    class="hover-images-popup"
    :style="{left: popupPosition.x + 'px', top: popupPosition.y + 'px'}"
    @mouseenter="activePopupTaskId = activePopupTaskId"
    @mouseleave="hideImagesPopup()"
  >
    <div class="popup-title">所有图片 ({{ getTaskImagesCount(tasks.find(t => t.id === activePopupTaskId)) }}张)</div>
    <div class="popup-images-grid">
      <div 
        v-for="imageId in tasks.find(t => t.id === activePopupTaskId)?.images" 
        :key="imageId" 
        class="popup-image"
      >
        <img 
          :src="getImageUrlById(imageId)" 
          :alt="images.find(img => img.id === imageId)?.title" 
        />
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

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.test-connection-button {
  background-color: #52c41a;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  font-size: 14px;
}

.test-connection-button:hover {
  background-color: #73d13d;
}

.create-button {
  background-color: #1890ff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.create-button:hover {
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
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.task-list {
  width: 100%;
  overflow-x: auto;
}

.task-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.task-table th, .task-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.task-table th {
  background-color: #fafafa;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.task-name {
  font-weight: 500;
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.actions-cell {
  white-space: nowrap;
  display: flex;
  gap: 8px;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-start;
}

.progress-cell {
  min-width: 150px;
}

.progress-container {
  width: 100%;
  height: 20px;
  background-color: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s ease;
  background-color: #4caf50;
}

.progress-warning {
  background-color: #ff9800;
}

.progress-success {
  background-color: #4caf50;
}

.progress-danger {
  background-color: #f44336;
}

.progress-text {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #333;
  font-weight: bold;
  font-size: 0.9em;
  text-shadow: 0 0 3px rgba(255, 255, 255, 0.8);
}

.processing-row {
  animation: processing-pulse 2s infinite;
}

@keyframes processing-pulse {
  0% {
    background-color: rgba(255, 152, 0, 0.05);
  }
  50% {
    background-color: rgba(255, 152, 0, 0.15);
  }
  100% {
    background-color: rgba(255, 152, 0, 0.05);
  }
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.9em;
  font-weight: 500;
}

.status-icon {
  margin-right: 5px;
  font-size: 1.1em;
}

.status-pending {
  background-color: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.status-processing {
  background-color: #fff7e6;
  color: #fa8c16;
  border: 1px solid #ffd591;
}

.status-completed {
  background-color: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.status-failed {
  background-color: #fff1f0;
  color: #f5222d;
  border: 1px solid #ffa39e;
}

.status-message {
  font-size: 0.85em;
  opacity: 0.8;
  margin-left: 4px;
}

.task-info {
  margin-bottom: 16px;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 0;
}

.info-item {
  margin-bottom: 8px;
  display: flex;
}

.info-item .label {
  width: 80px;
  color: #8c8c8c;
}

.info-item .value {
  flex: 1;
}

.info-item.error .value {
  color: #f5222d;
}

.task-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.run-button, .restart-button, .delete-button {
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  font-size: 13px;
  margin-right: 5px;
  transition: all 0.3s ease;
}

.run-button {
  background-color: #1890ff;
}

.run-button:disabled,
.restart-button:disabled,
.delete-button:disabled {
  background-color: #d9d9d9;
  cursor: not-allowed;
  color: #ffffff;
}

.run-button:disabled:hover,
.restart-button:disabled:hover,
.delete-button:disabled:hover {
  background-color: #d9d9d9;
}

.delete-button {
  background-color: #f5222d;
}

.delete-button:hover {
  background-color: #ff4d4f;
}

/* 删除确认弹窗的特殊样式 */
.el-message-box.delete-confirm .el-message-box__title {
  color: #f5222d;
}

.el-message-box.delete-confirm .el-message-box__content {
  color: #333;
  padding: 20px 0;
}

.el-message-box.delete-confirm .el-message-box__btns .el-button--primary {
  background-color: #f5222d;
  border-color: #f5222d;
}

.el-message-box.delete-confirm .el-message-box__btns .el-button--primary:hover {
  background-color: #ff4d4f;
  border-color: #ff4d4f;
}

.test-button {
  background-color: #52c41a;
  color: white;
}

.test-button:hover {
  background-color: #73d13d;
}

.dialog-overlay {
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

.dialog {
  background-color: white;
  border-radius: 8px;
  width: 600px;
  max-width: 90%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  overflow-y: auto;
  flex: 1;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group input, .form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.3s;
}

.form-group input:focus, .form-group select:focus {
  border-color: #1890ff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.no-images {
  color: #8c8c8c;
  padding: 16px;
  text-align: center;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
}

.image-selection {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.image-option {
  border: 2px solid #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  position: relative;
  transition: all 0.3s;
}

.image-option:hover {
  border-color: #1890ff;
}

.image-option.selected {
  border-color: #1890ff;
  background-color: rgba(24, 144, 255, 0.05);
}

.image-thumbnail {
  height: 80px;
  overflow: hidden;
}

.image-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-name {
  padding: 8px;
  font-size: 12px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selection-indicator {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: #1890ff;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.3s;
}

.image-option.selected .selection-indicator {
  opacity: 1;
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

.task-name-wrapper {
  display: flex;
  align-items: center;
}

.expand-icon {
  margin-right: 8px;
  cursor: pointer;
  user-select: none;
  font-size: 12px;
  display: inline-block;
  width: 16px;
  text-align: center;
}

.task-row {
  transition: background-color 0.2s;
}

.task-row.expanded {
  background-color: #f6f8fa;
}

.task-details-row {
  background-color: #fafafa;
}

.task-details {
  padding: 16px 16px 16px 48px !important;
}

.detail-item {
  margin-bottom: 8px;
  display: flex;
}

.detail-label {
  width: 80px;
  color: #8c8c8c;
}

.detail-value {
  flex: 1;
}

.detail-item.error .detail-value {
  color: #f5222d;
}

.images-count {
  text-align: center;
  font-weight: 500;
}

.thumbnail-cell {
  width: 300px;
  position: relative;
}

.task-thumbnails-container {
  display: flex;
  gap: 4px;
  position: relative;
  align-items: center;
}

.task-thumbnail {
  width: 50px;
  height: 50px;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
  border: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.task-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.more-images-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 12px;
  padding: 0 8px;
  height: 20px;
  border-radius: 10px;
  margin-left: 4px;
}

.hover-images-popup {
  position: fixed;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  width: 600px;
  max-height: 600px;
  overflow-y: auto;
  padding: 16px;
  display: block;
  transform: none;
  transition: opacity 0.2s;
}

.task-thumbnails-container:hover .hover-images-popup {
  display: block;
}

.popup-title {
  font-weight: 500;
  margin-bottom: 12px;
  color: #333;
}

.popup-images-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.popup-image {
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #f0f0f0;
}

.popup-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-thumbnail {
  color: #bfbfbf;
  font-size: 12px;
}

.detail-images {
  display: flex;
  gap: 15px;
  margin-top: 15px;
  flex-wrap: wrap;
  max-height: 300px;
  overflow-y: auto;
}

.detail-image {
  width: 100px;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #f0f0f0;
  margin-bottom: 10px;
  position: relative;
}

.detail-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-image .image-title {
  font-size: 12px;
  color: #333;
  text-align: center;
  padding: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100px;
  background-color: #f9f9f9;
  border-top: 1px solid #eee;
  margin-top: 2px;
}

.more-images-note {
  display: flex;
  align-items: center;
  color: #8c8c8c;
  font-size: 12px;
}

.popup-close {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 24px;
  height: 24px;
  background-color: #f0f0f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  color: #333;
}

.popup-close:hover {
  background-color: #e0e0e0;
}

.task-thumbnails-container .hover-trigger {
  cursor: pointer;
}

.task-id {
  font-weight: 500;
  color: #555;
  width: 80px;
  text-align: center;
}

.algorithm-table {
  display: flex;
  flex-direction: column;
  margin-top: 10px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  overflow: hidden;
  width: 100%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.algorithm-row {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.3s;
  cursor: pointer;
  position: relative;
}

.algorithm-row:last-child {
  border-bottom: none;
}

.algorithm-row:hover {
  background-color: #e6f7ff;
}

.algorithm-row.selected {
  background-color: #e6f7ff;
}

.algorithm-row.selected:after {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: #1890ff;
}

.algorithm-checkbox-cell {
  width: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.algorithm-name-cell {
  flex: 1;
  padding-left: 10px;
}

.algorithm-name-cell label {
  cursor: pointer;
  font-size: 14px;
  color: #333;
  font-weight: 400;
}

.blue-checkbox {
  accent-color: #1890ff;
  width: 18px;
  height: 18px;
  cursor: pointer;
  border-radius: 4px;
}

.info-button {
  margin-left: 5px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #f1f1f1;
  color: #666;
  font-size: 12px;
  font-weight: bold;
  cursor: pointer;
  border: none;
}

.algorithm-cell {
  width: 120px;
  position: relative;
}

.algorithm-count {
  display: flex;
  align-items: center;
  font-weight: 500;
}

.algorithm-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.algorithm-tag, .detail-algorithm-tag {
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: default;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.detail-algorithms {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: 10px;
}

.detail-algorithm-tag {
  margin-bottom: 5px;
  padding: 6px 12px;
  font-size: 13px;
}

.algorithm-tag:hover, .detail-algorithm-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

/* 添加搜索筛选区样式 */
.search-filters {
  background-color: white;
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
  border: 1px solid #f0f0f0;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
}

.form-item {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 200px;
}

.form-item label {
  margin-bottom: 8px;
  color: #666;
}

.form-item input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  height: 32px;
}

.form-actions {
  display: flex;
  gap: 12px;
}

.reset-button {
  background-color: white;
  border: 1px solid #d9d9d9;
  color: rgba(0, 0, 0, 0.65);
  padding: 0 12px;
  height: 32px;
  border-radius: 4px;
  cursor: pointer;
}

.search-button {
  background-color: #1890ff;
  color: white;
  border: none;
  padding: 0 12px;
  height: 32px;
  border-radius: 4px;
  cursor: pointer;
}

.clickable-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.clickable-row:hover {
  background-color: #f5f5f5;
}

.algorithm-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  font-weight: 500;
  background-color: #f5f5f5;
  padding: 5px 10px;
  border-radius: 15px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.algorithm-badge:hover {
  background-color: #eaeaea;
}

.algorithm-tags {
  display: flex;
  gap: 3px;
}

.algorithm-mini-tag {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
</style> 