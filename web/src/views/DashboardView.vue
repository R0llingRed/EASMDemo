<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import {
  getVulnerabilityStats,
  listApiRisks,
  listAssets,
  listScans,
  type ScanTask,
} from '../api/easm'
import { getErrorMessage } from '../api/client'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
const loading = ref(false)
const latestTasks = ref<ScanTask[]>([])

const stats = reactive({
  totalAssets: 0,
  criticalRisks: 0,
  runningTasks: 0,
  vulnerabilities: 0,
})

function resetStats() {
  stats.totalAssets = 0
  stats.criticalRisks = 0
  stats.runningTasks = 0
  stats.vulnerabilities = 0
  latestTasks.value = []
}

async function loadDashboard() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    resetStats()
    return
  }

  loading.value = true
  try {
    const [assetsPage, vulnStats, apiRiskPage, pendingPage, runningPage, scansPage] =
      await Promise.all([
        listAssets(projectId, { offset: 0, limit: 1 }),
        getVulnerabilityStats(projectId),
        listApiRisks(projectId, { severity: 'critical', limit: 1 }),
        listScans(projectId, { status: 'pending', limit: 1 }),
        listScans(projectId, { status: 'running', limit: 1 }),
        listScans(projectId, { skip: 0, limit: 5 }),
      ])

    stats.totalAssets = assetsPage.total
    stats.criticalRisks = vulnStats.critical + apiRiskPage.total
    stats.runningTasks = pendingPage.total + runningPage.total
    stats.vulnerabilities = vulnStats.total
    latestTasks.value = scansPage.items
  } catch (error) {
    ElMessage.error(`看板数据加载失败：${getErrorMessage(error)}`)
    resetStats()
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await workspace.loadProjects()
  await loadDashboard()
})

watch(
  () => workspace.selectedProjectId,
  async () => {
    await loadDashboard()
  },
)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">Dashboard</h1>
      <el-tag v-if="workspace.selectedProject">{{ workspace.selectedProject.name }}</el-tag>
      <el-tag type="warning" v-else>请先创建并选择项目</el-tag>
    </div>

    <el-row :gutter="16" v-loading="loading">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="text-sm text-gray-500 mb-2">资产总数</div>
          <div class="text-3xl font-bold text-blue-600">{{ stats.totalAssets }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="text-sm text-gray-500 mb-2">严重风险</div>
          <div class="text-3xl font-bold text-red-600">{{ stats.criticalRisks }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="text-sm text-gray-500 mb-2">运行中/待执行任务</div>
          <div class="text-3xl font-bold text-green-600">{{ stats.runningTasks }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="text-sm text-gray-500 mb-2">漏洞总数</div>
          <div class="text-3xl font-bold text-amber-600">{{ stats.vulnerabilities }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <span>最近扫描任务</span>
      </template>
      <el-empty v-if="!latestTasks.length" description="暂无任务数据" />
      <el-table v-else :data="latestTasks" size="small">
        <el-table-column prop="task_type" label="类型" min-width="140" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="priority" label="优先级" width="100" />
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
      </el-table>
    </el-card>
  </div>
</template>
