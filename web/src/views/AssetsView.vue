<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { deleteAsset, importAssets, listAssets, updateAsset, type Asset } from '../api/easm'
import { getErrorMessage } from '../api/client'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()

const loading = ref(false)
const importing = ref(false)
const assets = ref<Asset[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const actionAssetId = ref('')
const editVisible = ref(false)
const editing = ref(false)

const editForm = reactive({
  id: '',
  source: '',
})

const query = reactive<{
  asset_type?: 'domain' | 'ip' | 'url'
}>({
  asset_type: undefined,
})

const importForm = reactive({
  assetType: 'domain' as 'domain' | 'ip' | 'url',
  source: 'manual',
  lines: '',
})

async function loadAssets() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    assets.value = []
    total.value = 0
    return
  }

  loading.value = true
  try {
    const result = await listAssets(projectId, {
      asset_type: query.asset_type,
      offset: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    })
    assets.value = result.items
    total.value = result.total
  } catch (error) {
    ElMessage.error(`资产加载失败：${getErrorMessage(error)}`)
  } finally {
    loading.value = false
  }
}

function parseImportLines(): Array<{ asset_type: 'domain' | 'ip' | 'url'; value: string; source?: string }> {
  return importForm.lines
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((value) => ({
      asset_type: importForm.assetType,
      value,
      source: importForm.source.trim() || undefined,
    }))
}

async function submitImport() {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    ElMessage.warning('请先在 Projects 页面选择项目')
    return
  }

  const parsedAssets = parseImportLines()
  if (!parsedAssets.length) {
    ElMessage.warning('请至少输入一条资产')
    return
  }

  importing.value = true
  try {
    const result = await importAssets(projectId, parsedAssets)
    ElMessage.success(`导入完成：新增 ${result.inserted}，跳过 ${result.skipped}`)
    importForm.lines = ''
    currentPage.value = 1
    await loadAssets()
  } catch (error) {
    ElMessage.error(`导入失败：${getErrorMessage(error)}`)
  } finally {
    importing.value = false
  }
}

async function onFilterChange() {
  currentPage.value = 1
  await loadAssets()
}

async function onCurrentPageChange(page: number) {
  currentPage.value = page
  await loadAssets()
}

async function onPageSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  await loadAssets()
}

function openEdit(asset: Asset) {
  editForm.id = asset.id
  editForm.source = asset.source ?? ''
  editVisible.value = true
}

async function submitEdit() {
  const projectId = workspace.selectedProjectId
  if (!projectId || !editForm.id) {
    return
  }

  editing.value = true
  try {
    await updateAsset(projectId, editForm.id, {
      source: editForm.source.trim() || null,
    })
    ElMessage.success('资产来源已更新')
    editVisible.value = false
    await loadAssets()
  } catch (error) {
    ElMessage.error(`更新失败：${getErrorMessage(error)}`)
  } finally {
    editing.value = false
  }
}

async function removeAsset(asset: Asset) {
  const projectId = workspace.selectedProjectId
  if (!projectId) {
    return
  }

  try {
    await ElMessageBox.confirm('删除后无法恢复，是否继续？', '确认删除资产', {
      type: 'warning',
    })
  } catch {
    return
  }

  actionAssetId.value = asset.id
  try {
    await deleteAsset(projectId, asset.id)
    ElMessage.success('资产已删除')
    await loadAssets()
  } catch (error) {
    ElMessage.error(`删除失败：${getErrorMessage(error)}`)
  } finally {
    actionAssetId.value = ''
  }
}

onMounted(async () => {
  await workspace.loadProjects()
  await loadAssets()
})

watch(
  () => workspace.selectedProjectId,
  async () => {
    currentPage.value = 1
    await loadAssets()
  },
)
</script>

<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <h1 class="page-title">Assets</h1>
        <p class="page-subtitle">批量导入资产并按类型检索</p>
      </div>
      <el-tag v-if="workspace.selectedProject" effect="dark">{{ workspace.selectedProject.name }}</el-tag>
      <el-tag type="warning" v-else>未选择项目</el-tag>
    </div>

    <el-alert
      v-if="!workspace.selectedProjectId"
      title="请先在 Projects 页面选择项目后再导入或查看资产。"
      type="warning"
      :closable="false"
    />

    <el-card shadow="never" class="panel-card">
      <template #header>
        <span>批量导入资产（每行一条）</span>
      </template>
      <el-form label-width="90px">
        <el-form-item label="资产类型">
          <el-select v-model="importForm.assetType" style="width: 200px">
            <el-option label="domain" value="domain" />
            <el-option label="ip" value="ip" />
            <el-option label="url" value="url" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="importForm.source" placeholder="manual" style="max-width: 280px" />
        </el-form-item>
        <el-form-item label="资产列表">
          <el-input
            v-model="importForm.lines"
            type="textarea"
            :rows="6"
            placeholder="example.com&#10;api.example.com"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="importing" @click="submitImport">导入</el-button>
          <el-button @click="loadAssets" :loading="loading">刷新列表</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="panel-card">
      <template #header>
        <div class="flex items-center justify-between">
          <span>资产列表（{{ total }}）</span>
          <el-select
            v-model="query.asset_type"
            clearable
            placeholder="按类型过滤"
            style="width: 180px"
            @change="onFilterChange"
          >
            <el-option label="domain" value="domain" />
            <el-option label="ip" value="ip" />
            <el-option label="url" value="url" />
          </el-select>
        </div>
      </template>
      <el-empty v-if="!assets.length" description="暂无资产" />
      <el-table v-else :data="assets" v-loading="loading">
        <el-table-column prop="asset_type" label="类型" width="120" />
        <el-table-column prop="value" label="值" min-width="260" />
        <el-table-column prop="source" label="来源" width="140" />
        <el-table-column prop="first_seen" label="首次发现" min-width="180" />
        <el-table-column prop="last_seen" label="最近发现" min-width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button
                size="small"
                type="danger"
                :loading="actionAssetId === row.id"
                @click="removeAsset(row)"
              >
                删除
              </el-button>
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

    <el-dialog v-model="editVisible" title="编辑资产来源" width="560px">
      <el-form label-width="90px">
        <el-form-item label="来源">
          <el-input v-model="editForm.source" placeholder="例如：manual / external_feed" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editing" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
