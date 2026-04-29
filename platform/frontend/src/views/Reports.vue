<template>
  <div class="reports-page">
    <el-row :gutter="20">
      <!-- 左侧：报告列表 -->
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>📋 报告历史</span>
          </template>
          
          <el-input placeholder="搜索报告..." clearable prefix-icon="Search" v-model="searchQuery" style="margin-bottom:12px;" />
          
          <div class="report-list" v-loading="loading">
            <div 
              v-for="report in filteredReports" 
              :key="report.id" 
              class="report-item" 
              :class="{ active: selectedReport?.id === report.id }"
              @click="selectReport(report)"
            >
              <div class="report-header">
                <span class="report-name">{{ report.name }}</span>
                <el-tag :type="report.pass_rate >= 90 ? 'success' : report.pass_rate >= 70 ? 'warning' : 'danger'" size="small" round>
                  {{ report.pass_rate }}%
                </el-tag>
              </div>
              <div class="report-meta">
                <span>✓{{ report.passed }} ✗{{ report.failed }} 共{{ report.total }}</span>
                <span class="report-time">{{ formatTime(report.created_at) }}</span>
              </div>
              <el-progress 
                :percentage="report.pass_rate" 
                :show-text="false"
                :stroke-width="6"
                :color="progressColor(report.pass_rate)"
                style="margin-top:8px;"
              />
            </div>

            <el-empty v-if="!filteredReports.length && !loading" description="暂无报告" :image-size="60" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：报告预览 -->
      <el-col :span="16">
        <el-card class="report-viewer-card">
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div>
                <span v-if="selectedReport">📊 {{ selectedReport.name }}</span>
                <span v-else>📊 Allure 报告查看器</span>
              </div>
              <el-space>
                <el-button-group v-if="selectedReport">
                  <el-button size="small" icon="RefreshRight" @click="refreshIframe">刷新</el-button>
                  <el-button size="small" icon="FullScreen" @click="openFull">全屏</el-button>
                </el-button-group>
              </el-space>
            </div>
          </template>
          
          <!-- 报告摘要 -->
          <div v-if="selectedReport" class="report-summary">
            <el-row :gutter="16">
              <el-col :span="6"><div class="summary-item success">✅ 通过: <b>{{ selectedReport.passed }}</b></div></el-col>
              <el-col :span="6"><div class="summary-item danger">❌ 失败: <b>{{ selectedReport.failed }}</b></div></el-col>
              <el-col :span="6"><div class="summary-item warning">⏭️ 跳过: <b>{{ selectedReport.skipped || 0 }}</b></div></el-col>
              <el-col :span="6"><div class="summary-item info">⏱️ 耗时: <b>{{ selectedReport.duration?.toFixed(1) || '-' }}s</b></div></el-col>
            </el-row>
          </div>

          <!-- iframe 报告 -->
          <div class="report-iframe-container" v-if="hasReport">
            <iframe 
              ref="reportFrame"
              src="/allure/" 
              frameborder="0"
              allow="autoplay"
            ></iframe>
          </div>
          
          <el-empty v-else description="暂无报告数据，请先执行测试生成报告"></el-empty>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(false)
const searchQuery = ref('')
const reports = ref([])
const selectedReport = ref(null)
const hasReport = ref(true)
const reportFrame = ref(null)

// 过滤后的报告
const filteredReports = computed(() => {
  if (!searchQuery.value) return reports.value
  return reports.value.filter(r =>
    r.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// 加载报告列表
const loadReports = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/reports/list-reports/')
    reports.value = res.data
    
    // 自动选择最新报告
    if (reports.value.length && !selectedReport.value) {
      selectReport(reports.value[0])
    }
  } catch (e) {
    console.error('加载报告失败:', e)
  } finally {
    loading.value = false
  }
}

// 选择报告
const selectReport = (report) => {
  selectedReport.value = report
  refreshIframe()
}

// 刷新 iframe
const refreshIframe = () => {
  if (reportFrame.value) {
    reportFrame.value.src = '/allure/?t=' + Date.now()
  }
}

// 全屏打开
const openFull = () => window.open('/allure/', '_blank')

// 辅助函数
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : ''
const progressColor = (rate) => rate >= 90 ? '#10b981' : rate >= 70 ? '#f59e0b' : '#ef4444'

onMounted(() => { loadReports() })
</script>

<style scoped>
.report-list {
  max-height: calc(100vh - 240px);
  overflow-y: auto;
}

.report-item {
  padding: 14px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.report-item:hover { border-color: #409eff; background: #f5f7fa; }
.report-item.active { border-color: #409eff; background: #ecf5ff; }

.report-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.report-name { font-weight:600; font-size:14px; flex:1;margin-right:8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.report-meta { display:flex; justify-content:space-between; color:#909399; font-size:12px; margin-bottom:4px; }
.report-time { color:#c0c4cc; }

.report-summary { padding-bottom:16px; border-bottom:1px solid #ebeef5; margin-bottom:12px; }
.summary-item { 
  padding:10px; 
  border-radius:6px; 
  text-align:center; 
  background:#f8fafc;
  font-size:13px;
}
.summary-item.success { background:#f0fdf4; color:#166534; }
.summary-item.danger { background:#fef2f2; color:#991b1b; }
.summary-item.warning { background:#fffbeb; color:#92400e; }
.summary-item.info { background:#f0f9ff; color:#075985; }
</style>
