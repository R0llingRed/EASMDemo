<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { getErrorMessage } from '../api/client'
import {
  createDAGTemplate,
  createEventTrigger,
  listEventTriggers,
  updateEventTrigger,
  type DAGNodeInput,
  type EventTrigger,
} from '../api/easm'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()

const loading = ref(false)
const applying = ref(false)
const triggers = ref<EventTrigger[]>([])

const TASK_ORDER = [
  'subdomain_scan',
  'dns_resolve',
  'port_scan',
  'http_probe',
  'fingerprint',
  'screenshot',
  'nuclei_scan',
  'js_api_discovery',
  'xray_scan',
] as const

const TASK_LABELS: Record<string, string> = {
  subdomain_scan: '子域名枚举',
  dns_resolve: 'DNS 解析',
  port_scan: '端口探测',
  http_probe: 'HTTP 探活',
  fingerprint: '指纹识别',
  screenshot: '截图采集',
  nuclei_scan: 'Nuclei 漏洞扫描',
  js_api_discovery: 'JS/API 深度发现',
  xray_scan: 'Xray 深度扫描',
}

type PresetType = 'quick' | 'standard' | 'deep'

const PRESET_TASKS: Record<PresetType, string[]> = {
  quick: ['http_probe', 'fingerprint'],
  standard: ['subdomain_scan', 'dns_resolve', 'port_scan', 'http_probe', 'fingerprint'],
  deep: ['subdomain_scan', 'dns_resolve', 'port_scan', 'http_probe', 'fingerprint', 'screenshot', 'nuclei_scan', 'js_api_discovery', 'xray_scan'],
}

const form = reactive({
  preset: 'standard' as PresetType,
  strategyName: '标准自动化',
  description: '资产导入后自动执行扫描链路',
  tasks: [...PRESET_TASKS.standard],
  batchSize: 100,
  priority: 5,
  disableOld: true,
})

const pipelineText = computed(() => {
  const ordered = TASK_ORDER.filter((task) => form.tasks.includes(task))
  return ordered.map((task) => TASK_LABELS[task]).join(' -> ')
})

function applyPreset(preset: PresetType) {
  if (preset === 'quick') {
    form.strategyName = '快速自动化'
    form.description = '资产导入后执行探活与指纹识别'
    form.tasks = [...PRESET_TASKS.quick]
    return
  }
  if (preset === 'deep') {
    form.strategyName = '深度自动化'
    form.description = '资产导入后执行全链路深度扫描'
    form.tasks = [...PRESET_TASKS.deep]
    return
  }
  form.strategyName = '标准自动化'
  form.description = '资产导入后自动执行扫描链路'
  form.tasks = [...PRESET_TASKS.standard]
}

function buildNodeDependencies(taskType: string, orderedTasks: string[]): string[] {
  const has = (task: string) => orderedTasks.includes(task)

  if (taskType === 'dns_resolve' && has('subdomain_scan')) {
    return ['subdomain_scan']
  }
  if (taskType === 'port_scan') {
    if (has('dns_resolve')) {
      return ['dns_resolve']
    }
    if (has('subdomain_scan')) {
      return ['subdomain_scan']
    }
  }
  if (taskType === 'http_probe') {
    if (has('port_scan')) {
      return ['port_scan']
    }
    if (has('dns_resolve')) {
      return ['dns_resolve']
    }
    if (has('subdomain_scan')) {
      return ['subdomain_scan']
    }
  }
  if (['fingerprint', 'screenshot', 'nuclei_scan', 'js_api_discovery', 'xray_scan'].includes(taskType)) {
    if (has('http_probe')) {
      return ['http_probe']
    }
  }

  const index = orderedTasks.indexOf(taskType)
  if (index > 0) {
    return [orderedTasks[index - 1] ?? '']
  }
  return []
}

function buildNodes(): DAGNodeInput[] {
  const orderedTasks = TASK_ORDER.filter((task) => form.tasks.includes(task))
  return orderedTasks.map((task) => ({
    id: task,
    task_type: task,
    depends_on: buildNodeDependencies(task, orderedTasks).filter(Boolean),
    config: {
      batch_size: form.batchSize,
      priority: form.priority,
    },
  }))
}

async function loadTriggers() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    triggers.value = []
    return
  }

  loading.value = true
  try {
    const page = await listEventTriggers(projectId, {
      event_type: 'asset_created',
      skip: 0,
      limit: 200,
    })
    triggers.value = page.items
  } catch (error) {
    ElMessage.error(`自动化策略加载失败：${getErrorMessage(error)}`)
  } finally {
    loading.value = false
  }
}

async function toggleTrigger(trigger: EventTrigger) {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    return
  }
  try {
    await updateEventTrigger(projectId, trigger.id, { enabled: !trigger.enabled })
    ElMessage.success(trigger.enabled ? '已停用触发器' : '已启用触发器')
    await loadTriggers()
  } catch (error) {
    ElMessage.error(`触发器更新失败：${getErrorMessage(error)}`)
  }
}

async function applyStrategy() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    ElMessage.warning('请先选择项目')
    return
  }
  if (!form.tasks.length) {
    ElMessage.warning('请至少选择一个扫描任务')
    return
  }

  const nodes = buildNodes()
  const edges = nodes.flatMap((node) =>
    node.depends_on.map((dep) => ({ from: dep, to: node.id })),
  )

  applying.value = true
  try {
    if (form.disableOld) {
      const existing = await listEventTriggers(projectId, {
        event_type: 'asset_created',
        skip: 0,
        limit: 200,
      })
      for (const trigger of existing.items) {
        if (trigger.enabled && trigger.name.startsWith('AutoFlow:')) {
          await updateEventTrigger(projectId, trigger.id, { enabled: false })
        }
      }
    }

    const strategyTitle = form.strategyName.trim() || '自动化策略'
    const templateName = `AutoFlow:${strategyTitle}`
    const template = await createDAGTemplate(projectId, {
      name: templateName,
      description: form.description.trim() || undefined,
      nodes,
      edges,
      enabled: true,
    })

    const trigger = await createEventTrigger(projectId, {
      name: templateName,
      description: '资产导入后自动触发扫描流程',
      event_type: 'asset_created',
      dag_template_id: template.id,
      filter_config: {},
      dag_config: {
        batch_size: form.batchSize,
        priority: form.priority,
      },
      enabled: true,
    })

    ElMessage.success(`策略已启用（触发器 ${trigger.id.slice(0, 8)}）`)
    await loadTriggers()
  } catch (error) {
    ElMessage.error(`策略启用失败：${getErrorMessage(error)}`)
  } finally {
    applying.value = false
  }
}

watch(
  () => form.preset,
  (preset) => {
    applyPreset(preset)
  },
)

watch(
  () => workspace.selectedProjectId,
  async () => {
    await loadTriggers()
  },
)

onMounted(async () => {
  await workspace.loadProjects()
  await loadTriggers()
})
</script>

<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <h1 class="page-title">Automation</h1>
        <p class="page-subtitle">用策略方式配置“导入资产后自动扫描”</p>
      </div>
      <div class="page-tools">
        <el-button @click="loadTriggers" :loading="loading">刷新策略</el-button>
      </div>
    </div>

    <el-alert
      v-if="!workspace.selectedProjectId"
      title="请先在 Projects 页面选择一个项目，再配置自动化策略。"
      type="warning"
      :closable="false"
    />

    <el-card shadow="never" class="panel-card">
      <template #header>
        <span>策略向导</span>
      </template>
      <el-form label-width="140px">
        <el-form-item label="策略预设">
          <el-select v-model="form.preset" style="width: 220px">
            <el-option label="快速策略（探活+指纹）" value="quick" />
            <el-option label="标准策略（基础链路）" value="standard" />
            <el-option label="深度策略（全链路）" value="deep" />
          </el-select>
        </el-form-item>
        <el-form-item label="策略名称">
          <el-input v-model="form.strategyName" placeholder="例如：生产资产自动扫描" />
        </el-form-item>
        <el-form-item label="策略描述">
          <el-input v-model="form.description" placeholder="用于后续识别策略用途" />
        </el-form-item>
        <el-form-item label="扫描任务">
          <el-select v-model="form.tasks" multiple style="width: 100%" placeholder="选择要执行的扫描任务">
            <el-option
              v-for="task in TASK_ORDER"
              :key="task"
              :label="`${TASK_LABELS[task]} (${task})`"
              :value="task"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="批大小 batch_size">
          <el-input-number v-model="form.batchSize" :min="1" :max="5000" />
        </el-form-item>
        <el-form-item label="任务优先级">
          <el-input-number v-model="form.priority" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="启用前停用旧策略">
          <el-select v-model="form.disableOld" style="width: 180px">
            <el-option :value="true" label="是（推荐）" />
            <el-option :value="false" label="否" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行链路预览">
          <el-tag v-if="pipelineText" effect="dark">{{ pipelineText }}</el-tag>
          <el-tag v-else type="warning">未选择任务</el-tag>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="applying"
            :disabled="!workspace.selectedProjectId"
            @click="applyStrategy"
          >
            启用自动化策略
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="panel-card">
      <template #header>
        <span>资产导入触发器（event_type=asset_created）</span>
      </template>
      <el-empty v-if="!triggers.length" description="当前项目暂无自动化触发器" />
      <el-table v-else :data="triggers" v-loading="loading">
        <el-table-column prop="name" label="名称" min-width="220" />
        <el-table-column prop="enabled" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dag_template_id" label="DAG 模板 ID" min-width="240" />
        <el-table-column label="触发计数" min-width="180">
          <template #default="{ row }">
            total={{ row.trigger_count.total || 0 }},
            success={{ row.trigger_count.success || 0 }},
            failed={{ row.trigger_count.failed || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button size="small" @click="toggleTrigger(row)">
              {{ row.enabled ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
