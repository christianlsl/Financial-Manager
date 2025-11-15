<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="hover">
      <template #header>
        <div class="auth-card__header">
          <h2>创建新账号</h2>
          <p>填写以下信息，即刻开启智能财务管理</p>
        </div>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" type="email" placeholder="name@example.com" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位字符" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password placeholder="再次输入密码" />
        </el-form-item>
        <el-divider content-position="left">公司信息</el-divider>
        <el-form-item label="公司名称" prop="company_name" required>
          <el-input v-model="form.company_name" placeholder="如：示例科技有限公司" />
        </el-form-item>
        <el-alert v-if="auth.error" :closable="false" type="error" class="auth-card__alert" :title="auth.error" />
        <div class="auth-card__actions">
          <el-button :loading="auth.loading" type="primary" size="large" @click="onSubmit">注册</el-button>
          <el-button size="large" link @click="goLogin">已有账号？立即登录</el-button>
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
  password: '',
  confirm: '',
  company_name: ''
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为 6 位', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (!value) {
          callback(new Error('请再次输入密码'))
        } else if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: ['blur', 'change']
    }
  ]
}

rules.company_name = [
  { required: true, message: '请输入公司名称', trigger: 'blur' }
]

async function onSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    // 后端仅需公司名称
    await auth.register(form.email, form.password, form.company_name.trim())
    ElMessage.success('注册成功，已自动登录')
    router.push('/dashboard')
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || '注册失败'
    ElMessage.error(message)
  }
}

function goLogin() {
  router.push('/login')
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
