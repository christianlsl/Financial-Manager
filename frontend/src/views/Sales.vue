<template>
  <AppShell>
    <el-space direction="vertical" size="large" class="sales">
      <div class="sales__header">
        <div>
          <h2>销售管理</h2>
          <p>掌握每一笔销售进度，从草稿到回款一目了然。</p>
        </div>
        <el-space>
          <el-button :loading="loading" plain @click="loadSales">
            <el-icon>
              <Refresh />
            </el-icon>
            刷新
          </el-button>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon>
              <Plus />
            </el-icon>
            新建销售
          </el-button>
        </el-space>
      </div>

      <el-card shadow="never" class="sales__filters">
        <el-form :inline="false" :model="filters" label-width="90px" class="sales__filters-form">
          <!-- 第一排：搜索 -->
          <el-row :gutter="16" class="filters-row">
            <el-col :span="24">
              <el-form-item label="搜索">
                <el-input v-model="filters.keyword" placeholder="客户、公司或项目关键字" clearable
                  style="max-width: 360px; width: 100%" @change="handleFilterChange" @clear="handleFilterChange"
                  @keydown.enter.prevent="handleFilterChange">
                  <template #prefix>
                    <el-icon>
                      <Search />
                    </el-icon>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 第二排：客户，公司 -->
          <el-row :gutter="16" class="filters-row">
            <el-col :xs="24" :sm="12">
              <el-form-item label="客户">
                <el-select v-model="filters.customerId" placeholder="全部客户" clearable filterable style="width: 100%"
                  @change="handleFilterChange">
                  <el-option v-for="customer in customers" :key="customer.id" :label="customerLabel(customer)"
                    :value="customer.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="公司">
                <el-select v-model="filters.companyId" placeholder="全部公司" clearable filterable style="width: 100%"
                  @change="handleFilterChange">
                  <el-option v-for="company in companies" :key="company.id" :label="company.name" :value="company.id" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 第三排：类型，状态 -->
          <el-row :gutter="16" class="filters-row">
            <el-col :xs="24" :sm="12">
              <el-form-item label="类型">
                <el-select v-model="filters.typeId" placeholder="全部类型" clearable filterable style="width: 100%"
                  @change="handleFilterChange">
                  <el-option v-for="type in types" :key="type.id" :label="type.name" :value="type.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="状态">
                <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 100%"
                  @change="handleFilterChange">
                  <el-option v-for="(option, key) in statusOptions" :key="key" :label="option.label" :value="key" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 第四排：日期，金额 -->
          <el-row :gutter="16" class="filters-row">
            <el-col :xs="24" :sm="12">
              <el-form-item label="日期">
                <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" clearable
                  start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" unlink-panels
                  style="width: 100%" @change="handleFilterChange" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="金额">
                <div class="sales__amount-range">
                  <el-input-number v-model="filters.amountMin" :min="0" :max="999999999" :controls="false"
                    placeholder="最小值" style="width: 120px" @change="handleFilterChange" />
                  <span class="sales__amount-separator">-</span>
                  <el-input-number v-model="filters.amountMax" :min="0" :max="999999999" :controls="false"
                    placeholder="最大值" style="width: 120px" @change="handleFilterChange" />
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>
      <el-card shadow="never" class="sales__table" v-loading="loading" style="overflow:auto">
        <template #header>
          <div class="sales__table-header">销售列表</div>
        </template>
        <el-empty v-if="!sales.length && !loading" description="暂无销售记录" />
        <div v-else class="sales__table-grid">
          <el-table :data="sales" border stripe>
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column label="项目">
              <template #default="{ row }">{{ row.item_name || '未填写' }}</template>
            </el-table-column>
            <el-table-column label="公司" width="160">
              <template #default="{ row }">{{ customerCompanyName(row.customer_id) }}</template>
            </el-table-column>
            <el-table-column label="客户" width="180">
              <template #default="{ row }">{{ customerName(row.customer_id) }}</template>
            </el-table-column>
            <el-table-column label="类型" width="140">
              <template #default="{ row }">{{ typeName(row.type_id) }}</template>
            </el-table-column>
            <el-table-column label="数量" width="90" prop="items_count" />
            <el-table-column label="单价" width="110">
              <template #default="{ row }">¥ {{ formatAmount(row.unit_price) }}</template>
            </el-table-column>
            <el-table-column label="金额" width="110">
              <template #default="{ row }">¥ {{ formatAmount(row.total_price) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="备注">
              <template #default="{ row }">{{ row.notes || '—' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-popconfirm title="确认删除该销售记录？" confirm-button-text="删除" cancel-button-text="取消"
                  @confirm="removeSale(row.id)">
                  <template #reference>
                    <el-button type="danger" text size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-pagination v-if="pagination.total > 0" class="sales__pagination" :total="pagination.total"
          :page-sizes="[10, 20, 50]" :page-size="pagination.pageSize" :current-page="pagination.page"
          layout="total, sizes, prev, pager, next" @current-change="handlePageChange"
          @size-change="handlePageSizeChange" />
      </el-card>
    </el-space>

    <el-dialog v-model="dialogVisible" title="新建销售" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="销售日期" prop="date">
          <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期"
            style="width: 100%" />
        </el-form-item>
        <el-form-item label="关联客户" prop="customer_id">
          <el-select v-model="form.customer_id" placeholder="选择客户" filterable>
            <el-option v-for="customer in customers" :key="customer.id" :label="customerLabel(customer)"
              :value="customer.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="销售类型" prop="type_id">
          <el-select v-model="form.type_id" placeholder="选择类型" clearable filterable>
            <el-option v-for="type in types" :key="type.id" :label="type.name" :value="type.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目内容" prop="item_name">
          <el-input v-model="form.item_name" placeholder="如：2025党代会横幅" />
        </el-form-item>
        <el-form-item label="销售数量" prop="items_count">
          <el-input-number v-model="form.items_count" :min="1" :max="999999" />
        </el-form-item>
        <el-form-item label="销售单价" prop="unit_price">
          <el-input-number v-model="form.unit_price" :min="0" :step="10" :precision="2" />
        </el-form-item>
        <el-form-item label="销售金额" prop="total_price">
          <el-input-number v-model="form.total_price" :min="0" :step="10" :precision="2" disabled />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio-button :value="'draft'">已下单</el-radio-button>
            <el-radio-button :value="'sent'">已送货</el-radio-button>
            <el-radio-button :value="'paid'">已支付</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="记录更多信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-space>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
        </el-space>
      </template>
    </el-dialog>
  </AppShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'

import AppShell from '../components/AppShell.vue'
import { useAuthStore, api } from '../stores/auth'

const auth = useAuthStore()

const sales = ref([])
const companies = ref([])
const customers = ref([])
const types = ref([])
const loading = ref(false)
const saving = ref(false)

const dialogVisible = ref(false)
const formRef = ref()
const form = reactive(createDefaultForm())
const filters = reactive({
  keyword: '',
  customerId: null,
  companyId: null,
  typeId: null,
  status: null,
  dateRange: [],
  amountMin: null,
  amountMax: null
})
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const rules = {
  date: [{ required: true, message: '请选择销售日期', trigger: 'change' }],
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  item_name: [{ required: true, message: '请输入项目内容', trigger: 'blur' }],
  items_count: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  unit_price: [{ required: true, message: '请输入单价', trigger: 'blur' }]
}

const statusOptions = computed(() => ({
  draft: { label: '已下单', type: 'danger' },
  sent: { label: '已送货', type: 'warning' },
  paid: { label: '已支付', type: 'success' }
}))

function createDefaultForm() {
  return {
    date: new Date().toISOString().slice(0, 10),
    customer_id: null,
    type_id: null,
    item_name: '',
    items_count: 1,
    unit_price: 0,
    total_price: 0,
    status: 'draft',
    notes: ''
  }
}

watch(
  () => [form.items_count, form.unit_price],
  ([count, price]) => {
    const normalizedCount = Number(count) || 0
    const normalizedPrice = Number(price) || 0
    form.total_price = Number((normalizedCount * normalizedPrice).toFixed(2))
  },
  { immediate: true }
)

function formatAmount(value) {
  return Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function statusLabel(status) {
  return statusOptions.value[status]?.label || '草稿'
}

function statusType(status) {
  return statusOptions.value[status]?.type || 'info'
}

function companyName(id) {
  if (id === 0) return '个人客户'
  if (id === null || id === undefined) return '—'
  return companies.value.find((item) => item.id === id)?.name || '—'
}

function typeName(id) {
  if (!id) return '—'
  return types.value.find((item) => item.id === id)?.name || '—'
}

function customerLabel(customer) {
  if (!customer) return '—'
  const label = customer.name || `客户 #${customer.id}`
  const company = companyName(customer.company_id)
  return company && company !== '—' ? `${label}（${company}）` : label
}

function customerName(id) {
  const customer = customers.value.find((item) => item.id === id)
  return customer ? customerLabel(customer) : `客户 #${id}`
}

function customerCompanyName(id) {
  const customer = customers.value.find((item) => item.id === id)
  if (!customer) return '—'
  return companyName(customer.company_id)
}

function flattenCustomers(groups) {
  const flat = []
  for (const group of groups || []) {
    const fallbackCompanyId = typeof group?.company_id === 'number' ? group.company_id : 0
    for (const customer of group?.customers || []) {
      const resolvedCompanyId = typeof customer.company_id === 'number' ? customer.company_id : fallbackCompanyId
      flat.push({ ...customer, company_id: resolvedCompanyId })
    }
  }
  flat.sort((a, b) => (a.name || '').localeCompare(b.name || '', 'zh-CN'))
  return flat
}

function openCreateDialog() {
  Object.assign(form, createDefaultForm())
  dialogVisible.value = true
}

async function loadLookups() {
  try {
    const [{ data: companyData }, { data: customerGroups }, { data: typeData }] = await Promise.all([
      api.get('/companies/', { params: { limit: 200 } }),
      api.get('/customers/', { params: { limit: 300 } }),
      api.get('/types/', { params: { limit: 200 } })
    ])
    companies.value = companyData || []
    customers.value = flattenCustomers(customerGroups)
    types.value = typeData || []
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载基础数据失败'
    ElMessage.error(message)
  }
}

async function loadSales() {
  loading.value = true
  try {
    auth.ensureInterceptors()
    const params = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    }
    if (filters.customerId) params.customer_id = filters.customerId
    if (filters.typeId) params.type_id = filters.typeId
    if (filters.companyId) params.company_id = filters.companyId
    if (filters.status) params.status = filters.status
    if (Array.isArray(filters.dateRange) && filters.dateRange.length === 2) {
      params.date_from = filters.dateRange[0]
      params.date_to = filters.dateRange[1]
    }
    const keyword = filters.keyword?.trim()
    if (keyword) params.search = keyword

    const minAmount = Number(filters.amountMin)
    const maxAmount = Number(filters.amountMax)
    if (!Number.isNaN(minAmount) && filters.amountMin !== null && filters.amountMin !== undefined) {
      params.amount_min = minAmount
    }
    if (!Number.isNaN(maxAmount) && filters.amountMax !== null && filters.amountMax !== undefined) {
      params.amount_max = maxAmount
    }
    const { data } = await api.get('/sales/', { params })
    const items = Array.isArray(data?.items) ? data.items : []
    sales.value = items
    pagination.total = Number(data?.total ?? items.length)
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载销售数据失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    saving.value = true
    const payload = { ...form }
    if (payload.customer_id !== null && payload.customer_id !== undefined) {
      payload.customer_id = Number(payload.customer_id)
    }
    if (!payload.type_id) payload.type_id = null
    else payload.type_id = Number(payload.type_id)
    if (!payload.item_name) payload.item_name = null
    if (!payload.notes) payload.notes = null
    await api.post('/sales/', payload)
    ElMessage.success('创建销售成功')
    dialogVisible.value = false
    pagination.page = 1
    await loadSales()
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || '创建销售失败'
    ElMessage.error(message)
  } finally {
    saving.value = false
  }
}

async function removeSale(id) {
  try {
    await api.delete(`/sales/${id}`)
    ElMessage.success('删除成功')
    pagination.total = Math.max(0, pagination.total - 1)
    sales.value = sales.value.filter((item) => item.id !== id)
    if (!sales.value.length && pagination.page > 1) {
      pagination.page -= 1
      await loadSales()
    }
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '删除失败'
    ElMessage.error(message)
  }
}

function handleFilterChange() {
  pagination.page = 1
  loadSales()
}

function handlePageChange(page) {
  pagination.page = page
  loadSales()
}

function handlePageSizeChange(size) {
  pagination.pageSize = size
  pagination.page = 1
  loadSales()
}

onMounted(async () => {
  auth.ensureInterceptors()
  await loadLookups()
  await loadSales()
})
</script>

<style scoped>
.sales {
  width: 100%;
}

.sales__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.sales__header h2 {
  margin: 0;
  font-size: 26px;
  color: #1f2d3d;
}

.sales__header p {
  margin: 6px 0 0;
  color: #66757f;
}

.sales__filters,
.sales__table {
  border-radius: 14px;
  border: none;
  background: #ffffff;
  margin: 0 auto;
  box-sizing: border-box;
}

.sales__filters-form {
  display: block;
}

.filters-row+.filters-row {
  margin-top: 8px;
}

.sales__filters-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.sales__amount-range {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sales__amount-separator {
  color: #909399;
}

.sales__table-header {
  font-weight: 600;
}

.sales__pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.sales__table-grid {
  display: grid;
  /* grid-template-columns: 1fr;
  min-width: 0; */
  /* overflow: auto; */
}
</style>
