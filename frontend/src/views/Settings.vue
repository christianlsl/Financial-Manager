<template>
  <AppShell>
    <el-space direction="vertical" size="large" class="settings">
      <div class="settings__header">
        <div>
          <h2>个人设置</h2>
        </div>
      </div>
      <el-row>
        <!-- xs: <576px（手机手机竖屏）；sm: ≥576px（手机横屏）；md: ≥768px（平板）；
         lg: ≥992px（小桌面）；xl: ≥1200px（桌面）；xxl: ≥1600px（大桌面/显示器） -->
        <el-col :span="24">
          <el-card shadow="never" class="settings__card" v-loading="loadingProfile">
            <template #header>
              <div class="settings__card-header settings__card-header--actions">
                <span>账号信息</span>
                <el-button type="primary" link @click="openProfileDialog">编辑</el-button>
              </div>
            </template>
            <el-descriptions :column="1" border style="margin-bottom: 10px;">
              <el-descriptions-item label="邮箱">{{ profile.email }}</el-descriptions-item>
              <el-descriptions-item label="所属公司">{{ profile.company_name || '—' }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatDate(profile.created_at) }}</el-descriptions-item>
            </el-descriptions>
            <el-button type="primary" @click="pwdDialogVisible = true">修改密码</el-button>
          </el-card>
        </el-col>
      </el-row>

      <el-dialog v-model="pwdDialogVisible" title="修改密码" width="480px" destroy-on-close>
        <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="100px">
          <el-form-item label="当前密码" prop="current">
            <el-input v-model="pwdForm.current" type="password" show-password placeholder="输入当前密码" />
          </el-form-item>
          <el-form-item label="新密码" prop="newPwd">
            <el-input v-model="pwdForm.newPwd" type="password" show-password placeholder="至少 6 位字符" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirm">
            <el-input v-model="pwdForm.confirm" type="password" show-password placeholder="再次输入新密码" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-space>
            <el-button @click="pwdDialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="savingPwd" @click="changePassword">保存</el-button>
          </el-space>
        </template>
      </el-dialog>


      <el-dialog v-model="profileDialogVisible" title="修改个人信息" width="520px" destroy-on-close>
        <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-width="110px">
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="profileForm.email" type="email" placeholder="name@example.com" />
          </el-form-item>
          <el-form-item label="公司名称" prop="company_name">
            <el-input v-model="profileForm.company_name" placeholder="请输入公司名称" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-space>
            <el-button @click="profileDialogVisible = false" :disabled="savingProfile">取消</el-button>
            <el-button type="primary" :loading="savingProfile" @click="saveProfile">保存并重新登录</el-button>
          </el-space>
        </template>
      </el-dialog>
    </el-space>
  </AppShell>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import AppShell from '../components/AppShell.vue'
import { useAuthStore, api } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const loadingProfile = ref(false)
const savingPwd = ref(false)
const pwdDialogVisible = ref(false)
const profileDialogVisible = ref(false)
const savingProfile = ref(false)

const profile = reactive({ email: auth.email, company_name: '', created_at: null })
const companyForm = reactive({ name: '', address: '', legal_person: '', phone: '', email: auth.email })


const pwdFormRef = ref()
const pwdForm = reactive({ current: '', newPwd: '', confirm: '' })
const pwdRules = {
  current: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPwd: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '至少 6 位字符', trigger: 'blur' }
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_r, v, cb) => {
        if (!v) cb(new Error('请再次输入新密码'))
        else if (v !== pwdForm.newPwd) cb(new Error('两次输入不一致'))
        else cb()
      },
      trigger: ['blur', 'change']
    }
  ]
}

const bindForm = reactive({ company_id: null })
const profileFormRef = ref()
const profileForm = reactive({ email: auth.email || '', company_name: '' })
const profileRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }
  ],
  company_name: [{ required: true, message: '请输入公司名称', trigger: 'blur' }]
}

// Removed type management (types list & dialog)

function resetPwdForm() {
  Object.assign(pwdForm, { current: '', newPwd: '', confirm: '' })
}

function formatDate(s) {
  if (!s) return '—'
  try {
    const d = new Date(s)
    return d.toLocaleString()
  } catch {
    return s
  }
}

async function loadProfile() {
  loadingProfile.value = true
  try {
    const { data } = await api.get('/auth/me')
    profile.email = data.email
    profile.company_id = data.company_id
    profile.company_name = data.company_name || ''
    profile.created_at = data.created_at
    bindForm.company_id = data.company_id
    if (!companyForm.email) companyForm.email = profile.email || ''
    profileForm.email = profile.email || ''
    profileForm.company_name = profile.company_name || ''
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载资料失败'
    ElMessage.error(message)
  } finally {
    loadingProfile.value = false
  }
}

function openProfileDialog() {
  profileForm.email = profile.email || ''
  profileForm.company_name = profile.company_name || ''
  profileDialogVisible.value = true
}

async function saveProfile() {
  if (!profileFormRef.value) return
  try {
    await profileFormRef.value.validate()
    savingProfile.value = true
    const payload = {
      email: profileForm.email,
      company_name: profileForm.company_name.trim()
    }
    await api.put('/auth/update-profile', payload)
    ElMessage.success('个人信息已更新，请重新登录')
    profileDialogVisible.value = false
    auth.logout()
    router.replace('/login')
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || '更新个人信息失败'
    ElMessage.error(message)
  } finally {
    savingProfile.value = false
  }
}

async function changePassword() {
  if (!pwdFormRef.value) return
  try {
    await pwdFormRef.value.validate()
    savingPwd.value = true
    await api.post('/auth/change-password', { current_password: pwdForm.current, new_password: pwdForm.newPwd })
    ElMessage.success('密码已更新')
    resetPwdForm()
    pwdDialogVisible.value = false
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || '修改密码失败'
    ElMessage.error(message)
  } finally {
    savingPwd.value = false
  }
}


onMounted(async () => {
  auth.ensureInterceptors()
  await loadProfile()
})
</script>

<style scoped>
.settings {
  width: 100%;
}

.settings__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.settings__header h2 {
  margin: 0;
  font-size: 26px;
  color: #1f2d3d;
}

.settings__header p {
  margin: 6px 0 0;
  color: #66757f;
}

.settings__card {
  border-radius: 14px;
  border: none;
  background: #ffffff;
}

.settings__card-header {
  font-weight: 600;
}

.settings__card-header--actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
