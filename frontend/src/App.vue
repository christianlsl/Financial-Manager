<template>
  <el-config-provider :button="{ autoInsertSpace: true }">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import { ElConfigProvider } from 'element-plus'
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
}

body {
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  background: #f4f6f6;
}

a {
  color: var(--el-color-primary);
  text-decoration: none;
}

:root {
  --el-color-primary: #4b8b79;
  --el-color-primary-light-3: #6ca593;
  --el-color-primary-light-5: #81b5a2;
  --el-color-primary-light-7: #a2cab8;
  --el-color-primary-light-8: #b6d6c6;
  --el-color-primary-light-9: #d5e9df;
  --el-color-primary-dark-2: #3a6b5c;
}
</style>
