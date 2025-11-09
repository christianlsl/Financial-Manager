<template>
  <div>
    <nav>
      <strong>Financial Manager</strong>
      <span style="flex:1"></span>
      <router-link to="/register">注册</router-link>
    </nav>
    <div class="container">
      <h2>登录</h2>
      <form @submit.prevent="onSubmit">
        <label>邮箱</label>
        <input v-model="email" type="email" required />
        <label>密码</label>
        <input v-model="password" type="password" required />
        <div style="margin-top:12px">
          <button :disabled="auth.loading" type="submit">登录</button>
        </div>
        <p v-if="auth.error" style="color:red">{{ auth.error }}</p>
      </form>
    </div>
  </div>
  </template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')

async function onSubmit() {
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    // error shown by store
  }
}
</script>
