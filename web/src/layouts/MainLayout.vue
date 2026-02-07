<script setup lang="ts">
import { ref } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import {
  Monitor,
  Setting,
  User,
  Odometer,
  Files,
  WarnTriangleFilled,
  Aim
} from '@element-plus/icons-vue'

const route = useRoute()
const isCollapse = ref(false)

const handleOpen = (key: string, keyPath: string[]) => {
  console.log(key, keyPath)
}
const handleClose = (key: string, keyPath: string[]) => {
  console.log(key, keyPath)
}
</script>

<template>
  <el-container class="h-screen w-full">
    <el-aside width="240px" class="bg-gray-900 text-white transition-all duration-300" :class="{ 'w-16': isCollapse }">
      <div class="h-16 flex items-center justify-center border-b border-gray-800">
        <span class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-teal-400" v-if="!isCollapse">
          EASM Platform
        </span>
        <span v-else class="text-xl font-bold text-blue-400">E</span>
      </div>

      <el-menu
        active-text-color="#409EFF"
        background-color="#111827"
        class="el-menu-vertical-demo border-r-0"
        :default-active="route.path"
        text-color="#fff"
        :collapse="isCollapse"
        @open="handleOpen"
        @close="handleClose"
        router
      >
        <el-menu-item index="/">
          <el-icon><Odometer /></el-icon>
          <template #title>Dashboard</template>
        </el-menu-item>
        
        <el-menu-item index="/projects">
          <el-icon><Files /></el-icon>
          <template #title>Projects</template>
        </el-menu-item>

        <el-menu-item index="/assets">
          <el-icon><Monitor /></el-icon>
          <template #title>Assets</template>
        </el-menu-item>

        <el-menu-item index="/risks">
          <el-icon><WarnTriangleFilled /></el-icon>
          <template #title>Risks</template>
        </el-menu-item>
        
        <el-menu-item index="/tasks">
          <el-icon><Aim /></el-icon>
          <template #title>Tasks</template>
        </el-menu-item>

        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>Settings</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="bg-white border-b border-gray-200 flex items-center justify-between px-6 h-16">
        <div class="flex items-center">
          <button @click="isCollapse = !isCollapse" class="p-2 rounded hover:bg-gray-100 mr-4">
             <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
             </svg>
          </button>
          <h2 class="text-lg font-semibold text-gray-800">
             {{ route.name ? String(route.name).charAt(0).toUpperCase() + String(route.name).slice(1) : 'Dashboard' }}
          </h2>
        </div>
        
        <div class="flex items-center space-x-4">
          <el-dropdown>
            <span class="el-dropdown-link flex items-center cursor-pointer">
              <el-avatar :size="32" :icon="User" class="mr-2" />
              <span class="text-gray-700 font-medium">Admin User</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>Profile</el-dropdown-item>
                <el-dropdown-item>Logout</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="bg-gray-50 p-6">
        <RouterView v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 240px;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
