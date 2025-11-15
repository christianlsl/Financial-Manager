<template>
  <AppShell>
    <el-space direction="vertical" size="large" class="catalogs">
      <div class="catalogs__header">
        <div>
          <h2>业务资料管理</h2>
          <p>维护公司与业务类型，便于在采购与销售中快速引用。</p>
        </div>
        <el-button :loading="loading" type="primary" plain @click="loadAll">同步数据</el-button>
      </div>

      <el-card shadow="never" class="catalogs__card">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="客户" name="customers">
            <div class="catalogs__toolbar catalogs__toolbar--between">
              <div class="catalogs__filters">
                <el-select v-model="customerFilterCompanyId" placeholder="筛选公司" style="min-width: 200px">
                  <el-option :value="ALL_COMPANY_VALUE" label="全部客户" />
                  <el-option :value="PERSONAL_COMPANY_VALUE" label="个人客户" />
                  <el-option v-for="item in companies" :key="item.id" :value="item.id" :label="item.name" />
                </el-select>
              </div>
              <el-button type="primary" @click="openCustomerDialog()">
                <el-icon>
                  <User />
                </el-icon>
                新建客户
              </el-button>
            </div>
            <el-table :data="filteredCustomers" border stripe v-loading="loadingCustomers">
              <el-table-column prop="name" label="客户名称" min-width="200" />
              <el-table-column label="所属公司" min-width="180">
                <template #default="{ row }">{{ getCompanyName(row.company_id) }}</template>
              </el-table-column>
              <el-table-column prop="position" label="职位" min-width="140">
                <template #default="{ row }">{{ row.position || '—' }}</template>
              </el-table-column>
              <el-table-column prop="phone_number" label="联系电话" min-width="160">
                <template #default="{ row }">{{ row.phone_number || '—' }}</template>
              </el-table-column>
              <el-table-column prop="email" label="邮箱" min-width="200">
                <template #default="{ row }">{{ row.email || '—' }}</template>
              </el-table-column>
              <el-table-column label="操作" width="160" fixed="right">
                <template #default="{ row }">
                  <el-space>
                    <el-button type="primary" link size="small" @click="openCustomerDialog(row)">编辑</el-button>
                    <el-popconfirm title="确认删除该客户？" confirm-button-text="删除" cancel-button-text="取消"
                      @confirm="removeCustomer(row.id)">
                      <template #reference>
                        <el-button type="danger" link size="small">删除</el-button>
                      </template>
                    </el-popconfirm>
                  </el-space>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!filteredCustomers.length && !loadingCustomers" description="暂无客户数据" />
          </el-tab-pane>

          <el-tab-pane label="公司" name="companies">
            <div class="catalogs__toolbar">
              <el-button type="primary" @click="openCompanyDialog()">
                <el-icon>
                  <OfficeBuilding />
                </el-icon>
                新建公司
              </el-button>
            </div>
            <el-table :data="companies" border stripe v-loading="loadingCompanies">
              <el-table-column prop="name" label="公司名称" min-width="160" />
              <el-table-column prop="legal_person" label="法人代表" min-width="120">
                <template #default="{ row }">{{ row.legal_person || '—' }}</template>
              </el-table-column>
              <el-table-column prop="phone" label="联系电话" min-width="140">
                <template #default="{ row }">{{ row.phone || '—' }}</template>
              </el-table-column>
              <el-table-column prop="email" label="邮箱" min-width="160">
                <template #default="{ row }">{{ row.email || '—' }}</template>
              </el-table-column>
              <el-table-column prop="address" label="地址" min-width="200">
                <template #default="{ row }">{{ row.address || '—' }}</template>
              </el-table-column>
              <el-table-column label="操作" width="160" fixed="right">
                <template #default="{ row }">
                  <el-space>
                    <el-button type="primary" link size="small" @click="openCompanyDialog(row)">编辑</el-button>
                    <el-popconfirm title="确认删除该公司？" confirm-button-text="删除" cancel-button-text="取消"
                      @confirm="removeCompany(row.id)">
                      <template #reference>
                        <el-button type="danger" link size="small">删除</el-button>
                      </template>
                    </el-popconfirm>
                  </el-space>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!companies.length && !loadingCompanies" description="暂无公司数据" />
          </el-tab-pane>

          <el-tab-pane label="物料类型" name="types">
            <div class="catalogs__toolbar">
              <el-button type="primary" @click="openTypeDialog()">
                <el-icon>
                  <Ticket />
                </el-icon>
                新建类型
              </el-button>
            </div>
            <el-table :data="types" border stripe v-loading="loadingTypes">
              <el-table-column prop="name" label="类型名称" min-width="200" />
              <el-table-column label="操作" width="160" fixed="right">
                <template #default="{ row }">
                  <el-space>
                    <el-button type="primary" link size="small" @click="openTypeDialog(row)">编辑</el-button>
                    <el-popconfirm title="确认删除该类型？" confirm-button-text="删除" cancel-button-text="取消"
                      @confirm="removeType(row.id)">
                      <template #reference>
                        <el-button type="danger" link size="small">删除</el-button>
                      </template>
                    </el-popconfirm>
                  </el-space>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!types.length && !loadingTypes" description="暂无类型数据" />
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </el-space>

    <el-dialog v-model="customerDialog.visible" :title="customerDialog.isEdit ? '编辑客户' : '新建客户'" width="520px"
      destroy-on-close>
      <el-form ref="customerFormRef" :model="customerDialog.form" :rules="customerRules" label-width="96px">
        <el-form-item label="客户名称" prop="name">
          <el-input v-model="customerDialog.form.name" placeholder="请输入客户名称" />
        </el-form-item>
        <el-form-item label="所属公司" prop="company_id">
          <el-select v-model="customerDialog.form.company_id" placeholder="请选择公司或个人">
            <el-option :value="PERSONAL_COMPANY_VALUE" label="个人客户" />
            <el-option v-for="item in companies" :key="item.id" :value="item.id" :label="item.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="职位" prop="position">
          <el-input v-model="customerDialog.form.position" placeholder="请输入职位" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone_number">
          <el-input v-model="customerDialog.form.phone_number" placeholder="请输入电话号码" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="customerDialog.form.email" placeholder="name@example.com" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-space>
          <el-button @click="customerDialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="customerDialog.loading" @click="submitCustomer">保存</el-button>
        </el-space>
      </template>
    </el-dialog>

    <el-dialog v-model="companyDialog.visible" :title="companyDialog.isEdit ? '编辑公司' : '新建公司'" width="560px"
      destroy-on-close>
      <el-form ref="companyFormRef" :model="companyDialog.form" :rules="companyRules" label-width="96px">
        <el-form-item label="公司名称" prop="name">
          <el-input v-model="companyDialog.form.name" placeholder="请输入公司名称" />
        </el-form-item>
        <el-form-item label="法人代表" prop="legal_person">
          <el-input v-model="companyDialog.form.legal_person" placeholder="如：张三" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="companyDialog.form.phone" placeholder="请输入电话号码" />
        </el-form-item>
        <el-form-item label="联系邮箱" prop="email">
          <el-input v-model="companyDialog.form.email" placeholder="name@company.com" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="companyDialog.form.address" type="textarea" :rows="3" placeholder="详细地址" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-space>
          <el-button @click="companyDialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="companyDialog.loading" @click="submitCompany">保存</el-button>
        </el-space>
      </template>
    </el-dialog>

    <el-dialog v-model="typeDialog.visible" :title="typeDialog.isEdit ? '编辑类型' : '新建类型'" width="420px" destroy-on-close>
      <el-form ref="typeFormRef" :model="typeDialog.form" :rules="typeRules" label-width="96px">
        <el-form-item label="类型名称" prop="name">
          <el-input v-model="typeDialog.form.name" placeholder="请输入类型名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-space>
          <el-button @click="typeDialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="typeDialog.loading" @click="submitType">保存</el-button>
        </el-space>
      </template>
    </el-dialog>
  </AppShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { OfficeBuilding, Ticket, User } from '@element-plus/icons-vue'

import AppShell from '../components/AppShell.vue'
import { useAuthStore, api } from '../stores/auth'

const auth = useAuthStore()

const activeTab = ref('customers')
const companies = ref([])
const types = ref([])
const loading = ref(false)
const loadingCompanies = ref(false)
const loadingCustomers = ref(false)
const loadingTypes = ref(false)
const customers = ref([])

const ALL_COMPANY_VALUE = 'all'
const PERSONAL_COMPANY_VALUE = 0
const customerFilterCompanyId = ref(ALL_COMPANY_VALUE)

const filteredCustomers = computed(() => {
  const filter = customerFilterCompanyId.value
  if (filter === ALL_COMPANY_VALUE) return customers.value
  if (filter === PERSONAL_COMPANY_VALUE) return customers.value.filter((item) => item.company_id === 0)
  return customers.value.filter((item) => item.company_id === filter)
})

const companyDialog = reactive({
  visible: false,
  isEdit: false,
  loading: false,
  form: createCompanyForm()
})

const customerDialog = reactive({
  visible: false,
  isEdit: false,
  loading: false,
  form: createCustomerForm()
})

const typeDialog = reactive({
  visible: false,
  isEdit: false,
  loading: false,
  form: createTypeForm()
})

const companyFormRef = ref()
const customerFormRef = ref()
const typeFormRef = ref()

const companyRules = {
  name: [{ required: true, message: '请输入公司名称', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }]
}

const customerRules = {
  name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  company_id: [{ required: true, message: '请选择所属公司', trigger: 'change' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }]
}

const typeRules = {
  name: [{ required: true, message: '请输入类型名称', trigger: 'blur' }]
}

function createCompanyForm() {
  return {
    id: null,
    name: '',
    legal_person: '',
    phone: '',
    email: '',
    address: ''
  }
}

function createCustomerForm() {
  return {
    id: null,
    name: '',
    phone_number: '',
    email: '',
    position: '',
    company_id: PERSONAL_COMPANY_VALUE
  }
}

function createTypeForm() {
  return {
    id: null,
    name: ''
  }
}

function getCompanyName(companyId) {
  if (companyId === 0) return '个人客户'
  if (companyId === null || companyId === undefined) return '—'
  const company = companies.value.find((item) => item.id === companyId)
  return company?.name || `公司 #${companyId}`
}

async function loadCompanies() {
  loadingCompanies.value = true
  try {
    const { data } = await api.get('/companies/', { params: { limit: 200 } })
    companies.value = data
    if (typeof customerFilterCompanyId.value === 'number' && customerFilterCompanyId.value > 0) {
      const exists = data.some((item) => item.id === customerFilterCompanyId.value)
      if (!exists) customerFilterCompanyId.value = ALL_COMPANY_VALUE
    }
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载公司列表失败'
    ElMessage.error(message)
  } finally {
    loadingCompanies.value = false
  }
}

async function loadCustomers() {
  loadingCustomers.value = true
  try {
    const { data } = await api.get('/customers/', { params: { limit: 300 } })
    customers.value = (data || []).flatMap((group) => {
      const resolvedGroupCompanyId = typeof group.company_id === 'number' ? group.company_id : PERSONAL_COMPANY_VALUE
      return (group.customers || []).map((customer) => {
        const customerCompanyId = typeof customer.company_id === 'number' ? customer.company_id : resolvedGroupCompanyId
        return {
          ...customer,
          company_id: customerCompanyId
        }
      })
    })
    customers.value.sort((a, b) => {
      const companyA = a.company_id ?? -1
      const companyB = b.company_id ?? -1
      if (companyA !== companyB) return companyA - companyB
      return a.id - b.id
    })
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载客户列表失败'
    ElMessage.error(message)
  } finally {
    loadingCustomers.value = false
  }
}

async function loadTypes() {
  loadingTypes.value = true
  try {
    const { data } = await api.get('/types/', { params: { limit: 200 } })
    types.value = data
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载类型列表失败'
    ElMessage.error(message)
  } finally {
    loadingTypes.value = false
  }
}

async function loadAll() {
  loading.value = true
  try {
    await Promise.all([loadCompanies(), loadCustomers(), loadTypes()])
  } finally {
    loading.value = false
  }
}

function openCompanyDialog(company) {
  companyDialog.visible = true
  companyDialog.isEdit = Boolean(company)
  Object.assign(companyDialog.form, createCompanyForm(), company || {})
}

function openCustomerDialog(customer) {
  customerDialog.visible = true
  customerDialog.isEdit = Boolean(customer)
  Object.assign(customerDialog.form, createCustomerForm())
  if (customer) {
    customerDialog.form.id = customer.id
    customerDialog.form.name = customer.name || ''
    customerDialog.form.phone_number = customer.phone_number || ''
    customerDialog.form.email = customer.email || ''
    customerDialog.form.position = customer.position || ''
    customerDialog.form.company_id = typeof customer.company_id === 'number' ? customer.company_id : PERSONAL_COMPANY_VALUE
  } else {
    if (customerFilterCompanyId.value === PERSONAL_COMPANY_VALUE) {
      customerDialog.form.company_id = PERSONAL_COMPANY_VALUE
    } else if (customerFilterCompanyId.value !== ALL_COMPANY_VALUE) {
      customerDialog.form.company_id = customerFilterCompanyId.value
    } else {
      customerDialog.form.company_id = PERSONAL_COMPANY_VALUE
    }
  }
}

function openTypeDialog(type) {
  typeDialog.visible = true
  typeDialog.isEdit = Boolean(type)
  Object.assign(typeDialog.form, createTypeForm(), type || {})
}

async function submitCompany() {
  if (!companyFormRef.value) return
  try {
    await companyFormRef.value.validate()
    companyDialog.loading = true
    const payload = { ...companyDialog.form }
    const companyId = payload.id
    if (!payload.legal_person) payload.legal_person = null
    if (!payload.phone) payload.phone = null
    if (!payload.email) payload.email = null
    if (!payload.address) payload.address = null
    delete payload.id
    if (companyDialog.isEdit && companyId) {
      await api.put(`/companies/${companyId}`, payload)
      ElMessage.success('更新公司成功')
    } else {
      await api.post('/companies/', payload)
      ElMessage.success('创建公司成功')
    }
    companyDialog.visible = false
    await loadCompanies()
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || '保存公司失败'
    ElMessage.error(message)
  } finally {
    companyDialog.loading = false
  }
}

async function removeCompany(id) {
  const hasCustomers = customers.value.some((item) => item.company_id === id)
  if (hasCustomers) {
    ElMessage.error('请先删除该公司下的客户')
    return
  }
  try {
    await api.delete(`/companies/${id}`)
    ElMessage.success('删除公司成功')
    await loadCompanies()
    await loadCustomers()
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '删除公司失败'
    ElMessage.error(message)
  }
}

async function submitCustomer() {
  if (!customerFormRef.value) return
  try {
    await customerFormRef.value.validate()
    customerDialog.loading = true
    const payload = { ...customerDialog.form }
    const customerId = payload.id
    delete payload.id
    payload.name = payload.name?.trim() || ''
    customerDialog.form.name = payload.name
    const trimmedPhone = payload.phone_number ? payload.phone_number.trim() : ''
    const trimmedEmail = payload.email ? payload.email.trim() : ''
    const trimmedPosition = payload.position ? payload.position.trim() : ''
    customerDialog.form.phone_number = trimmedPhone
    customerDialog.form.email = trimmedEmail
    customerDialog.form.position = trimmedPosition
    if (!payload.name) {
      ElMessage.error('请输入客户名称')
      return
    }
    const numericCompanyId = Number(payload.company_id)
    if (!Number.isFinite(numericCompanyId) || numericCompanyId < 0) {
      ElMessage.error('请选择所属公司')
      return
    }
    payload.company_id = numericCompanyId
    payload.phone_number = trimmedPhone || null
    payload.email = trimmedEmail || null
    payload.position = trimmedPosition || null
    if (customerDialog.isEdit && customerId) {
      await api.put(`/customers/${customerId}`, payload)
      ElMessage.success('更新客户成功')
    } else {
      await api.post('/customers/', payload)
      ElMessage.success('创建客户成功')
    }
    customerDialog.visible = false
    await loadCustomers()
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || '保存客户失败'
    ElMessage.error(message)
  } finally {
    customerDialog.loading = false
  }
}

async function removeCustomer(id) {
  try {
    await api.delete(`/customers/${id}`)
    ElMessage.success('删除客户成功')
    await loadCustomers()
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '删除客户失败'
    ElMessage.error(message)
  }
}

async function submitType() {
  if (!typeFormRef.value) return
  try {
    await typeFormRef.value.validate()
    typeDialog.loading = true
    const payload = { ...typeDialog.form }
    const typeId = payload.id
    delete payload.id
    if (typeDialog.isEdit && typeId) {
      await api.put(`/types/${typeId}`, payload)
      ElMessage.success('更新类型成功')
    } else {
      await api.post('/types/', payload)
      ElMessage.success('创建类型成功')
    }
    typeDialog.visible = false
    await loadTypes()
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || '保存类型失败'
    ElMessage.error(message)
  } finally {
    typeDialog.loading = false
  }
}

async function removeType(id) {
  try {
    await api.delete(`/types/${id}`)
    ElMessage.success('删除类型成功')
    types.value = types.value.filter((item) => item.id !== id)
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '删除类型失败'
    ElMessage.error(message)
  }
}

onMounted(async () => {
  auth.ensureInterceptors()
  await loadAll()
})
</script>

<style scoped>
.catalogs {
  width: 100%;
}

.catalogs__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.catalogs__header h2 {
  margin: 0;
  font-size: 26px;
  color: #1f2d3d;
}

.catalogs__header p {
  margin: 6px 0 0;
  color: #66757f;
}

.catalogs__card {
  border-radius: 14px;
  border: none;
  background: #ffffff;
}

.catalogs__toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.catalogs__toolbar--between {
  justify-content: space-between;
  align-items: center;
}

.catalogs__filters {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
