<template>
  <router-view />
</template>

<script setup>
</script>

<style>
html, body, #app { height: 100%; margin: 0; }
body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji', sans-serif; }
a { color: #3e7bfa; text-decoration: none; }
nav { display: flex; gap: 12px; padding: 8px 16px; border-bottom: 1px solid #eee; }
.container { padding: 16px; max-width: 960px; margin: 0 auto; }
label { display: block; margin: 8px 0 4px; }
input, select, textarea { padding: 8px; width: 100%; box-sizing: border-box; }
button { padding: 8px 12px; cursor: pointer; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 8px; }
th { background: #f8f8f8; }
</style>
