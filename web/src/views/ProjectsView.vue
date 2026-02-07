<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { getErrorMessage } from '../api/client'
import { useWorkspaceStore } from '../stores/workspace'

const workspace = useWorkspaceStore()
const creating = ref(false)
const form = reactive({
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

onMounted(async () => {
  await refresh()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">Projects</h1>
      <el-button @click="refresh" :loading="workspace.loading">刷新</el-button>
    </div>

    <el-card shadow="never">
      <template #header>
        <span>创建项目</span>
      </template>
      <el-form :inline="true" @submit.prevent>
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

    <el-card shadow="never">
      <template #header>
        <span>项目列表</span>
      </template>
      <el-empty v-if="!workspace.projects.length" description="暂无项目，请先创建" />
      <el-table v-else :data="workspace.projects">
        <el-table-column prop="name" label="名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="240" />
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button
              size="small"
              :type="workspace.selectedProjectId === row.id ? 'success' : 'primary'"
              @click="workspace.setSelectedProject(row.id)"
            >
              {{ workspace.selectedProjectId === row.id ? '当前项目' : '设为当前' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
