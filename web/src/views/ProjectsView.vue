<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { getErrorMessage } from '../api/client'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
const creating = ref(false)
const deletingId = ref('')
const editVisible = ref(false)
const editing = ref(false)
const form = reactive({
  name: '',
  description: '',
})
const editForm = reactive({
  id: '',
  name: '',
  description: '',
})

async function refresh() {
  await workspace.loadProjects()
}

async function submitCreate() {
  const name = form.name.trim()
  if (!name) {
    ElMessage.warning('项目名称不能为空')
    return
  }

  creating.value = true
  try {
    await workspace.createProjectAndRefresh({
      name,
      description: form.description.trim() || undefined,
    })
    form.name = ''
    form.description = ''
    ElMessage.success('项目创建成功')
  } catch (error) {
    ElMessage.error(`项目创建失败：${getErrorMessage(error)}`)
  } finally {
    creating.value = false
  }
}

function openEdit(row: { id: string; name: string; description: string | null }) {
  editForm.id = row.id
  editForm.name = row.name
  editForm.description = row.description ?? ''
  editVisible.value = true
}

async function submitEdit() {
  const name = editForm.name.trim()
  if (!name) {
    ElMessage.warning('项目名称不能为空')
    return
  }
  if (!editForm.id) {
    return
  }

  editing.value = true
  try {
    await workspace.updateProjectAndRefresh(editForm.id, {
      name,
      description: editForm.description.trim() || null,
    })
    ElMessage.success('项目已更新')
    editVisible.value = false
  } catch (error) {
    ElMessage.error(`项目更新失败：${getErrorMessage(error)}`)
  } finally {
    editing.value = false
  }
}

async function removeProject(row: { id: string; name: string }) {
  try {
    await ElMessageBox.confirm(
      `删除项目「${row.name}」将清理其关联资产和任务，是否继续？`,
      '确认删除项目',
      { type: 'warning' },
    )
  } catch {
    return
  }

  deletingId.value = row.id
  try {
    await workspace.deleteProjectAndRefresh(row.id)
    ElMessage.success('项目已删除')
  } catch (error) {
    ElMessage.error(`项目删除失败：${getErrorMessage(error)}`)
  } finally {
    deletingId.value = ''
  }
}

onMounted(async () => {
  await refresh()
})
</script>

<template>
  <div class="page-shell">
    <div class="page-head">
      <div>
        <h1 class="page-title">Projects</h1>
        <p class="page-subtitle">创建项目并切换当前工作空间</p>
      </div>
      <div class="page-tools">
        <el-button @click="refresh" :loading="workspace.loading">刷新</el-button>
      </div>
    </div>

    <el-card shadow="never" class="panel-card">
      <template #header>
        <span>创建项目</span>
      </template>
      <el-form @submit.prevent class="grid grid-cols-1 gap-3 md:grid-cols-3">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="例如: prod-easm" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="可选" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="creating" @click="submitCreate">创建</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="panel-card">
      <template #header>
        <span>项目列表</span>
      </template>
      <el-empty v-if="!workspace.projects.length" description="暂无项目，请先创建" />
      <el-table v-else :data="workspace.projects">
        <el-table-column prop="name" label="名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="240" />
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <el-button
                size="small"
                :type="workspace.selectedProjectId === row.id ? 'success' : 'primary'"
                @click="workspace.setSelectedProject(row.id)"
              >
                {{ workspace.selectedProjectId === row.id ? '当前项目' : '设为当前' }}
              </el-button>
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button
                size="small"
                type="danger"
                :loading="deletingId === row.id"
                @click="removeProject(row)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="editVisible" title="编辑项目" width="560px">
      <el-form label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editing" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
