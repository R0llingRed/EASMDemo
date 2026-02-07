<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'

import {
  API_BASE_URL_STORAGE,
  API_KEY_STORAGE,
  getErrorMessage,
} from '../api/client'
import { getHealth } from '../api/easm'

const ENV_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const form = reactive({
  apiBaseUrl: localStorage.getItem(API_BASE_URL_STORAGE) ?? ENV_BASE_URL,
  apiKey: localStorage.getItem(API_KEY_STORAGE) ?? '',
})

function save() {
  localStorage.setItem(API_BASE_URL_STORAGE, form.apiBaseUrl.trim())
  localStorage.setItem(API_KEY_STORAGE, form.apiKey.trim())
  ElMessage.success('设置已保存')
}

function reset() {
  localStorage.removeItem(API_BASE_URL_STORAGE)
  localStorage.removeItem(API_KEY_STORAGE)
  form.apiBaseUrl = ENV_BASE_URL
  form.apiKey = ''
  ElMessage.success('已恢复默认设置')
}

async function testConnection() {
  try {
    const health = await getHealth()
    if (health.status === 'ok') {
      ElMessage.success('连接成功，API 服务健康')
      return
    }
    ElMessage.warning(`连接返回异常状态：${health.status}`)
  } catch (error) {
    ElMessage.error(`连接失败：${getErrorMessage(error)}`)
  }
}
</script>

<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <h1 class="page-title">Settings</h1>
        <p class="page-subtitle">管理 API 地址、密钥和连通性测试</p>
      </div>
    </div>

    <el-card shadow="never" class="panel-card">
      <template #header><span>API 连接配置</span></template>
      <el-form label-width="120px" style="max-width: 720px">
        <el-form-item label="API Base URL">
          <el-input v-model="form.apiBaseUrl" placeholder="http://localhost:8000" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="form.apiKey"
            placeholder="X-API-Key"
            show-password
            type="password"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="save">保存</el-button>
          <el-button @click="testConnection">测试连通性</el-button>
          <el-button @click="reset">恢复默认</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
