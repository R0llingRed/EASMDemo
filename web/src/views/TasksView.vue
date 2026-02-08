<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  cancelScan,
  createScan,
  deleteScan,
  getScan,
  listScans,
  pauseScan,
  resumeScan,
  startScan,
  updateScan,
  type ScanTask,
} from '../api/easm'
import { getErrorMessage } from '../api/client'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()

const loading = ref(false)
const creating = ref(false)
const scans = ref<ScanTask[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const startingTaskId = ref('')
const actionTaskId = ref('')
const detailVisible = ref(false)
const detailLoading = ref(false)
const selectedTask = ref<ScanTask | null>(null)
const editVisible = ref(false)
const editing = ref(false)

const editForm = reactive({
  id: '',
  priority: 5,
  configJson: '{}',
})

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

function prettyJson(value: unknown): string {
  try {
    return JSON.stringify(value ?? {}, null, 2)
  } catch {
    return String(value ?? '')
  }
}

function isEditableStatus(status: string): boolean {
  return status === 'pending' || status === 'paused'
}

async function runTaskAction(taskId: string, action: () => Promise<void>) {
  actionTaskId.value = taskId
  try {
    await action()
  } finally {
    actionTaskId.value = ''
    await refreshScans()
  }
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
      try {
        await startScan(projectId, created.id)
        ElMessage.success('任务已创建并启动')
      } catch (error) {
        ElMessage.error(`任务已创建，但启动失败：${getErrorMessage(error)}`)
      }
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
  startingTaskId.value = taskId
  try {
    await startScan(projectId, taskId)
    ElMessage.success('任务已启动')
  } catch (error) {
    ElMessage.error(`启动失败：${getErrorMessage(error)}`)
  } finally {
    startingTaskId.value = ''
    await refreshScans()
  }
}

async function triggerPause(taskId: string) {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    return
  }
  await runTaskAction(taskId, async () => {
    await pauseScan(projectId, taskId)
    ElMessage.success('任务已暂停')
  })
}

async function triggerResume(taskId: string) {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    return
  }
  await runTaskAction(taskId, async () => {
    await resumeScan(projectId, taskId)
    ElMessage.success('任务已恢复为待执行')
  })
}

async function triggerCancel(taskId: string) {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    return
  }
  try {
    await ElMessageBox.confirm(
      '取消后任务将停止后续处理，是否继续？',
      '确认取消任务',
      { type: 'warning' },
    )
  } catch {
    return
  }

  await runTaskAction(taskId, async () => {
    await cancelScan(projectId, taskId)
    ElMessage.success('任务已取消')
  })
}

function openTaskEditor(task: ScanTask) {
  if (!isEditableStatus(task.status)) {
    ElMessage.warning('只有 pending/paused 任务可编辑')
    return
  }
  editForm.id = task.id
  editForm.priority = task.priority
  editForm.configJson = prettyJson(task.config)
  editVisible.value = true
}

async function submitTaskEdit() {
  const projectId = workspace.selectedProjectId
  if (!projectId || !editForm.id) {
    return
  }

  let config: Record<string, unknown>
  try {
    config = JSON.parse(editForm.configJson) as Record<string, unknown>
  } catch {
    ElMessage.error('配置 JSON 格式不合法')
    return
  }

  editing.value = true
  try {
    await updateScan(projectId, editForm.id, {
      priority: editForm.priority,
      config,
    })
    ElMessage.success('任务已更新')
    editVisible.value = false
    await refreshScans()
  } catch (error) {
    ElMessage.error(`更新失败：${getErrorMessage(error)}`)
  } finally {
    editing.value = false
  }
}

async function triggerDelete(task: ScanTask) {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    return
  }
  if (task.status === 'running') {
    ElMessage.warning('运行中的任务不可删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      '删除任务后将无法恢复，是否继续？',
      '确认删除任务',
      { type: 'warning' },
    )
  } catch {
    return
  }

  await runTaskAction(task.id, async () => {
    await deleteScan(projectId, task.id)
    ElMessage.success('任务已删除')
  })
}

async function openTaskDetails(task: ScanTask) {
  const projectId = workspace.selectedProjectId
  selectedTask.value = task
  detailVisible.value = true

  if (!projectId) {
    return
  }

  detailLoading.value = true
  try {
    const latest = await getScan(projectId, task.id)
    selectedTask.value = latest
  } catch (error) {
    ElMessage.error(`详情加载失败：${getErrorMessage(error)}`)
  } finally {
    detailLoading.value = false
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
          <el-option label="paused" value="paused" />
          <el-option label="running" value="running" />
          <el-option label="completed" value="completed" />
          <el-option label="failed" value="failed" />
          <el-option label="cancelled" value="cancelled" />
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
        <el-table-column label="操作" width="520">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <el-button
                v-if="row.status === 'pending'"
                type="primary"
                size="small"
                :loading="startingTaskId === row.id || actionTaskId === row.id"
                @click="triggerStart(row.id)"
              >
                启动
              </el-button>
              <el-button
                v-if="row.status === 'pending'"
                size="small"
                :loading="actionTaskId === row.id"
                @click="triggerPause(row.id)"
              >
                暂停
              </el-button>
              <el-button
                v-if="row.status === 'paused'"
                type="success"
                size="small"
                :loading="actionTaskId === row.id"
                @click="triggerResume(row.id)"
              >
                恢复
              </el-button>
              <el-button
                v-if="row.status === 'pending' || row.status === 'paused' || row.status === 'running'"
                type="warning"
                size="small"
                :loading="actionTaskId === row.id"
                @click="triggerCancel(row.id)"
              >
                取消
              </el-button>
              <el-button
                v-if="isEditableStatus(row.status)"
                size="small"
                @click="openTaskEditor(row)"
              >
                编辑
              </el-button>
              <el-button
                v-if="row.status !== 'running'"
                type="danger"
                size="small"
                :loading="actionTaskId === row.id"
                @click="triggerDelete(row)"
              >
                删除
              </el-button>
              <el-button size="small" @click="openTaskDetails(row)">详情/日志</el-button>
            </div>
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

    <el-drawer
      v-model="detailVisible"
      title="任务详情与日志"
      size="56%"
      :destroy-on-close="false"
    >
      <el-skeleton :loading="detailLoading" animated>
        <template #template>
          <el-skeleton-item variant="p" style="width: 100%; height: 24px; margin-bottom: 12px" />
          <el-skeleton-item variant="text" style="width: 100%; height: 180px" />
        </template>
        <template #default>
          <div v-if="selectedTask" class="space-y-4">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="任务 ID">{{ selectedTask.id }}</el-descriptions-item>
              <el-descriptions-item label="任务类型">{{ selectedTask.task_type }}</el-descriptions-item>
              <el-descriptions-item label="状态">{{ selectedTask.status }}</el-descriptions-item>
              <el-descriptions-item label="优先级">{{ selectedTask.priority }}</el-descriptions-item>
              <el-descriptions-item label="进度">{{ selectedTask.progress }}%</el-descriptions-item>
              <el-descriptions-item label="目标完成">
                {{ selectedTask.completed_targets }}/{{ selectedTask.total_targets }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ selectedTask.created_at }}</el-descriptions-item>
              <el-descriptions-item label="开始时间">{{ selectedTask.started_at || '-' }}</el-descriptions-item>
              <el-descriptions-item label="结束时间">{{ selectedTask.completed_at || '-' }}</el-descriptions-item>
            </el-descriptions>

            <el-alert
              v-if="selectedTask.error_message"
              type="error"
              :closable="false"
              :title="selectedTask.error_message"
              show-icon
            />
            <el-alert
              v-else
              type="success"
              :closable="false"
              title="暂无错误日志"
              show-icon
            />

            <el-card shadow="never">
              <template #header><span>任务配置</span></template>
              <pre class="rounded bg-slate-950 p-3 text-xs text-slate-100">{{ prettyJson(selectedTask.config) }}</pre>
            </el-card>

            <el-card shadow="never">
              <template #header><span>执行摘要/日志</span></template>
              <pre class="rounded bg-slate-950 p-3 text-xs text-slate-100">{{ prettyJson(selectedTask.result_summary) }}</pre>
            </el-card>
          </div>
          <el-empty v-else description="暂无可展示任务" />
        </template>
      </el-skeleton>
    </el-drawer>

    <el-dialog v-model="editVisible" title="编辑任务" width="680px">
      <el-form label-width="100px">
        <el-form-item label="优先级">
          <el-input-number v-model="editForm.priority" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="配置(JSON)">
          <el-input v-model="editForm.configJson" type="textarea" :rows="10" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editing" @click="submitTaskEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
