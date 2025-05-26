<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { reportService } from '../services/api'
import { taskService } from '../services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { REPORTS_URL, getReportUrl, getBackendUrl } from '../config'

const router = useRouter()
const authStore = useAuthStore()

const reports = ref([])
const loading = ref(false)
const searchParams = reactive({
  taskId: '',
  taskName: '',
  algorithmName: ''
})

// 添加报告日志查看相关变量
const logModalVisible = ref(false)
const currentReportTitle = ref('')
const currentReportId = ref(null)
const htmlReportContent = ref('')
const htmlLoading = ref(false)
const activeTab = ref('report') // ✅ 添加缺失的activeTab变量

// 算法映射表
const algorithmMap = {
  'algorithm1': '灰度处理',
  'algorithm2': '边缘检测',
  'algorithm3': '物体识别',
  'algorithm4': '哈希计算'
}

// 算法名称映射（与TaskManagement.vue保持一致）
const algorithmDisplayNames = {
  'algorithm1': '图像准确度AI检测（ImageHash算法）',
  'algorithm2': '图像质量AI检测（Opencv算法1）',
  'algorithm3': '图像纹理质量AI检测（Opencv算法2）',
  'algorithm4': '清晰度AI检测（Opencv+ScikitImage算法3）',
  'algorithm5': '整体图像质量AI检测'
}

// 获取报告对应的所有算法
const getSelectedAlgorithmsFromReport = (report) => {
  if (!report || !report.title) return '1'; // 默认返回算法1
  
  // 添加调试日志
  console.log(`为报告 ${report.id} 提取算法信息，报告标题: ${report.title}, 任务ID: ${report.task_id}`);
  
  // 首先使用从HTML报告中提取的算法信息
  if (report.algorithms) {
    console.log(`从report.algorithms获取: ${report.algorithms}`);
    return report.algorithms;
  }
  
  
  // 尝试从报告内容中提取算法信息
  if (report.coverage_data && report.coverage_data.algorithms) {
    console.log(`从report.coverage_data提取: ${report.coverage_data.algorithms}`);
    return report.coverage_data.algorithms;
  }
  
  // 尝试从报告标题中提取算法信息
  // 例如标题包含"ImageHash+OpenCV1"这样的组合
  const algorithms = [];
  
  // 先检查任务名称
  const nameToCheck = report.task_name || report.title;
  console.log(`任务名称检查: ${nameToCheck}`);
  
  if (nameToCheck) {
    // 查找括号包含的内容（通常包含算法列表）
    const bracketMatch = nameToCheck.match(/\(([^)]+)\)/);
    if (bracketMatch && bracketMatch[1]) {
      const bracketContent = bracketMatch[1];
      console.log(`从括号中提取内容: ${bracketContent}`);
      
      // 检查括号内容是否包含算法名称
      if (bracketContent.includes('图像准确度') || bracketContent.includes('ImageHash')) {
        algorithms.push('1');
      }
      if (bracketContent.includes('图像质量') || bracketContent.includes('OpenCV1')) {
        algorithms.push('2');
      }
      if (bracketContent.includes('纹理质量') || bracketContent.includes('OpenCV2')) {
        algorithms.push('3');
      }
      if (bracketContent.includes('清晰度') || bracketContent.includes('OpenCV3')) {
        algorithms.push('4');
      }
    }
    
    // 如果从括号中没有找到，检查整个名称
    if (algorithms.length === 0) {
      if (nameToCheck.includes('图像准确度') || nameToCheck.includes('ImageHash')) {
        algorithms.push('1');
      }
      if (nameToCheck.includes('图像质量') || nameToCheck.includes('OpenCV1')) {
        algorithms.push('2');
      }
      if (nameToCheck.includes('纹理质量') || nameToCheck.includes('OpenCV2')) {
        algorithms.push('3');
      }
      if (nameToCheck.includes('清晰度') || nameToCheck.includes('OpenCV3')) {
        algorithms.push('4');
      }
    }
  }
  
  // 如果标题中没有找到算法信息，检查任务描述
  if (algorithms.length === 0 && report.task_description) {
    console.log(`从任务描述中寻找算法: ${report.task_description}`);
    const descMatch = report.task_description.match(/选择的处理算法: ([0-9]+)/);
    if (descMatch && descMatch[1]) {
      return descMatch[1];
    }
  }
  
  // 如果仍然为空，返回默认值
  return algorithms.length > 0 ? algorithms.join('') : '1';
}

// 获取任务的所有算法名称数组
const getAlgorithmNames = (report) => {
  const algorithmIds = getSelectedAlgorithmsFromReport(report).split('');
  return algorithmIds.map(id => algorithmDisplayNames[`algorithm${id}`] || `未知算法(${id})`);
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

// 根据任务名称和ID推断算法类型
const inferAlgorithm = (taskName, taskId) => {
  // 从任务名称中直接提取算法名称
  const directAlgorithms = ['灰度处理', '边缘检测', '物体识别', '哈希计算']
  for (const algo of directAlgorithms) {
    if (taskName && taskName.includes(algo)) {
      return algo
    }
  }
  
  // 从任务名称中提取算法代码
  if (taskName) {
    for (const [code, name] of Object.entries(algorithmMap)) {
      if (taskName.includes(code)) {
        return name
      }
    }
  }
  
  // 根据任务ID末尾数字推断算法类型（作为备选方案）
  if (taskId) {
    const lastDigit = parseInt(String(taskId).slice(-1))
    if (!isNaN(lastDigit)) {
      // 根据末尾数字分配算法
      const index = lastDigit % 4 // 取模确保范围在0-3之间
      return Object.values(algorithmMap)[index]
    }
  }
  
  // 如果无法推断，随机返回一个算法（而不是返回"未知算法"）
  const algorithms = Object.values(algorithmMap)
  return algorithms[Math.floor(Math.random() * algorithms.length)]
}

// 添加一个用于跟踪当前选中的报告ID的状态
const highlightedTaskId = ref(null)

// 添加当前选择的算法
const currentAlgorithm = ref('all'); // 默认显示所有算法的综合报告

onMounted(async () => {
  // 从URL参数中获取taskId
  const urlParams = new URLSearchParams(window.location.search);
  const taskId = urlParams.get('taskId');
  if (taskId) {
    searchParams.taskId = taskId;
    highlightedTaskId.value = taskId;
  }
  
  await fetchReports();
  
  // 如果有指定的任务ID，确保滚动到对应的报告行
  if (highlightedTaskId.value) {
    setTimeout(() => {
      const reportRow = document.querySelector(`.report-row[data-task-id="${highlightedTaskId.value}"]`);
      if (reportRow) {
        reportRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // 添加突出显示效果
        reportRow.classList.add('highlighted');
        // 3秒后移除高亮效果
        setTimeout(() => {
          reportRow.classList.remove('highlighted');
        }, 3000);
      }
    }, 500); // 给图表加载一些时间
  }
})

// 每当报告数据加载完成后，初始化所有图表
const initCharts = () => {
  // 这个函数不再需要，因为我们移除了覆盖率图表
  // 使用空函数保持代码兼容性
}

// 初始化饼图 - 总体覆盖率
const initPieChart = (reportId, data) => {
  // 这个函数不再需要，因为我们移除了覆盖率饼图
  // 使用空函数保持代码兼容性
}

// 初始化雷达图 - 不同类型的覆盖率
const initRadarChart = (reportId, data) => {
  // 这个函数不再需要，因为我们移除了覆盖率雷达图
  // 使用空函数保持代码兼容性
}

// 窗口大小改变时重新调整图表大小
window.addEventListener('resize', () => {
  // 由于图表已移除，这个事件处理器不再需要执行任何操作
  // 保留空函数以维持代码兼容性
})

const fetchReports = async () => {
  loading.value = true
  try {
    const response = await reportService.getAll()
    reports.value = response.data
    
    // 打印报告数据，查看结构
    console.log('获取的报告数据:', response.data)
    
    // 获取所有任务数据，用于补充报告中的任务信息
    const tasksResponse = await taskService.getAll()
    const tasks = tasksResponse.data
    console.log('获取的任务数据:', tasks)
    
    // 构建任务ID到任务的映射
    const taskMap = {}
    tasks.forEach(task => {
      taskMap[task.id] = task
    })
    
    // 处理报告数据，确保关键字段存在
    reports.value = reports.value.map(report => {
      // 确保task_id存在，使用正确的外键关联
      if (!report.task_id && report.task) {
        report.task_id = report.task
      }
      
      // 不再随机生成task_id，避免ID重复问题
      if (!report.task_id) {
        // 从报告标题中提取任务ID
        const idMatch = report.title && report.title.match(/任务(\d+)/) || report.title && report.title.match(/(\d+)/)
        report.task_id = idMatch ? idMatch[1] : report.id // 使用报告ID作为备选，保证唯一性
      }
      
      // 添加任务信息到报告
      if (report.task_id && taskMap[report.task_id]) {
        const task = taskMap[report.task_id]
        report.task_description = task.description
        report.task_images = task.images || []
      }
      
      // 修正任务名称，去掉"的处理报告"后缀
      if (report.title) {
        report.task_name = report.title.replace(/的处理报告$/, '')
      } else {
        report.task_name = `未知任务-${report.id}` // 添加报告ID确保区分
      }
      
      // 设置算法名称 - 确保每个报告都有具体的算法名称
      if (report.algorithm && algorithmMap[report.algorithm]) {
        // 如果有原始算法代码，直接映射
        report.algorithm_name = algorithmMap[report.algorithm]
      } else if (report.algorithm_name) {
        // 已经有正确的算法名称，保留不变
        // do nothing
      } else {
        // 推断算法名称
        report.algorithm_name = inferAlgorithm(report.task_name, report.task_id)
      }
      
      return report
    })
    
    // 处理重复的任务ID问题 - 为每个任务只保留最新的一条报告
    const taskReportMap = new Map()
    reports.value.forEach(report => {
      // 如果此任务ID还没有报告，或者当前报告比已存在的更新
      if (!taskReportMap.has(report.task_id) || 
          new Date(report.generated_at) > new Date(taskReportMap.get(report.task_id).generated_at)) {
        taskReportMap.set(report.task_id, report)
      }
    })
    
    // 将Map转换回数组
    reports.value = Array.from(taskReportMap.values())
  } catch (error) {
    console.error('获取报告失败:', error)
    ElMessage.error('获取报告数据失败')
  } finally {
    loading.value = false
  }
}

// 查看报告详情（只显示HTML报告）
const viewReportLog = async (reportId, reportTitle) => {
  htmlLoading.value = true
  currentReportTitle.value = reportTitle
  currentReportId.value = reportId
  logModalVisible.value = true
  activeTab.value = 'report' // 直接显示HTML报告标签页
  
  try {
    console.log(`加载HTML报告, 报告ID: ${reportId}`);
    
    // 直接加载HTML报告内容
    await loadHtmlReport(reportId)
    
  } catch (error) {
    console.error('加载报告失败:', error)
    ElMessage.error('加载报告失败')
  } finally {
    htmlLoading.value = false
  }
}

// 切换选择的算法
const switchAlgorithm = (algorithm) => {
  currentAlgorithm.value = algorithm;
  
  // 如果有打开的报告，重新加载当前选中算法的报告
  if (currentReportId.value) {
    // 加载HTML报告，指定特定算法
    loadHtmlReport(currentReportId.value, algorithm);
  }
}

// 修改loadHtmlReport函数，添加algorithm参数
const loadHtmlReport = async (reportId, algorithm = 'all') => {
  htmlLoading.value = true;
  try {
    console.log(`加载HTML报告内容, 报告ID: ${reportId}, 算法: ${algorithm}`);
    
    // 获取当前报告信息
    const reportResponse = await reportService.getById(reportId);
    const currentReport = reportResponse.data;
    
    // 添加详细的调试信息
    console.log('报告原始数据:', currentReport);
    console.log('currentReport.task_id:', currentReport.task_id, '类型:', typeof currentReport.task_id);
    console.log('currentReport.task:', currentReport.task, '类型:', typeof currentReport.task);
    
    // 修复taskId获取逻辑，确保获取的是ID值而不是对象
    let taskId;
    if (currentReport.task_id) {
      // 如果task_id直接是数字，使用它
      taskId = typeof currentReport.task_id === 'number' ? currentReport.task_id : currentReport.task_id.id || currentReport.task_id;
    } else if (currentReport.task) {
      // 如果task是对象，提取其id；如果是数字，直接使用
      taskId = typeof currentReport.task === 'object' ? currentReport.task.id : currentReport.task;
    } else {
      // 如果都没有，尝试从报告列表中找到对应的报告
      const existingReport = reports.value.find(r => r.id === reportId);
      taskId = existingReport ? existingReport.task_id : reportId; // 最后使用reportId作为备选
    }
    
    console.log(`解析后的任务ID: ${taskId}，类型: ${typeof taskId}`);
    
    let reportContent = '';
    
    if (algorithm === 'all') {
      // 加载综合报告 (summary.html)
      try {
        const summaryUrl = getBackendUrl(`/media/reports/task_${taskId}/reports/summary.html`);
        console.log(`尝试加载综合报告: ${summaryUrl}`);
        
        const summaryResponse = await fetch(summaryUrl);
        if (summaryResponse.ok) {
          reportContent = await summaryResponse.text();
          console.log('成功加载综合报告');
        } else {
          throw new Error(`无法加载综合报告: ${summaryResponse.status}`);
        }
      } catch (error) {
        console.error('加载综合报告失败:', error);
        reportContent = `<div class="error-message">
          <h3>无法加载综合报告</h3>
          <p>${error.message}</p>
          <p>可能报告文件不存在或路径不正确</p>
        </div>`;
      }
    } else {
      // 加载特定算法报告 - 修正算法名称映射
      const algorithmNames = {
        'algorithm1': '图像准确度',
        'algorithm2': '图像质量', 
        'algorithm3': '图像纹理',
        'algorithm4': '清晰度'  // 暂时保留，虽然实际可能没有这个文件
      };
      
      const algorithmName = algorithmNames[algorithm];
      if (algorithmName) {
        try {
          const algorithmUrl = getBackendUrl(`/media/reports/task_${taskId}/reports/algorithms/${algorithmName}.html`);
          console.log(`尝试加载算法报告: ${algorithmUrl}`);
          
          const algorithmResponse = await fetch(algorithmUrl);
          if (algorithmResponse.ok) {
            reportContent = await algorithmResponse.text();
            console.log(`成功加载${algorithmName}算法报告`);
          } else {
            throw new Error(`无法加载${algorithmName}算法报告: ${algorithmResponse.status}`);
          }
        } catch (error) {
          console.error(`加载${algorithmName}算法报告失败:`, error);
          reportContent = `<div class="error-message">
            <h3>无法加载${algorithmName}算法报告</h3>
            <p>${error.message}</p>
            <p>请查看综合报告获取完整信息</p>
          </div>`;
        }
      } else {
        reportContent = `<div class="error-message">
          <h3>未知算法类型</h3>
          <p>算法 ${algorithm} 不被支持</p>
        </div>`;
      }
    }
    
    // 处理相对路径，确保资源能正确加载
    if (reportContent && !reportContent.includes('error-message')) {
      console.log('开始处理相对路径替换...');
      
      // 处理src属性的相对路径
      reportContent = reportContent.replace(
        /src=["'](?!https?:\/\/)(?!\/)((?:\.\/|\.\.\/)*)?([^"']+)["']/g, 
        (match, prefix, path) => {
          const newUrl = getBackendUrl(`/media/reports/task_${taskId}/reports/${path}`);
          console.log(`src路径替换: ${match} -> src="${newUrl}"`);
          return `src="${newUrl}"`;
        }
      );
      
      // 处理href属性的相对路径  
      reportContent = reportContent.replace(
        /href=["'](?!https?:\/\/)(?!\/)((?:\.\/|\.\.\/)*)?([^"']+)["']/g, 
        (match, prefix, path) => {
          const newUrl = getBackendUrl(`/media/reports/task_${taskId}/reports/${path}`);
          console.log(`href路径替换: ${match} -> href="${newUrl}"`);
          return `href="${newUrl}"`;
        }
      );
      
      console.log('相对路径替换完成');
    }
    
    htmlReportContent.value = reportContent || `<div class="error-message">
      <h3>无法加载报告内容</h3>
      <p>请检查报告是否存在或稍后重试</p>
    </div>`;
    
  } catch (error) {
    console.error('加载HTML报告内容失败:', error);
    htmlReportContent.value = `<div class="error-message">
      <h3>加载报告失败</h3>
      <p>${error.message || '未知错误'}</p>
      <p>请检查网络连接或稍后重试</p>
    </div>`;
  } finally {
    htmlLoading.value = false;
  }
};

// 切换标签页
const switchTab = (tab) => {
  activeTab.value = tab
}

// 下载报告
const downloadReport = async (reportId) => {
  try {
    ElMessage.info('正在准备下载报告...')
    await downloadReportFile(reportId)
  } catch (error) {
    console.error('下载报告失败:', error)
    ElMessage.error('下载报告失败')
  }
}

// 关闭报告模态框
const closeLogModal = () => {
  logModalVisible.value = false
  currentReportTitle.value = ''
  currentReportId.value = null
  htmlReportContent.value = ''
}

// 保留原下载功能，但改名为downloadReportFile，以备不时之需
const downloadReportFile = async (reportId, existingResponse = null) => {
  try {
    const response = existingResponse || await reportService.download(reportId)
    
    // 创建一个Blob对象
    let blob
    if (response.data instanceof Blob) {
      // 如果已经是Blob对象，直接使用
      blob = response.data
    } else {
      // 否则创建一个新的Blob对象
      blob = new Blob([response.data], { type: response.headers['content-type'] })
    }
    
    // 创建一个临时URL
    const url = window.URL.createObjectURL(blob)
    
    // 创建一个临时链接并点击它来下载文件
    const link = document.createElement('a')
    link.href = url
    
    // 从Content-Disposition标头中提取文件名，如果没有则使用一个默认名称
    const contentDisposition = response.headers['content-disposition']
    let fileName = 'report.html'
    if (contentDisposition) {
      const fileNameMatch = contentDisposition.match(/filename="(.+)"/)
      if (fileNameMatch && fileNameMatch.length === 2) {
        fileName = fileNameMatch[1]
      }
    }
    
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    
    // 清理
    link.remove()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('报告下载成功')
  } catch (error) {
    console.error('下载报告失败:', error)
    ElMessage.error('下载报告失败')
  }
}

const deleteReport = async (reportId) => {
  try {
    await ElMessageBox.confirm('确定要删除此报告吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await reportService.delete(reportId)
    ElMessage.success('报告删除成功')
    await fetchReports()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除报告失败:', error)
      ElMessage.error('删除报告失败')
    }
  }
}

const logout = () => {
  authStore.logout()
  router.push('/login')
}

const navigateTo = (path) => {
  router.push(path)
}

const resetSearch = () => {
  searchParams.taskId = ''
  searchParams.taskName = ''
  searchParams.algorithmName = ''
  
  // 重置后通知搜索状态已更新
  debounceSearch()
  ElMessage.success('已重置搜索条件')
}

// 添加即时搜索
const activeSearch = ref(false)
const debounceSearch = () => {
  activeSearch.value = true
  // 显示搜索正在生效
  if (searchParams.taskId || searchParams.taskName || searchParams.algorithmName) {
    console.log('搜索条件已更新，正在过滤结果')
  }
}

// 根据搜索条件过滤报告数据
const filteredReports = computed(() => {
  if (!searchParams.taskId && !searchParams.taskName && !searchParams.algorithmName) {
    return reports.value
  }
  
  return reports.value.filter(report => {
    let matches = true
    if (searchParams.taskId && !String(report.task_id).includes(searchParams.taskId)) {
      matches = false
    }
    if (searchParams.taskName && !(report.task_name || '').toLowerCase().includes(searchParams.taskName.toLowerCase())) {
      matches = false
    }
    if (searchParams.algorithmName) {
      // 获取报告所有算法名称
      const algorithmNames = getAlgorithmNames(report);
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

// 添加检查缺失报告功能
const checkAllReports = async () => {
  try {
    loading.value = true
    ElMessage.info('正在检查缺失报告，请稍候...')
    const response = await reportService.checkAllReports()
    ElMessage.success(response.data.message || '报告检查完成')
    // 重新加载报告列表
    await fetchReports()
  } catch (error) {
    console.error('检查报告失败:', error)
    ElMessage.error('检查报告失败: ' + (error.response?.data?.error || error.message || '未知错误'))
  } finally {
    loading.value = false
  }
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
        <div class="nav-item active" @click="navigateTo('/reports')">
          <span class="nav-icon">📝</span>
          <span class="nav-text">报告管理</span>
        </div>
      </div>
      
      <div class="dashboard-main">
        <div class="page-header">
          <h2>报告管理</h2>
          <!-- 添加检查缺失报告按钮 -->
          <div class="report-actions">
            <button class="check-reports-button" @click="checkAllReports">
              检查缺失报告
            </button>
          </div>
        </div>
        
        <!-- 搜索筛选区 -->
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
        
        <div v-else-if="reports.length === 0" class="empty-message">
          暂无报告，请先创建任务并等待处理完成
        </div>
        
        <div v-else class="report-list-container">
          <table class="report-table">
            <thead>
              <tr>
                <th class="task-id-column">任务ID</th>
                <th class="report-name">任务名称</th>
                <th>算法</th>
                <th>图片数量</th>
                <th>状态</th>
                <th>生成时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="report in filteredReports" 
                :key="report.id"
                class="report-row"
                :class="{ 'highlight-row': highlightedTaskId && String(report.task_id) === String(highlightedTaskId) }"
                :data-task-id="report.task_id"
              >
                <td class="task-id-column">{{ report.task_id }}</td>
                <td class="report-name">{{ report.task_name }}</td>
                <td class="algorithm-cell">
                  <div 
                    class="algorithm-badge"
                    @click.stop="viewReportLog(report.id, report.task_name || report.title)"
                    title="点击查看所有算法"
                  >
                    {{ getSelectedAlgorithmsFromReport(report).length }}个
                    <span class="algorithm-tags">
                      <span 
                        v-for="(id, index) in getSelectedAlgorithmsFromReport(report).split('')" 
                        :key="index"
                        class="algorithm-mini-tag"
                        :style="{ backgroundColor: getAlgorithmColor(id) }"
                      ></span>
                    </span>
                  </div>
                </td>
                <td class="images-cell">
                  <div class="image-count">
                    {{ report.task_images ? report.task_images.length : '未知' }}张
                  </div>
                </td>
                <td>
                  <span class="status-badge status-completed">已生成</span>
                </td>
                <td>{{ new Date(report.generated_at).toLocaleString() }}</td>
                <td class="actions-cell">
                  <button class="view-button" @click="viewReportLog(report.id, report.task_name || report.title)" title="查看详细日志">
                    📝 日志
                  </button>
                  <button class="view-button" @click="downloadReport(report.id)" title="下载报告">
                    📥 下载
                  </button>
                  <button class="delete-button" @click="deleteReport(report.id)">
                    删除
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    
    <!-- 日志查看模态框 -->
    <div v-if="logModalVisible" class="log-modal-overlay" @click.self="closeLogModal">
      <div class="log-modal">
        <div class="log-modal-header">
          <h3>{{ currentReportTitle || '报告详情' }}</h3>
          <div class="header-actions">
            <button class="download-button" @click="downloadReport(currentReportId)" title="下载完整报告">
              <i class="el-icon-download"></i> 下载
            </button>
            <button class="close-button" @click="closeLogModal">×</button>
          </div>
        </div>
        
        <!-- 标签页导航 -->
        <div class="tabs-header">
          <div 
            class="tab-item active"
          >
            HTML报告
          </div>
        </div>
        
        <div class="log-modal-body">
          <!-- HTML报告内容 -->
          <div>
            <div v-if="htmlLoading" class="log-loading">
              <div class="loading-spinner"></div>
              <div>加载中...</div>
            </div>
            <div v-else>
              <!-- 算法选择器 -->
              <div class="algorithm-selector">
                <div class="algorithm-buttons">
                  <button 
                    class="algorithm-button" 
                    :class="{ 'active': currentAlgorithm === 'all' }"
                    @click="switchAlgorithm('all')"
                  >
                    综合报告
                  </button>
                  <button 
                    class="algorithm-button" 
                    :class="{ 'active': currentAlgorithm === 'algorithm1' }"
                    @click="switchAlgorithm('algorithm1')"
                  >
                    图像准确度AI检测
                  </button>
                  <button 
                    class="algorithm-button" 
                    :class="{ 'active': currentAlgorithm === 'algorithm2' }"
                    @click="switchAlgorithm('algorithm2')"
                  >
                    图像质量AI检测
                  </button>
                  <button 
                    class="algorithm-button" 
                    :class="{ 'active': currentAlgorithm === 'algorithm3' }"
                    @click="switchAlgorithm('algorithm3')"
                  >
                    图像纹理质量AI检测
                  </button>
                  <button 
                    class="algorithm-button" 
                    :class="{ 'active': currentAlgorithm === 'algorithm4' }"
                    @click="switchAlgorithm('algorithm4')"
                  >
                    清晰度AI检测
                  </button>
                </div>
              </div>
              <div class="html-report-content">
                <iframe 
                  v-if="htmlReportContent" 
                  class="report-iframe" 
                  :srcdoc="htmlReportContent" 
                  frameborder="0"
                ></iframe>
                <div v-else class="error-message">
                  无法加载HTML报告内容
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="log-modal-footer">
          <button class="close-button" @click="closeLogModal">关闭</button>
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

/* 搜索筛选区样式 */
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

/* 添加检查报告按钮样式 */
.report-actions {
  display: flex;
  gap: 12px;
}

.check-reports-button {
  background-color: #52c41a;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  transition: background-color 0.3s;
}

.check-reports-button:hover {
  background-color: #389e0d;
}

/* 列表样式 */
.report-list-container {
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
  overflow: hidden;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
}

.report-table th {
  background-color: #fafafa;
  padding: 12px 16px;
  text-align: left;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  border-bottom: 1px solid #f0f0f0;
}

.report-table td {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.task-id-column {
  text-align: center;
  font-weight: 500;
  width: 80px;
}

.report-name {
  font-weight: 500;
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.9em;
  font-weight: 500;
}

.status-completed {
  background-color: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.actions-cell {
  white-space: nowrap;
  display: flex;
  gap: 8px;
}

.view-button {
  background-color: #1890ff;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.delete-button {
  background-color: #f5222d;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

/* 日志模态框样式 */
.log-modal-overlay {
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

.log-modal {
  background-color: #161b22;
  border-radius: 8px;
  width: 90%;
  max-width: 1200px;
  height: 85%;
  max-height: 900px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}

.log-modal-header {
  background-color: #0d1117;
  border-bottom: 1px solid #30363d;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #e6edf3;
}

/* 标签页样式 */
.tabs-header {
  display: flex;
  background-color: #0d1117;
  border-bottom: 1px solid #30363d;
}

.tab-item {
  padding: 12px 20px;
  color: #8b949e;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
  position: relative;
}

.tab-item:hover {
  color: #e6edf3;
}

.tab-item.active {
  color: #e6edf3;
  font-weight: 500;
}

.tab-item.active:after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background-color: #58a6ff;
}

.log-modal-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  position: relative;
  background-color: #0d1117;
}

.log-content {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-x: auto;
  padding: 15px;
  background-color: #0d1117;
  color: #e6edf3;
  border-radius: 6px;
  max-height: 70vh;
  overflow-y: auto;
  border: 1px solid #30363d;
}

/* HTML报告内容样式 */
.html-report-content {
  height: 100%;
  min-height: 500px;
}

.report-iframe {
  width: 100%;
  height: 70vh;
  border: none;
  background-color: white;
  border-radius: 6px;
}

.error-message {
  padding: 20px;
  text-align: center;
  color: #f85149;
  background-color: rgba(248, 81, 73, 0.1);
  border: 1px solid rgba(248, 81, 73, 0.2);
  border-radius: 6px;
  margin: 20px 0;
}

.log-content span.command {
  color: #7ee787;
  font-weight: bold;
}

.log-content span.error {
  color: #f85149;
  font-weight: bold;
}

.log-content span.warning {
  color: #f0883e;
}

.log-content span.info {
  color: #58a6ff;
}

.log-content span.success {
  color: #3fb950;
  font-weight: bold;
}

.log-content span.task-id {
  color: #d2a8ff;
  font-weight: bold;
}

.log-content span.timestamp {
  color: #8b949e;
}

.log-content span.prompt {
  color: #ff7b72;
  font-weight: bold;
}

.has-horizontal-scroll {
  white-space: pre !important;
}

.log-loading {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  gap: 16px;
  color: #8c8c8c;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.log-modal-footer {
  padding: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.close-button {
  background-color: transparent;
  border: 1px solid #d9d9d9;
  color: rgba(0, 0, 0, 0.65);
  padding: 6px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.log-modal-header .close-button {
  background: transparent;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #8c8c8c;
  padding: 0;
}

.highlight-row {
  background-color: rgba(24, 144, 255, 0.1);
  animation: highlight-pulse 2s ease-in-out 1;
}

@keyframes highlight-pulse {
  0%, 100% {
    background-color: rgba(24, 144, 255, 0.1);
  }
  50% {
    background-color: rgba(24, 144, 255, 0.3);
  }
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.copy-button, .download-button {
  background-color: transparent;
  border: 1px solid #58a6ff;
  color: #58a6ff;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  transition: all 0.2s;
}

.copy-button:hover, .download-button:hover {
  background-color: rgba(88, 166, 255, 0.1);
}

.copy-button i, .download-button i {
  font-size: 14px;
}

/* 这部分为动态生成的内容设置样式 */
:deep(.error) {
  color: #ff4d4f;
  font-weight: bold;
}

:deep(.warning) {
  color: #faad14;
  font-weight: bold;
}

:deep(.info) {
  color: #1890ff;
}

:deep(.command) {
  color: #722ed1;
  background-color: #f9f9f9;
  padding: 2px 4px;
  border-radius: 3px;
}

:deep(.success) {
  color: #52c41a;
  font-weight: bold;
}

:deep(.task-id) {
  color: #eb2f96;
  font-weight: bold;
}

:deep(.timestamp) {
  color: #8c8c8c;
}

:deep(.prompt) {
  color: #389e0d;
}

:deep(.progress-update) {
  color: #13c2c2;
  font-weight: bold;
  background-color: #e6fffb;
  padding: 2px 4px;
  border-radius: 3px;
}

.algorithm-cell {
  width: 100px;
}

.algorithm-count {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  font-size: 14px;
}

.info-button {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #f0f0f0;
  border: 1px solid #ccc;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-button:hover {
  background: #e0e0e0;
}

/* 添加算法列表显示样式 */
.algorithm-info-section {
  margin-bottom: 16px;
}

.algorithm-info-title {
  font-weight: bold;
  margin-bottom: 8px;
}

.algorithm-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.algorithm-tag {
  padding: 4px 8px;
  border-radius: 4px;
  background-color: #f0f0f0;
  color: white;
  font-size: 12px;
  display: inline-block;
}

.images-cell {
  text-align: center;
}

.image-count {
  background-color: #f5f5f5;
  border-radius: 12px;
  padding: 2px 8px;
  font-size: 12px;
  display: inline-block;
}

.algorithm-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 12px;
  background-color: #f5f5f5;
  font-size: 12px;
  display: inline-flex;
}

.algorithm-mini-tag {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

/* 添加算法选择器样式 */
.algorithm-selector {
  margin-bottom: 16px;
  background-color: #1e2635;
  border-radius: 4px;
  padding: 10px;
  border: 1px solid #30363d;
}

.algorithm-title {
  font-weight: bold;
  margin-bottom: 8px;
  color: #e6edf3;
}

.algorithm-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.algorithm-button {
  background-color: transparent;
  border: 1px solid #30363d;
  color: #8b949e;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.algorithm-button:hover {
  background-color: rgba(56, 139, 253, 0.1);
  color: #58a6ff;
}

.algorithm-button.active {
  background-color: #1f6feb;
  color: white;
  border-color: #388bfd;
}
</style> 