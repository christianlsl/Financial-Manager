<template>
  <div>
    <nav>
      <strong>Financial Manager</strong>
      <router-link to="/dashboard">总览</router-link>
      <router-link to="/purchases">采购</router-link>
      <router-link to="/sales">销售</router-link>
      <router-link to="/invoices">发票</router-link>
      <span style="flex:1"></span>
      <span>{{ auth.email }}</span>
      <button @click="logout">退出</button>
    </nav>
    <div class="container">
      <h2>总览</h2>
      <p>欢迎使用财务管理系统。</p>
      <ul>
        <li><router-link to="/purchases">管理采购清单</router-link></li>
        <li><router-link to="/sales">管理销售清单</router-link></li>
        <li><router-link to="/invoices">管理发票</router-link></li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
const router = useRouter()
const auth = useAuthStore()
function logout() {
  auth.logout()
  router.push('/login')
}
</script>
