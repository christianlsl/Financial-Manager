<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="hover">
      <template #header>
        <div class="auth-card__header">
          <h2>欢迎回来</h2>
          <p>登录以继续管理您的财务数据</p>
        </div>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" type="email" placeholder="name@example.com" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-alert v-if="auth.error" :closable="false" type="error" class="auth-card__alert" :title="auth.error" />
        <div class="auth-card__actions">
          <el-button :loading="auth.loading" type="primary" size="large" @click="onSubmit">登录</el-button>
          <el-button size="large" link @click="goRegister">还没有账号？立即注册</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const formRef = ref()
const form = reactive({
  email: '',
  password: ''
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为 6 位', trigger: 'blur' }
  ]
}

async function onSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    await auth.login(form.email, form.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || '登录失败'
    ElMessage.error(message)
  }
}

function goRegister() {
  router.push('/register')
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: radial-gradient(circle at top, rgba(75, 139, 121, 0.14), transparent), #f4f6f6;
}

.auth-card {
  width: 420px;
  max-width: 100%;
  border: none;
  border-radius: 16px;
}

.auth-card__header h2 {
  margin: 0;
  font-size: 24px;
  color: #1f2d3d;
}

.auth-card__header p {
  margin: 8px 0 0;
  color: #5c6b77;
  font-size: 14px;
}

.auth-card__actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.auth-card__alert {
  margin-bottom: 12px;
}
</style>
