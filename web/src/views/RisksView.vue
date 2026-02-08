<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import {
  getVulnerabilityStats,
  listApiRisks,
  listRiskScores,
  listVulnerabilities,
  updateApiRiskStatus,
  updateVulnerability,
  type ApiRisk,
  type RiskScore,
  type Vulnerability,
  type VulnerabilityStats,
} from '../api/easm'
import { getErrorMessage } from '../api/client'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
const loading = ref(false)
const apiRiskTotal = ref(0)

const vulnerabilityStats = reactive<VulnerabilityStats>({
  total: 0,
  critical: 0,
  high: 0,
  medium: 0,
  low: 0,
  info: 0,
  open: 0,
  confirmed: 0,
  fixed: 0,
  false_positive: 0,
})

const vulnerabilities = ref<Vulnerability[]>([])
const vulnerabilityTotal = ref(0)
const vulnerabilityQuery = reactive({
  severity: '',
  status: '',
  page: 1,
  pageSize: 10,
})

const apiRisks = ref<ApiRisk[]>([])
const apiRiskQuery = reactive({
  severity: '',
  status: '',
  page: 1,
  pageSize: 10,
})

const riskScores = ref<RiskScore[]>([])
const riskScoreTotal = ref(0)
const riskScoreQuery = reactive({
  severity: '',
  page: 1,
  pageSize: 10,
})

const vulnActionVisible = ref(false)
const vulnActionLoading = ref(false)
const vulnActionForm = reactive({
  id: '',
  status: 'open' as 'open' | 'confirmed' | 'fixed' | 'false_positive',
})

const apiRiskActionVisible = ref(false)
const apiRiskActionLoading = ref(false)
const apiRiskActionForm = reactive({
  id: '',
  status: 'open' as 'open' | 'investigating' | 'accepted_risk' | 'resolved' | 'false_positive',
  updatedBy: 'ui-user',
  resolutionNotes: '',
})

function resetAll() {
  Object.assign(vulnerabilityStats, {
    total: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    info: 0,
    open: 0,
    confirmed: 0,
    fixed: 0,
    false_positive: 0,
  })
  vulnerabilities.value = []
  vulnerabilityTotal.value = 0
  apiRisks.value = []
  apiRiskTotal.value = 0
  riskScores.value = []
  riskScoreTotal.value = 0
}

async function loadSummary() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    return
  }
  const stats = await getVulnerabilityStats(projectId)
  Object.assign(vulnerabilityStats, stats)
}

async function loadVulnerabilities() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    vulnerabilities.value = []
    vulnerabilityTotal.value = 0
    return
  }

  const page = await listVulnerabilities(projectId, {
    severity: vulnerabilityQuery.severity || undefined,
    status: vulnerabilityQuery.status || undefined,
    skip: (vulnerabilityQuery.page - 1) * vulnerabilityQuery.pageSize,
    limit: vulnerabilityQuery.pageSize,
  })

  vulnerabilities.value = page.items
  vulnerabilityTotal.value = page.total
}

async function loadApiRiskList() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    apiRisks.value = []
    apiRiskTotal.value = 0
    return
  }

  const page = await listApiRisks(projectId, {
    severity: apiRiskQuery.severity || undefined,
    status: apiRiskQuery.status || undefined,
    skip: (apiRiskQuery.page - 1) * apiRiskQuery.pageSize,
    limit: apiRiskQuery.pageSize,
  })

  apiRisks.value = page.items
  apiRiskTotal.value = page.total
}

async function loadRiskScoreList() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    riskScores.value = []
    riskScoreTotal.value = 0
    return
  }

  const page = await listRiskScores(projectId, {
    severity_level: riskScoreQuery.severity || undefined,
    skip: (riskScoreQuery.page - 1) * riskScoreQuery.pageSize,
    limit: riskScoreQuery.pageSize,
  })
  riskScores.value = page.items
  riskScoreTotal.value = page.total
}

async function loadAll() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    resetAll()
    return
  }

  loading.value = true
  try {
    await Promise.all([
      loadSummary(),
      loadVulnerabilities(),
      loadApiRiskList(),
      loadRiskScoreList(),
    ])
  } catch (error) {
    ElMessage.error(`风险数据加载失败：${getErrorMessage(error)}`)
  } finally {
    loading.value = false
  }
}

async function onVulnerabilityFilterChange() {
  vulnerabilityQuery.page = 1
  await loadAll()
}

async function onVulnerabilityPageChange(page: number) {
  vulnerabilityQuery.page = page
  await loadAll()
}

async function onVulnerabilityPageSizeChange(size: number) {
  vulnerabilityQuery.pageSize = size
  vulnerabilityQuery.page = 1
  await loadAll()
}

async function onApiRiskFilterChange() {
  apiRiskQuery.page = 1
  await loadAll()
}

async function onApiRiskPageChange(page: number) {
  apiRiskQuery.page = page
  await loadAll()
}

async function onApiRiskPageSizeChange(size: number) {
  apiRiskQuery.pageSize = size
  apiRiskQuery.page = 1
  await loadAll()
}

async function onRiskScoreFilterChange() {
  riskScoreQuery.page = 1
  await loadAll()
}

async function onRiskScorePageChange(page: number) {
  riskScoreQuery.page = page
  await loadAll()
}

async function onRiskScorePageSizeChange(size: number) {
  riskScoreQuery.pageSize = size
  riskScoreQuery.page = 1
  await loadAll()
}

function openVulnerabilityAction(row: Vulnerability) {
  vulnActionForm.id = row.id
  vulnActionForm.status = row.status as typeof vulnActionForm.status
  vulnActionVisible.value = true
}

async function submitVulnerabilityAction() {
  const projectId = workspace.selectedProjectId
  if (!projectId || !vulnActionForm.id) {
    return
  }
  vulnActionLoading.value = true
  try {
    await updateVulnerability(projectId, vulnActionForm.id, {
      status: vulnActionForm.status,
      is_false_positive: vulnActionForm.status === 'false_positive',
    })
    ElMessage.success('漏洞状态已更新')
    vulnActionVisible.value = false
    await loadAll()
  } catch (error) {
    ElMessage.error(`漏洞更新失败：${getErrorMessage(error)}`)
  } finally {
    vulnActionLoading.value = false
  }
}

function openApiRiskAction(row: ApiRisk) {
  apiRiskActionForm.id = row.id
  apiRiskActionForm.status = row.status as typeof apiRiskActionForm.status
  apiRiskActionForm.updatedBy = row.updated_by || 'ui-user'
  apiRiskActionForm.resolutionNotes = row.resolution_notes || ''
  apiRiskActionVisible.value = true
}

async function submitApiRiskAction() {
  const projectId = workspace.selectedProjectId
  if (!projectId || !apiRiskActionForm.id) {
    return
  }
  const needNotes =
    apiRiskActionForm.status === 'resolved' || apiRiskActionForm.status === 'false_positive'
  if (needNotes && !apiRiskActionForm.resolutionNotes.trim()) {
    ElMessage.warning('resolved/false_positive 必须填写处置说明')
    return
  }

  apiRiskActionLoading.value = true
  try {
    await updateApiRiskStatus(projectId, apiRiskActionForm.id, {
      status: apiRiskActionForm.status,
      updated_by: apiRiskActionForm.updatedBy.trim() || 'ui-user',
      resolution_notes: apiRiskActionForm.resolutionNotes.trim() || undefined,
    })
    ElMessage.success('API 风险状态已更新')
    apiRiskActionVisible.value = false
    await loadAll()
  } catch (error) {
    ElMessage.error(`API 风险更新失败：${getErrorMessage(error)}`)
  } finally {
    apiRiskActionLoading.value = false
  }
}

onMounted(async () => {
  await workspace.loadProjects()
  await loadAll()
})

watch(
  () => workspace.selectedProjectId,
  async () => {
    vulnerabilityQuery.page = 1
    apiRiskQuery.page = 1
    riskScoreQuery.page = 1
    await loadAll()
  },
)
</script>

<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <h1 class="page-title">Risks</h1>
        <p class="page-subtitle">聚合漏洞、API 风险和资产风险分值</p>
      </div>
      <div class="page-tools">
        <el-button @click="loadAll" :loading="loading">刷新</el-button>
      </div>
    </div>

    <div class="kpi-grid" v-loading="loading">
      <article class="kpi-card text-[#2f6f7e]">
        <div class="kpi-label">漏洞总数</div>
        <div class="kpi-value kpi-value--neutral">{{ vulnerabilityStats.total }}</div>
      </article>
      <article class="kpi-card text-[var(--danger)]">
        <div class="kpi-label">严重漏洞</div>
        <div class="kpi-value kpi-value--danger">{{ vulnerabilityStats.critical }}</div>
      </article>
      <article class="kpi-card text-[var(--accent)]">
        <div class="kpi-label">高危漏洞</div>
        <div class="kpi-value kpi-value--accent">{{ vulnerabilityStats.high }}</div>
      </article>
      <article class="kpi-card text-[var(--brand)]">
        <div class="kpi-label">API 风险</div>
        <div class="kpi-value kpi-value--brand">{{ apiRiskTotal }}</div>
      </article>
    </div>

    <el-card shadow="never" class="panel-card">
      <template #header>
        <div class="flex items-center justify-between">
          <span>漏洞列表</span>
          <div class="flex items-center gap-2">
            <el-select
              v-model="vulnerabilityQuery.severity"
              clearable
              placeholder="严重度"
              style="width: 130px"
              @change="onVulnerabilityFilterChange"
            >
              <el-option label="critical" value="critical" />
              <el-option label="high" value="high" />
              <el-option label="medium" value="medium" />
              <el-option label="low" value="low" />
              <el-option label="info" value="info" />
            </el-select>
            <el-select
              v-model="vulnerabilityQuery.status"
              clearable
              placeholder="状态"
              style="width: 140px"
              @change="onVulnerabilityFilterChange"
            >
              <el-option label="open" value="open" />
              <el-option label="confirmed" value="confirmed" />
              <el-option label="fixed" value="fixed" />
              <el-option label="false_positive" value="false_positive" />
            </el-select>
          </div>
        </div>
      </template>
      <el-empty v-if="!vulnerabilities.length" description="暂无漏洞数据" />
      <el-table v-else :data="vulnerabilities" size="small">
        <el-table-column prop="severity" label="严重度" width="120" />
        <el-table-column prop="title" label="标题" min-width="280" />
        <el-table-column prop="target_url" label="目标" min-width="260" />
        <el-table-column prop="status" label="状态" width="140" />
        <el-table-column prop="last_seen" label="最近发现" min-width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="openVulnerabilityAction(row)">处置</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="mt-4 flex justify-end">
        <el-pagination
          layout="total, sizes, prev, pager, next"
          :total="vulnerabilityTotal"
          :current-page="vulnerabilityQuery.page"
          :page-size="vulnerabilityQuery.pageSize"
          :page-sizes="[10, 20, 50]"
          @current-change="onVulnerabilityPageChange"
          @size-change="onVulnerabilityPageSizeChange"
        />
      </div>
    </el-card>

    <el-card shadow="never" class="panel-card">
      <template #header>
        <div class="flex items-center justify-between">
          <span>API 风险列表</span>
          <div class="flex items-center gap-2">
            <el-select
              v-model="apiRiskQuery.severity"
              clearable
              placeholder="严重度"
              style="width: 130px"
              @change="onApiRiskFilterChange"
            >
              <el-option label="critical" value="critical" />
              <el-option label="high" value="high" />
              <el-option label="medium" value="medium" />
              <el-option label="low" value="low" />
              <el-option label="info" value="info" />
            </el-select>
            <el-select
              v-model="apiRiskQuery.status"
              clearable
              placeholder="状态"
              style="width: 160px"
              @change="onApiRiskFilterChange"
            >
              <el-option label="open" value="open" />
              <el-option label="investigating" value="investigating" />
              <el-option label="accepted_risk" value="accepted_risk" />
              <el-option label="resolved" value="resolved" />
              <el-option label="false_positive" value="false_positive" />
            </el-select>
          </div>
        </div>
      </template>
      <el-empty v-if="!apiRisks.length" description="暂无 API 风险" />
      <el-table v-else :data="apiRisks" size="small">
        <el-table-column prop="severity" label="严重度" width="120" />
        <el-table-column prop="title" label="标题" min-width="280" />
        <el-table-column prop="rule_name" label="规则" min-width="200" />
        <el-table-column prop="status" label="状态" width="150" />
        <el-table-column prop="updated_at" label="更新时间" min-width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="openApiRiskAction(row)">处置</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="mt-4 flex justify-end">
        <el-pagination
          layout="total, sizes, prev, pager, next"
          :total="apiRiskTotal"
          :current-page="apiRiskQuery.page"
          :page-size="apiRiskQuery.pageSize"
          :page-sizes="[10, 20, 50]"
          @current-change="onApiRiskPageChange"
          @size-change="onApiRiskPageSizeChange"
        />
      </div>
    </el-card>

    <el-card shadow="never" class="panel-card">
      <template #header>
        <div class="flex items-center justify-between">
          <span>风险评分</span>
          <el-select
            v-model="riskScoreQuery.severity"
            clearable
            placeholder="风险等级"
            style="width: 140px"
            @change="onRiskScoreFilterChange"
          >
            <el-option label="critical" value="critical" />
            <el-option label="high" value="high" />
            <el-option label="medium" value="medium" />
            <el-option label="low" value="low" />
            <el-option label="info" value="info" />
          </el-select>
        </div>
      </template>
      <el-empty v-if="!riskScores.length" description="暂无风险评分" />
      <el-table v-else :data="riskScores" size="small">
        <el-table-column prop="asset_type" label="资产类型" width="140" />
        <el-table-column prop="asset_id" label="资产 ID" min-width="260" />
        <el-table-column prop="total_score" label="风险分值" width="130" />
        <el-table-column prop="severity_level" label="等级" width="120" />
        <el-table-column prop="calculated_at" label="计算时间" min-width="180" />
      </el-table>
      <div class="mt-4 flex justify-end">
        <el-pagination
          layout="total, sizes, prev, pager, next"
          :total="riskScoreTotal"
          :current-page="riskScoreQuery.page"
          :page-size="riskScoreQuery.pageSize"
          :page-sizes="[10, 20, 50]"
          @current-change="onRiskScorePageChange"
          @size-change="onRiskScorePageSizeChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="vulnActionVisible" title="漏洞处置" width="520px">
      <el-form label-width="90px">
        <el-form-item label="状态">
          <el-select v-model="vulnActionForm.status" style="width: 220px">
            <el-option label="open" value="open" />
            <el-option label="confirmed" value="confirmed" />
            <el-option label="fixed" value="fixed" />
            <el-option label="false_positive" value="false_positive" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="vulnActionVisible = false">取消</el-button>
        <el-button type="primary" :loading="vulnActionLoading" @click="submitVulnerabilityAction">
          保存
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="apiRiskActionVisible" title="API 风险处置" width="640px">
      <el-form label-width="110px">
        <el-form-item label="状态">
          <el-select v-model="apiRiskActionForm.status" style="width: 260px">
            <el-option label="open" value="open" />
            <el-option label="investigating" value="investigating" />
            <el-option label="accepted_risk" value="accepted_risk" />
            <el-option label="resolved" value="resolved" />
            <el-option label="false_positive" value="false_positive" />
          </el-select>
        </el-form-item>
        <el-form-item label="更新人">
          <el-input v-model="apiRiskActionForm.updatedBy" placeholder="例如：secops@example.com" />
        </el-form-item>
        <el-form-item label="处置说明">
          <el-input
            v-model="apiRiskActionForm.resolutionNotes"
            type="textarea"
            :rows="4"
            placeholder="resolved/false_positive 时必填"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="apiRiskActionVisible = false">取消</el-button>
        <el-button type="primary" :loading="apiRiskActionLoading" @click="submitApiRiskAction">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>
