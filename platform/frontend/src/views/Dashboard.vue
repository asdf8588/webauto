<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6" v-for="(stat, index) in statsData.cases" :key="'case-' + index">
        <el-card shadow="hover" class="stat-card">
          <div :class="'stat-value stat-' + stat.color">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
      <el-col :span="6" v-for="(stat, index) in statsData.tasks" :key="'task-' + index">
        <el-card shadow="hover" class="stat-card">
          <div :class="'stat-value stat-' + stat.color">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 快速操作 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>⚡ 快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" size="large" @click="runQuickTest('all')" style="width:100%;margin-bottom:12px;">
              <el-icon><VideoPlay /></el-icon> 运行全部测试
            </el-button>
            <el-button type="success" size="large" @click="runQuickTest('smoke')" style="width:100%;margin-bottom:12px;">
              <el-icon><Aim /></el-icon> 运行冒烟测试
            </el-button>
            <el-button type="warning" size="large" @click="$router.push('/cases')" style="width:100%;">
              <el-icon><Refresh /></el-icon> 扫描用例目录
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 最近任务 -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span>📋 最近执行记录</span>
              <el-button text @click="$router.push('/tasks')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentTasks" stripe size="small" v-loading="loading">
            <el-table-column prop="name" label="任务名称" min-width="180" />
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="结果" width="150" align="center">
              <template #default="{ row }">
                <template v-if="row.result_summary">
                  <span class="status-passed">{{ row.result_summary.passed || 0 }} 通过</span>
                  /
                  <span class="status-failed">{{ row.result_summary.failed || 0 }} 失败</span>
                </template>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="completed_at" label="完成时间" width="170" />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button 
                  v-if="row.allure_report_path" 
                  text type="primary" 
                  size="small"
                  @click="viewReport(row)"
                >查看报告</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- Allure 报告预览 -->
    <el-card style="margin-top:20px;">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span>📊 最新报告预览</span>
          <el-button-group>
            <el-button type="primary" size="small" @click="$router.push('/reports')">查看完整报告</el-button>
            <el-button size="small" @click="refreshReport">刷新</el-button>
          </el-button-group>
        </div>
      </template>
      <div class="report-preview" v-if="hasReport">
        <iframe src="/allure/" frameborder="0" style="width:100%;height:500px;border-radius:8px;"></iframe>
      </div>
      <el-empty v-else description="暂无报告，请先运行测试"></el-empty>
    </el-card>

    <!-- 执行日志对话框 -->
    <el-dialog v-model="showLogDialog" :title="`执行日志 - ${currentTask?.name}`" width="70%" top="5vh">
      <TaskLogViewer :task-id="currentTask?.id" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import axios from 'axios'
import TaskLogViewer from '../components/TaskLogViewer.vue'

const loading = ref(false)
const showLogDialog = ref(false)
const currentTask = ref(null)
const hasReport = ref(true)

const statsData = reactive({
  cases: [
    { value: '-', label: '总用例数', color: 'blue' },
    { value: '-', label: '活跃用例', color: 'green' },
    { value: '-', label: 'UI 测试', color: 'purple' },
    { value: '-', label: 'API 测试', color: 'orange' }
  ],
  tasks: [
    { value: '-', label: '今日执行', color: 'cyan' },
    { value: '-', label: '成功次数', color: 'green' },
    { value: '-', label: '失败次数', color: 'red' },
    { value: '-', label: '通过率', color: 'blue' }
  ]
})

const recentTasks = ref([])

// 加载仪表盘数据
const loadDashboardData = async () => {
  loading.value = true
  try {
    const [dashboardRes, historyRes] = await Promise.all([
      axios.get('/api/reports/dashboard/'),
      axios.get('/api/tasks/history/?limit=10')
    ])

    // 用例统计
    const d = dashboardRes.data
    statsData.cases[0].value = d.cases?.total || 0
    statsData.cases[1].value = d.cases?.active || 0
    
    // 任务统计
    statsData.tasks[0].value = d.tasks?.today || 0
    statsData.tasks[1].value = d.tasks?.completed || 0
    statsData.tasks[2].value = d.tasks?.failed || 0

    // 获取用例类型统计
    try {
      const caseStatsRes = await axios.get('/api/cases/testcases/stats/')
      if (caseStatsRes.data.by_type) {
        statsData.cases[2].value = caseStatsRes.data.by_type.ui || 0
        statsData.cases[3].value = caseStatsRes.data.by_type.api || 0
      }
      
      // 计算通过率
      const total = (caseStatsRes.data.total || 1)
      const active = caseStatsRes.data.active || 0
      statsData.tasks[3].value = Math.round(active / total * 100) + '%'
    } catch(e) {}

    recentTasks.value = historyRes.data

  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 快速执行测试
const runQuickTest = async (type) => {
  try {
    await axios.post('/api/tasks/run_quick/', {
      marker: type === 'smoke' ? 'smoke' : '',
      name: type === 'smoke' ? '冒烟测试' : '全部测试'
    })
    
    ElMessage.success('任务已创建，正在执行...')
    setTimeout(loadDashboardData, 2000)
  } catch (e) {
    ElMessage.error('创建任务失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 查看报告
const viewReport = (task) => {
  window.open(`/allure/`, '_blank')
}

// 刷新报告
const refreshReport = () => {
  hasReport.value = false
  setTimeout(() => hasReport.value = true, 100)
}

// 状态映射
const statusType = (s) => ({ completed:'success', failed:'danger', running:'warning', cancelled:'info', pending:'info' }[s] || 'info')
const statusText = (s) => ({ completed:'已完成', failed:'失败', running:'运行中', cancelled:'已取消', pending:'等待中' }[s] || s)

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.stats-row .stat-card {
  cursor: default;
}
.stat-blue { color: #3b82f6; }
.stat-green { color: #10b981; }
.stat-red { color: #ef4444; }
.stat-orange { color: #f59e0b; }
.stat-purple { color: #8b5cf6; }
.stat-cyan { color: #06b6d4; }

.quick-actions {
  display: flex;
  flex-direction: column;
}

.report-preview {
  background: #f8fafc;
  border-radius: 8px;
  overflow: hidden;
}
</style>
