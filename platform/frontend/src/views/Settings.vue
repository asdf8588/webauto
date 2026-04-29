<template>
  <div class="settings-page">
    <el-row :gutter="20">
      <!-- 基本设置 -->
      <el-col :span="12">
        <el-card>
          <template #header><span>⚙️ 基本设置</span></template>
          
          <el-form label-width="120px" style="max-width:500px;">
            <el-form-item label="项目路径">
              <el-input value="D:\pythonshiyan\webauto" disabled />
              <div style="color:#909399;font-size:12px;">WebAuto 项目根目录（自动检测）</div>
            </el-form-item>

            <el-form-item label="测试目录">
              <el-input value="tests/" disabled />
            </el-form-item>

            <el-form-item label="Allure 报告目录">
              <el-input value="allure-report/" disabled />
            </el-form-item>

            <el-form-item label="Trace 输出目录">
              <el-input value="test-results/" disabled />
            </el-form-item>
            
            <el-divider />

            <el-form-item label="默认浏览器">
              <el-select v-model="settings.defaultBrowser">
                <el-option label="Chromium" value="chromium" />
                <el-option label="Firefox" value="firefox" />
                <el-option label="WebKit" value="webkit" />
              </el-select>
            </el-form-item>

            <el-form-item label="默认超时(秒)">
              <el-input-number v-model="settings.timeout" :min="60" :max="3600" :step="60" />
            </el-form-item>

            <el-form-item label="">
              <el-button type="primary" @click="saveSettings">保存设置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 通知配置 -->
      <el-col :span="12">
        <el-card>
          <template #header><span>🔔 通知配置</span></template>
          
          <el-alert 
            title="企业微信 / 钉钉通知" 
            type="info" 
            :closable="false"
            show-icon
            style="margin-bottom:20px;"
            description="配置 Webhook 后，每次定时任务完成会自动发送测试结果通知。"
          />

          <el-form label-width="120px" style="max-width:500px;">
            <el-form-item label="启用通知">
              <el-switch v-model="notification.enabled" />
            </el-form-item>

            <el-form-item label="企业微信 Webhook">
              <el-input 
                v-model="notification.wecomWebhook" 
                placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
                type="password"
                show-password
              />
            </el-form-item>

            <el-form-item label="钉钉 Webhook">
              <el-input 
                v-model="notification.dingtalkWebhook" 
                placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx"
                type="password"
                show-password
              />
            </el-form-item>

            <el-form-item label="飞书 Webhook">
              <el-input 
                v-model="notification.feishuWebhook" 
                placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
                type="password"
                show-password
              />
            </el-form-item>

            <el-form-item label="">
              <el-button type="success" @click="testNotification" :disabled="!notification.enabled">
                发送测试通知
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统信息 -->
    <el-card style="margin-top:20px;">
      <template #header><span>ℹ️ 系统信息</span></template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="平台版本">WebAuto Test Platform v1.0.0</el-descriptions-item>
        <el-descriptions-item label="后端框架">Django + DRF</el-descriptions-item>
        <el-descriptions-item label="前端框架">Vue 3 + Element Plus</el-descriptions-item>
        <el-descriptions-item label="测试框架">pytest + Allure + Playwright</el-descriptions-item>
        <el-descriptions-item label="数据库">SQLite (开发环境)</el-descriptions-item>
        <el-descriptions-item label="Python 版本">{{ pythonVersion }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const settings = ref({
  defaultBrowser: 'chromium',
  timeout: 300,
})

const notification = ref({
  enabled: false,
  wecomWebhook: '',
  dingtalkWebhook: '',
  feishuWebhook: '',
})

const pythonVersion = ref('-')

// 保存设置
const saveSettings = () => {
  // 保存到 localStorage 或发到后端
  localStorage.setItem('webauto_settings', JSON.stringify(settings.value))
  localStorage.setItem('webauto_notification', JSON.stringify(notification.value))
  ElMessage.success('设置已保存')
}

// 加载已保存的设置
const loadSettings = () => {
  const savedSettings = localStorage.getItem('webauto_settings')
  if (savedSettings) Object.assign(settings.value, JSON.parse(savedSettings))

  const savedNotif = localStorage.getItem('webauto_notification')
  if (savedNotif) Object.assign(notification.value, JSON.parse(savedNotif))
}

// 测试通知
const testNotification = async () => {
  try {
    const res = await fetch('/api/settings/test-notification/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(notification.value)
    })
    
    if (res.ok) {
      ElMessage.success('测试通知已发送，请检查是否收到')
    } else {
      ElMessage.error('发送失败，请检查 Webhook 配置')
    }
  } catch (e) {
    ElMessage.error('请求失败: ' + e.message)
  }
}

onMounted(() => {
  loadSettings()
  
  // 获取 Python 版本（从后端 API 获取）
  fetch('/api/settings/system-info/')
    .then(r => r.json())
    .then(d => { if(d.python_version) pythonVersion.value = d.python_version })
    .catch(() => {})
})
</script>

<style scoped>
.settings-page .el-card { margin-bottom: 20px; }
</style>
