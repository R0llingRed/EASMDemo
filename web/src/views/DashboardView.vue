<script setup lang="ts">
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">Dashboard</h1>
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Total Assets</span>
            </div>
          </template>
          <div class="text-3xl font-bold text-blue-600">1,234</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Critical Risks</span>
            </div>
          </template>
          <div class="text-3xl font-bold text-red-600">5</div>
        </el-card>
      </el-col>
       <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Active Tasks</span>
            </div>
          </template>
          <div class="text-3xl font-bold text-green-600">3</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
