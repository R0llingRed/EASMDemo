import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { createProject, listProjects, type Project } from '../api/easm'

const ACTIVE_PROJECT_STORAGE = 'easm_active_project_id'

export const useWorkspaceStore = defineStore('workspace', () => {
  const projects = ref<Project[]>([])
  const loading = ref(false)
  const selectedProjectId = ref(localStorage.getItem(ACTIVE_PROJECT_STORAGE) ?? '')

  const selectedProject = computed(() =>
    projects.value.find((project) => project.id === selectedProjectId.value) ?? null,
  )

  async function loadProjects() {
    loading.value = true
    try {
      const result = await listProjects()
      projects.value = result.items

      if (!projects.value.length) {
        selectedProjectId.value = ''
        localStorage.removeItem(ACTIVE_PROJECT_STORAGE)
        return
      }

      const stillExists = projects.value.some(
        (project) => project.id === selectedProjectId.value,
      )
      if (!stillExists) {
        const [firstProject] = projects.value
        if (firstProject) {
          selectedProjectId.value = firstProject.id
          localStorage.setItem(ACTIVE_PROJECT_STORAGE, selectedProjectId.value)
        }
      }
      return true
    } catch {
      projects.value = []
      selectedProjectId.value = ''
      return false
    } finally {
      loading.value = false
    }
  }

  function setSelectedProject(projectId: string) {
    selectedProjectId.value = projectId
    localStorage.setItem(ACTIVE_PROJECT_STORAGE, projectId)
  }

  async function createProjectAndRefresh(payload: { name: string; description?: string }) {
    await createProject(payload)
    await loadProjects()
  }

  return {
    projects,
    loading,
    selectedProjectId,
    selectedProject,
    loadProjects,
    setSelectedProject,
    createProjectAndRefresh,
  }
})
