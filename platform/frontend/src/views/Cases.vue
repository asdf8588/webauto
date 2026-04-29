<template>
  <div class="cases-page">
    <!-- 工具栏 -->
    <el-card class="toolbar-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="18">
          <el-input
            v-model="searchQuery"
            placeholder="搜索用例名称、文件路径..."
            clearable
            prefix-icon="Search"
            style="max-width:300px;"
          />
          <el-select v-model="filterType" placeholder="类型" clearable style="margin-left:12px;width:120px;">
            <el-option label="UI 测试" value="ui" />
            <el-option label="API 测试" value="api" />
            <el-option label="E2E 测试" value="e2e" />
          </el-select>
          <el-select v-model="filterStatus" placeholder="状态" clearable style="margin-left:12px;width:120px;">
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
          </el-select>
          <el-select v-model="filterModule" placeholder="模块" clearable filterable style="margin-left:12px;width:160px;">
            <el-option v-for="m in modules" :key="m" :label="m" :value="m" />
          </el-select>
        </el-col>
        <el-col :span="6" style="text-align:right;">
          <el-button type="primary" icon="Refresh" @click="scanCases" :loading="scanning">扫描导入</el-button>
          <el-button type="success" icon="Plus" @click="showBatchRun">批量执行</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 统计信息 -->
    <el-row :gutter="16" style="margin-bottom:16px;" v-if="caseStats.total">
      <el-col :span="3"><el-tag effect="dark" round size="large">总计 {{ caseStats.total }}</el-tag></el-col>
      <el-col :span="3"><el-tag type="success" effect="dark" round size="large">活跃 {{ caseStats.active }}</el-tag></el-col>
      <el-col :span="3" v-for="(count, type) in caseStats.by_type" :key="type">
        <el-tag :type="typeColor(type)" round size="large">{{ typeName(type) }} {{ count }}</el-tag>
      </el-col>
    </el-row>

    <!-- 用例表格 -->
    <el-card>
      <el-table 
        :data="filteredCases" 
        stripe 
        v-loading="loading"
        @selection-change="handleSelectionChange"
        size="default"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="name" label="用例名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="showCaseDetail(row)">{{ row.name || row.test_id }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="case_type" label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="typeColor(row.case_type)" size="small">{{ row.type_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="priorityColor(row.priority)" size="small">{{ row.priority_display }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module" label="所属模块" min-width="140" show-overflow-tooltip />
        <el-table-column prop="file_path" label="文件路径" min-width="220" show-overflow-tooltip />
        <el-table-column prop="test_id" label="测试ID" width="160" show-overflow-tooltip />
        <el-table-column prop="tags" label="标签" width="140">
          <template #default="{ row }">
            <el-tag v-for="tag in (row.tags || [])" :key="tag" size="small" style="margin:2px;">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.status" active-value="active" inactive-value="inactive"
                       @change="toggleCaseStatus(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="runSingleCase(row)">执行</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div style="margin-top:16px;display:flex;justify-content:flex-end;">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="20"
          :total="filteredCases.length"
          layout="total, prev, pager, next"
          small
        />
      </div>
    </el-card>

    <!-- 用例详情对话框 -->
    <el-dialog v-model="showDetail" :title="selectedCase?.name" width="60%">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="名称">{{ selectedCase?.name }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ selectedCase?.type_display }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ selectedCase?.priority_display }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ selectedCase?.status_display }}</el-descriptions-item>
        <el-descriptions-item label="文件路径" :span="2">{{ selectedCase?.file_path }}</el-descriptions-item>
        <el-descriptions-item label="测试ID" :span="2"><code>{{ selectedCase?.full_path }}</code></el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ selectedCase?.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="函数文档" :span="2" v-if="selectedCase?.docstring">
          <pre style="white-space:pre-wrap;font-size:13px;">{{ selectedCase.docstring }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 批量执行对话框 -->
    <el-dialog v-model="showBatchDialog" title="批量执行测试" width="500px">
      <el-form label-width="100px">
        <el-form-item label="已选用例">
          <span>{{ selectedRows.length }} 个</span>
        </el-form-item>
        <el-form-item label="并行执行">
          <el-switch v-model="batchConfig.parallel" />
        </el-form-item>
        <el-form-item label="并行数" v-show="batchConfig.parallel">
          <el-input-number v-model="batchConfig.workers" :min="1" :max="8" />
        </el-form-item>
        <el-form-item label="标记过滤">
          <el-input v-model="batchConfig.marker" placeholder="如 smoke, regression" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBatchDialog=false">取消</el-button>
        <el-button type="primary" @click="confirmBatchRun" :disabled="!selectedRows.length">确认执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(false)
const scanning = ref(false)
const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('')
const filterModule = ref('')
const currentPage = ref(1)
const allCases = ref([])
const selectedRows = ref([])
const caseStats = ref({})
const modules = ref([])

// 详情对话框
const showDetail = ref(false)
const selectedCase = ref(null)

// 批量执行对话框
const showBatchDialog = ref(false)
const batchConfig = ref({ parallel: false, workers: 2, marker: '' })

// 过滤后的用例
const filteredCases = computed(() => {
  let list = [...allCases.value]
  
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(c =>
      c.name.toLowerCase().includes(q) ||
      c.file_path.toLowerCase().includes(q) ||
      c.test_id.toLowerCase().includes(q)
    )
  }
  
  if (filterType.value) list = list.filter(c => c.case_type === filterType.value)
  if (filterStatus.value) list = list.filter(c => c.status === filterStatus.value)
  if (filterModule.value) list = list.filter(c => c.module.includes(filterModule.value))
  
  return list
})

// 加载用例列表
const loadCases = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/cases/testcases/', { params: { page_size: 9999 } })
    allCases.value = res.data.results || res.data
  } catch (e) {
    console.error('加载用例失败:', e)
  } finally {
    loading.value = false
  }
}

// 加载统计
const loadStats = async () => {
  try {
    const res = await axios.get('/api/cases/testcases/stats/')
    caseStats.value = res.data
    modules.value = res.data.modules || []
  } catch (e) {}
}

// 扫描导入用例
const scanCases = async () => {
  scanning.value = true
  try {
    const res = await axios.post('/api/cases/testcases/scan/')
    ElMessage.success(res.data.message)
    await loadCases()
    await loadStats()
  } catch (e) {
    ElMessage.error('扫描失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    scanning.value = false
  }
}

// 切换用例状态
const toggleCaseStatus = async (caseItem) => {
  try {
    await axios.post(`/api/cases/testcases/${caseItem.id}/toggle/`)
    ElMessage.success(`已${caseItem.status === 'active' ? '启用' : '禁用'}`)
  } catch (e) {}
}

// 显示用例详情
const showCaseDetail = (row) => {
  selectedCase.value = row
  showDetail.value = true
}

// 选择变化
const handleSelectionChange = (rows) => { selectedRows.value = rows }

// 单个执行
const runSingleCase = async (row) => {
  try {
    await axios.post('/api/tasks/run_quick/', {
      test_ids: [row.id],
      name: `执行 - ${row.name}`
    })
    ElMessage.success('已开始执行，请在"执行任务"页面查看进度')
  } catch (e) {
    ElMessage.error('执行失败')
  }
}

// 显示批量执行
const showBatchRun = () => {
  if (!selectedRows.value.length) {
    ElMessage.warning('请先选择要执行的用例')
    return
  }
  showBatchDialog.value = true
}

// 确认批量执行
const confirmBatchRun = async () => {
  try {
    await axios.post('/api/tasks/run_quick/', {
      test_ids: selectedRows.value.map(r => r.id),
      ...batchConfig.value,
      name: `批量执行 ${selectedRows.value.length} 个用例`
    })
    showBatchDialog.value = false
    ElMessage.success('批量任务已创建')
  } catch (e) {
    ElMessage.error('创建任务失败')
  }
}

// 辅助函数
const typeColor = (t) => ({ ui: '', api: 'success', e2e: 'warning' }[t])
const typeName = (t) => ({ ui: 'UI', api: 'API', e2e: 'E2E' }[t])
const priorityColor = (p) => ([ 'danger', 'danger', 'warning', 'info', 'info'][p])

onMounted(() => {
  loadCases()
  loadStats()
})
</script>

<style scoped>
.toolbar-card { margin-bottom: 16px; }
.toolbar-card :deep(.el-card__body) { padding: 14px; }
</style>
