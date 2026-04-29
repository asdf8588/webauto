<template>
  <div class="traces-page">
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span>🎬 Playwright Trace 文件</span>
          <el-button icon="Refresh" @click="loadTraces">刷新</el-button>
        </div>
      </template>

      <el-table :data="traces" stripe v-loading="loading" empty-text="暂无 Trace 文件，执行 UI 测试后会自动生成">
        <el-table-column prop="filename" label="文件名" min-width="200">
          <template #default="{ row }">
            <el-link type="primary">{{ row.filename }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="filesize_display" label="大小" width="100" align="center" />
        <el-table-column prop="modified_time" label="修改时间" width="180" align="center">
          <template #default="{ row }">{{ formatTime(row.modified_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button text type="primary" size="small" @click="viewTrace(row)">查看</el-button>
              <el-button text type="info" size="small" @click="downloadTrace(row)">下载</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Trace 查看器对话框 -->
    <el-dialog v-model="showViewerDialog" :title="`Trace 查看 - ${currentTrace?.filename}`" width="90%" top="3vh">
      <div class="trace-viewer-container">
        <iframe 
          v-if="currentTrace"
          :src="`/api/reports/traces/${currentTrace.filename}/download/`"
          frameborder="0"
          class="trace-iframe"
        ></iframe>
        
        <!-- 提示信息 -->
        <div class="trace-hint">
          <el-alert 
            title="提示" 
            description="Playwright Trace 需要在支持的环境中查看。如果无法正常显示，请下载后使用命令: playwright show-trace trace_xxx.zip"
            type="info"
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(false)
const traces = ref([])
const showViewerDialog = ref(false)
const currentTrace = ref(null)

// 加载 trace 列表
const loadTraces = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/reports/traces/')
    traces.value = res.data
  } catch (e) {
    console.error('加载 traces 失败:', e)
  } finally {
    loading.value = false
  }
}

// 查看 trace
const viewTrace = (row) => {
  currentTrace.value = row
  showViewerDialog.value = true
}

// 下载 trace
const downloadTrace = async (row) => {
  window.open(`/api/reports/traces/${row.filename}/download/`, '_blank')
}

const formatTime = (ts) => {
  if (!ts) return '-'
  return new Date(ts * 1000).toLocaleString('zh-CN')
}

onMounted(() => { loadTraces() })
</script>

<style scoped>
.trace-viewer-container {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.trace-iframe {
  flex: 1;
  border-radius: 8px;
  background: #1e293b;
}
.trace-hint { flex-shrink: 0; }
</style>
