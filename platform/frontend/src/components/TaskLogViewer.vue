<template>
  <div class="log-viewer">
    <div class="log-toolbar">
      <el-space>
        <el-tag type="warning" size="small">实时日志</el-tag>
        <el-switch v-model="autoScroll" active-text="自动滚动" inactive-text="" size="small" />
        <el-button size="small" text @click="clearLogs">清空</el-button>
        <el-button size="small" text @click="refreshLogs" :loading="loading">刷新</el-button>
      </el-space>
    </div>

    <div ref="logContainer" class="log-output" @scroll="handleScroll">
      <div v-for="(log, index) in logs" :key="index" :class="'log-line log-line-' + log.level.toLowerCase()">
        <span class="log-time">{{ formatTime(log.timestamp) }}</span>
        <span class="log-level">[{{ log.level }}]</span>
        <span class="log-msg">{{ log.message }}</span>
      </div>
      
      <div v-if="!logs.length && !loading" class="log-empty">
        {{ taskStatus === 'running' ? '等待输出...' : '暂无日志' }}
      </div>
    </div>

    <!-- 底部状态栏 -->
    <div class="log-footer" v-if="taskStatus">
      <el-space>
        <el-tag :type="statusType(taskStatus)" size="small">{{ statusText(taskStatus) }}</el-tag>
        <span v-if="duration" style="font-size:12px;color:#909399;">耗时: {{ duration.toFixed(1) }}s</span>
        <span v-if="resultSummary?.total" style="font-size:12px;">
          结果:
          <span class="status-passed">{{ resultSummary.passed }} 通过</span>,
          <span class="status-failed">{{ resultSummary.failed }} 失败</span>
        </span>
      </el-space>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'

const props = defineProps({
  taskId: [String, Number]
})

const logs = ref([])
const loading = ref(false)
const autoScroll = ref(true)
const logContainer = ref(null)

const taskStatus = ref('')
const duration = ref(0)
const resultSummary = ref(null)

let pollTimer = null

// 格式化时间
const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleTimeString('zh-CN') + '.' + String(new Date(t).getMilliseconds()).padStart(3,'0')
}

// 处理滚动
const handleScroll = () => {
  if (!logContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = logContainer.value
  autoScroll.value = scrollHeight - scrollTop - clientHeight < 50
}

// 加载日志
const loadLogs = async () => {
  if (!props.taskId) return
  
  loading.value = true
  try {
    const res = await axios.get(`/api/tasks/${props.taskId}/output/`)
    
    if (res.data.logs) {
      logs.value = res.data.logs.reverse() // 最新的在前
    }
    
    taskStatus.value = res.data.status || ''
    duration.value = res.data.duration || 0
    resultSummary.value = res.data.result_summary || null
    
    // 自动滚动到底部
    if (autoScroll.value) {
      await nextTick()
      if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
    
  } catch (e) {}
  finally { loading.value = false }
}

// 刷新
const refreshLogs = () => loadLogs()

// 清空
const clearLogs = () => { logs.value = [] }

// 状态映射
const statusType = s => ({ completed:'success', failed:'danger', running:'warning', cancelled:'info', pending:'info', timeout:'danger'}[s] || 'info')
const statusText = s => ({ completed:'已完成', failed:'失败', running:'运行中...', cancelled:'已取消', pending:'等待中', timeout:'超时'}[s] || s)

// 监听 taskId 变化
watch(() => props.taskId, () => {
  clearLogs()
  loadLogs()
}, { immediate: true })

// 定时刷新（任务运行中时）
onMounted(() => {
  pollTimer = setInterval(() => {
    if (taskStatus.value === 'running') loadLogs()
  }, 1500)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.log-viewer { display:flex; flex-direction:column; height:100%; }

.log-toolbar {
  padding: 10px 14px;
  background: #f8fafc;
  border-bottom: 1px solid #ebeef5;
  border-radius: 4px 4px 0 0;
}

.log-output {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  font-family: 'Fira Code', Consolas, Monaco, monospace;
  font-size: 13px;
  line-height: 1.7;
  max-height: calc(70vh - 140px);
  min-height: 200px;
}

.log-line { white-space: pre-wrap; word-break: break-all; padding: 2px 0; }
.log-time { color:#64748b; margin-right:6px; font-size:11px; }
.log-level { font-weight:600; margin-right:8px; font-size:11px; }
.log-msg { color:#e2e8f0; }

.log-empty { color:#64748b; text-align:center; padding:40px; }

.log-footer {
  padding: 10px 16px;
  background: #f8fafc;
  border-top: 1px solid #ebeef5;
  border-radius: 0 0 4px 4px;
}
</style>
