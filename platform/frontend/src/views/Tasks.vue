<template>
  <div class="tasks-page">
    <!-- 快速执行面板 -->
    <el-card class="quick-run-card">
      <template #header>
        <span>⚡ 快速创建任务</span>
      </template>
      <el-form :model="taskForm" label-width="100px" inline>
        <el-form-item label="任务名称">
          <el-input v-model="taskForm.name" placeholder="输入任务名称" style="width:220px;" />
        </el-form-item>
        <el-form-item label="执行范围">
          <el-select v-model="taskForm.scope" style="width:160px;">
            <el-option label="全部用例" value="all" />
            <el-option label="冒烟测试" value="smoke" />
            <el-option label="回归测试" value="regression" />
            <el-option label="仅UI测试" value="ui_only" />
            <el-option label="仅API测试" value="api_only" />
          </el-select>
        </el-form-item>
        <el-form-item label="并行">
          <el-switch v-model="taskForm.parallel" active-text="开" inactive-text="关" />
        </el-form-item>
        <el-form-item label="并行数" v-show="taskForm.parallel">
          <el-input-number v-model="taskForm.workers" :min="1" :max="8" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="VideoPlay" @click="createAndRun">立即执行</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 运行中的任务 -->
    <template v-if="runningTasks.length">
      <h3 style="margin:20px 0 12px;">🔴 正在运行 ({{ runningTasks.length }})</h3>
      <el-row :gutter="16">
        <el-col :span="12" v-for="task in runningTasks" :key="task.id">
          <el-card class="running-task-card">
            <div class="running-header">
              <span>{{ task.name }}</span>
              <el-button text type="danger" size="small" @click="stopTask(task)">停止</el-button>
            </div>
            <el-progress 
              :percentage="calcProgress(task)" 
              :status="'warning'" 
              :stroke-width="12"
              style="margin:12px 0;"
            />
            <div class="running-actions">
              <el-button size="small" @click="showTaskLog(task)">查看日志</el-button>
              <el-tag type="warning" size="small">{{ formatTime(task.started_at) }}</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- 历史任务列表 -->
    <h3 style="margin:24px 0 12px;">📋 执行历史</h3>
    <el-card>
      <el-table :data="historyTasks" stripe v-loading="loadingHistory">
        <el-table-column prop="name" label="任务名称" min-width="200">
          <template #default="{ row }">
            <el-link @click="showTaskDetail(row)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="结果" width="180" align="center">
          <template #default="{ row }">
            <template v-if="row.result_summary?.total">
              <el-progress 
                :percentage="row.pass_rate || 0"
                :color="row.pass_rate >= 80 ? '#10b981' : '#ef4444'"
                :stroke-width="8"
                style="width:120px;"
              >
                <span style="font-size:12px;">{{ row.result_summary.passed }}/{{ row.result_summary.total }}</span>
              </el-progress>
            </template>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="80" align="center">
          <template #default="{ row }">{{ row.duration ? row.duration.toFixed(1) + 's' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="170" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button v-if="row.allure_report_path" text type="primary" size="small" @click="viewReport(row)">报告</el-button>
              <el-button text type="info" size="small" @click="showTaskLog(row)">日志</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top:16px;text-align:center;">
        <el-pagination
          layout="prev, pager, next"
          :total="totalCount"
          :current-page="currentPage"
          :page-size="pageSize"
          @current-change="loadHistory"
          small
        />
      </div>
    </el-card>

    <!-- 任务日志对话框 -->
    <el-dialog v-model="showLogDialog" :title="`任务日志 - ${logTask?.name}`" width="75%" top="5vh" destroy-on-close>
      <TaskLogViewer :task-id="logTask?.id" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import TaskLogViewer from '../components/TaskLogViewer.vue'

const taskForm = ref({
  name: '',
  scope: 'all',
  parallel: false,
  workers: 2,
})

const loadingHistory = ref(false)
const runningTasks = ref([])
const historyTasks = ref([])
const currentPage = ref(1)
const pageSize = ref(15)
const totalCount = ref(0)

// 日志对话框
const showLogDialog = ref(false)
const logTask = ref(null)

let pollTimer = null

// 创建并立即执行
const createAndRun = async () => {
  const scopeConfig = {
    all: {},
    smoke: { marker: 'smoke' },
    regression: { marker: 'regression' },
    ui_only: { marker: 'ui' },
    api_only: { marker: 'api' }
  }

  try {
    await axios.post('/api/tasks/run_quick/', {
      name: taskForm.value.name || `快速测试_${new Date().toLocaleTimeString()}`,
      ...scopeConfig[taskForm.value.scope],
      parallel: taskForm.value.parallel,
      workers: taskForm.value.workers ? taskForm.value.workers : undefined,
    })
    
    ElMessage.success('任务已创建并开始执行')
    taskForm.value.name = ''
    await loadRunning()
  } catch (e) {
    ElMessage.error('创建失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 加载运行中任务
const loadRunning = async () => {
  try {
    const res = await axios.get('/api/tasks/running/')
    runningTasks.value = res.data.results || res.data || []
  } catch (e) {}
}

// 加载历史记录
const loadHistory = async (page = 1) => {
  loadingHistory.value = true
  currentPage.value = page
  try {
    const res = await axios.get(`/api/tasks/history/?limit=${pageSize.value}&offset=${(page-1)*pageSize.value}`)
    historyTasks.value = res.data
    totalCount.value = Array.isArray(res.data) ? res.data.length : (res.data.count || 0)
  } catch (e) {}
  finally { loadingHistory.value = false }
}

// 停止任务
const stopTask = async (task) => {
  try {
    await axios.post(`/api/tasks/${task.id}/stop/`)
    ElMessage.info('已发送停止指令')
    setTimeout(loadRunning, 2000)
  } catch (e) {}
}

// 查看报告
const viewReport = (task) => window.open('/allure/', '_blank')

// 显示日志
const showTaskLog = (task) => { logTask.value = task; showLogDialog.value = true }

// 显示详情
const showTaskDetail = (row) => { /* 可扩展 */ }

// 计算进度（模拟）
const calcProgress = (task) => {
  if (!task.started_at) return 0
  const elapsed = (Date.now() - new Date(task.started_at).getTime()) / 1000
  return Math.min(95, Math.round(elapsed / 5)) // 每5秒增加1%，最大95%
}

// 格式化时间
const formatTime = (t) => t ? new Date(t).toLocaleTimeString() : '-'

// 状态映射
const statusType = s => ({ completed:'success', failed:'danger', running:'warning', cancelled:'info', pending:'info', timeout:'danger'}[s])
const statusText = s => ({ completed:'已完成', failed:'失败', running:'运行中', cancelled:'已取消', pending:'等待中', timeout:'超时'}[s])

// 定时刷新
onMounted(() => {
  loadRunning()
  loadHistory()
  pollTimer = setInterval(loadRunning, 5000)
})

onUnmounted(() => { if(pollTimer) clearInterval(pollTimer) })
</script>

<style scoped>
.quick-run-card { margin-bottom: 16px; }
.running-task-card { background: #fffbeb; border-color: #fde68a; }
.running-header { display:flex; justify-content:space-between; align-items:center; font-weight:600; }
.running-actions { display:flex; justify-content:space-between; align-items:center; }
</style>
