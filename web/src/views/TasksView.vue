<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { createScan, listScans, startScan, type ScanTask } from '../api/easm'
import { getErrorMessage } from '../api/client'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()

const loading = ref(false)
const creating = ref(false)
const scans = ref<ScanTask[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const query = reactive({
  taskType: '',
  status: '',
})

const form = reactive({
  taskType: 'js_api_discovery',
  priority: 5,
  configJson: '{\n  "batch_size": 50\n}',
  autoStart: true,
})

const taskTypes = [
  'subdomain_scan',
  'dns_resolve',
  'port_scan',
  'http_probe',
  'fingerprint',
  'screenshot',
  'nuclei_scan',
  'xray_scan',
  'js_api_discovery',
]

function parseConfigJson() {
  if (!form.configJson.trim()) {
    return {}
  }
  return JSON.parse(form.configJson) as Record<string, unknown>
}

async function refreshScans() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    scans.value = []
    total.value = 0
    return
  }

  loading.value = true
  try {
    const page = await listScans(projectId, {
      task_type: query.taskType || undefined,
      status: query.status || undefined,
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    })
    scans.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(`任务加载失败：${getErrorMessage(error)}`)
  } finally {
    loading.value = false
  }
}

async function submitCreate() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    ElMessage.warning('请先选择项目')
    return
  }

  let config: Record<string, unknown>
  try {
    config = parseConfigJson()
  } catch {
    ElMessage.error('配置 JSON 格式不合法')
    return
  }

  creating.value = true
  try {
    const created = await createScan(projectId, {
      task_type: form.taskType,
      priority: form.priority,
      config,
    })

    if (form.autoStart) {
      await startScan(projectId, created.id)
      ElMessage.success('任务已创建并启动')
    } else {
      ElMessage.success('任务已创建')
    }

    currentPage.value = 1
    await refreshScans()
  } catch (error) {
    ElMessage.error(`任务创建失败：${getErrorMessage(error)}`)
  } finally {
    creating.value = false
  }
}

async function triggerStart(taskId: string) {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    return
  }
  try {
    await startScan(projectId, taskId)
    ElMessage.success('任务已启动')
    await refreshScans()
  } catch (error) {
    ElMessage.error(`启动失败：${getErrorMessage(error)}`)
  }
}

async function onFilterChange() {
  currentPage.value = 1
  await refreshScans()
}

async function onCurrentPageChange(page: number) {
  currentPage.value = page
  await refreshScans()
}

async function onPageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  await refreshScans()
}

onMounted(async () => {
  await workspace.loadProjects()
  await refreshScans()
})

watch(
  () => workspace.selectedProjectId,
  async () => {
    currentPage.value = 1
    await refreshScans()
  },
)
</script>

<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <h1 class="page-title">Tasks</h1>
        <p class="page-subtitle">创建并启动扫描任务，跟踪执行进度</p>
      </div>
      <div class="page-tools">
        <el-select
          v-model="query.taskType"
          clearable
          placeholder="任务类型"
          style="width: 180px"
          @change="onFilterChange"
        >
          <el-option v-for="item in taskTypes" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select
          v-model="query.status"
          clearable
          placeholder="状态"
          style="width: 130px"
          @change="onFilterChange"
        >
          <el-option label="pending" value="pending" />
          <el-option label="running" value="running" />
          <el-option label="completed" value="completed" />
          <el-option label="failed" value="failed" />
        </el-select>
        <el-button @click="refreshScans" :loading="loading">刷新</el-button>
      </div>
    </div>

    <el-card shadow="never" class="panel-card">
      <template #header><span>创建扫描任务</span></template>
      <el-form label-width="100px">
        <el-form-item label="任务类型">
          <el-select v-model="form.taskType" style="width: 280px">
            <el-option v-for="item in taskTypes" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="form.priority" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="配置(JSON)">
          <el-input
            v-model="form.configJson"
            type="textarea"
            :rows="6"
            style="max-width: 640px"
          />
        </el-form-item>
        <el-form-item label="创建后启动">
          <el-select v-model="form.autoStart" style="width: 120px">
            <el-option :value="true" label="是" />
            <el-option :value="false" label="否" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="creating" @click="submitCreate">创建任务</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="panel-card">
      <template #header><span>任务列表</span></template>
      <el-empty v-if="!scans.length" description="暂无任务" />
      <el-table v-else :data="scans" v-loading="loading">
        <el-table-column prop="task_type" label="类型" min-width="140" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="priority" label="优先级" width="100" />
        <el-table-column prop="progress" label="进度" width="100" />
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              type="primary"
              size="small"
              @click="triggerStart(row.id)"
            >
              启动
            </el-button>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="mt-4 flex justify-end">
        <el-pagination
          layout="total, sizes, prev, pager, next"
          :total="total"
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          @current-change="onCurrentPageChange"
          @size-change="onPageSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>
