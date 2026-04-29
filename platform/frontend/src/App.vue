<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="logo" @click="$router.push('/')">
          <span class="logo-icon">🧪</span>
          <span class="logo-text">WebAuto 测试平台</span>
        </div>
        <el-menu
          mode="horizontal"
          :default-active="currentRoute"
          :ellipsis="false"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/">
            <el-icon><DataAnalysis /></el-icon>
            工作台
          </el-menu-item>
          <el-menu-item index="/cases">
            <el-icon><Document /></el-icon>
            用例管理
          </el-menu-item>
          <el-menu-item index="/tasks">
            <el-icon><VideoPlay /></el-icon>
            执行任务
          </el-menu-item>
          <el-menu-item index="/reports">
            <el-icon><Files /></el-icon>
            测试报告
          </el-menu-item>
          <el-menu-item index="/traces">
            <el-icon><Film /></el-icon>
            Trace查看
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            设置
          </el-menu-item>
        </el-menu>

        <!-- 右侧状态 -->
        <div class="header-right">
          <el-badge :value="runningCount" :hidden="runningCount === 0" type="warning">
            <el-tag :type="runningCount > 0 ? 'warning' : 'success'" effect="dark">
              {{ runningCount > 0 ? `${runningCount} 个运行中` : '空闲' }}
            </el-tag>
          </el-badge>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const router = useRouter()
const route = useRoute()
const currentRoute = ref(route.path)
const runningCount = ref(0)

// 轮询运行中的任务数量
let pollingTimer = null

const fetchRunningCount = async () => {
  try {
    const res = await fetch('/api/tasks/running/')
    if (res.ok) {
      const data = await res.json()
      runningCount.value = data.length || data.count || 0
    }
  } catch (e) {
    // 忽略错误
  }
}

onMounted(() => {
  fetchRunningCount()
  pollingTimer = setInterval(fetchRunningCount, 5000) // 每5秒刷新
})

onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer)
})

const handleMenuSelect = (index) => {
  currentRoute.value = index
  router.push(index)
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #06b6d4 100%);
  padding: 0 24px;
  height: 60px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #fff;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
}

.header .el-menu {
  background: transparent !important;
  border-bottom: none !important;
  margin-left: 40px;
}

.header :deep(.el-menu-item) {
  color: rgba(255,255,255,0.85) !important;
  font-weight: 500;
  border-bottom: none !important;
  padding: 0 16px;
}

.header :deep(.el-menu-item:hover),
.header :deep(.el-menu-item.is-active) {
  color: #fff !important;
  background: rgba(255,255,255,0.15) !important;
  border-radius: 6px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  padding: 20px;
}
</style>
