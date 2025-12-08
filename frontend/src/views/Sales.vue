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
          <el-button @click="downloadCsv" plain>
            <el-icon>
              <Download />
            </el-icon>
            下载表格
          </el-button>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon>
              <Plus />
            </el-icon>
            新建销售
          </el-button>
        </el-space>
      </div>

      <el-card shadow="always" class="sales__filters">
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

          <!-- 第二排：客户，公司，部门 -->
          <el-row :gutter="16" class="filters-row">
            <el-col :xs="24" :sm="8" :md="8">
              <el-form-item label="客户类型">
                <el-radio-group v-model="filters.customerType" @change="handleCustomerTypeChange">
                  <el-radio-button :value="'company'">公司客户</el-radio-button>
                  <el-radio-button :value="'personal'">个人客户</el-radio-button>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col v-if="filters.customerType === 'company'" :xs="24" :sm="8" :md="6">
              <el-form-item label="公司">
                <el-select v-model="filters.companyId" placeholder="全部公司" clearable filterable style="width: 100%"
                  @change="handleFilterChange">
                  <el-option v-for="company in companies" :key="company.id" :label="company.name" :value="company.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col v-if="filters.customerType === 'company'" :xs="24" :sm="8" :md="4">
              <el-form-item label="部门">
                <el-select v-model="filters.departmentId" placeholder="全部部门" clearable filterable style="width: 100%"
                  @change="handleFilterChange">
                  <el-option v-for="dept in departmentOptions" :key="dept.id" :label="dept.name" :value="dept.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="8" :md="6">
              <el-form-item label="客户">
                <el-select v-model="filters.customerId" placeholder="全部客户" clearable filterable style="width: 100%"
                  @change="handleFilterChange">
                  <el-option v-for="customer in filterCustomerOptions" :key="customer.id"
                    :label="customerLabel(customer)" :value="customer.id" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 第三排：类型，状态 -->
          <el-row :gutter="16" class="filters-row">
            <el-col :xs="24" :sm="12">
              <el-form-item label="物料类型">
                <el-select v-model="filters.typeId" placeholder="全部类型" clearable filterable style="width: 100%"
                  @change="handleFilterChange">
                  <el-option v-for="type in types" :key="type.id" :label="type.name" :value="type.id" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="货品状态">
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
      <el-card shadow="always" class="sales__table" v-loading="loading" style="overflow:auto">
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
            <el-table-column label="部门" width="140">
              <template #default="{ row }">
                {{ row.customer_department?.name || '—' }}
              </template>
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
            <el-table-column label="图片" width="160">
              <template #default="{ row }">
                <div class="sales__image-cell">
                  <el-image v-if="row.image_url" :src="row.image_url" class="sales__image-thumb" fit="cover"
                    :preview-src-list="[row.image_url]" :preview-teleported="true" />
                  <div v-else class="sales__image-placeholder">无</div>
                  <el-upload class="sales__image-upload" accept="image/*" :limit="1" :show-file-list="false"
                    :http-request="(options) => handleRowImageUpload(options, row)"
                    :on-exceed="(files) => handleRowImageExceed(files, row)">
                    <el-button type="info" plain size="small" :loading="!!rowImageUploading[row.id]"
                      :disabled="!!rowImageUploading[row.id]">
                      上传/修改
                    </el-button>
                  </el-upload>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-popover v-model:visible="statusPopoverVisible[row.id]" trigger="click" placement="top"
                  :close-on-click-outside="true" :close-on-click="false">
                  <template #reference>
                    <el-tag :type="statusType(row.status)" size="small" @click.stop>
                      {{ statusLabel(row.status) }}
                    </el-tag>
                  </template>
                  <el-select v-model="editingStatus[row.id]" placeholder="选择状态" size="small" style="width: 120px"
                    :loading="isUpdatingStatus[row.id]" :disabled="isUpdatingStatus[row.id]"
                    @change="handleStatusChange(row.id)"
                    @visible-change="handleStatusSelectVisibleChange($event, row.id)">
                    <el-option v-for="(option, key) in statusOptions" :key="key" :label="option.label" :value="key" />
                  </el-select>
                </el-popover>
              </template>
            </el-table-column>
            <el-table-column label="备注">
              <template #default="{ row }">{{ row.notes || '—' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button type="warning" link size="small" @click="openEditDialog(row)">修改</el-button>
                <el-popconfirm title="确认删除该销售记录？" confirm-button-text="删除" cancel-button-text="取消"
                  @confirm="removeSale(row.id)">
                  <template #reference>
                    <el-button type="danger" link size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-pagination v-if="pagination.total > 0" class="sales__pagination" :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]" :page-size="pagination.pageSize" :current-page="pagination.page"
          layout="total, sizes, prev, pager, next" @current-change="handlePageChange"
          @size-change="handlePageSizeChange" />
      </el-card>
    </el-space>

    <el-dialog v-model="dialogVisible" title="销售数据" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="销售日期" prop="date">
          <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期"
            style="width: 100%" />
        </el-form-item>
        <el-form-item label="客户类型">
          <el-radio-group v-model="isStrangerCustomer">
            <el-radio-button :value="false">已有客户</el-radio-button>
            <el-radio-button :value="true">陌生客户</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="!isStrangerCustomer" label="公司" prop="company_id">
          <el-select v-model="form.company_id" placeholder="选择公司" filterable clearable style="width: 100%">
            <el-option :key="0" :label="'个人客户'" :value="0" />
            <el-option v-for="company in companies" :key="company.id" :label="company.name" :value="company.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!isStrangerCustomer" label="部门" prop="department_id">
          <el-select v-model="form.department_id" placeholder="选择部门" clearable filterable style="width: 100%"
            :disabled="!showDepartmentSelect">
            <el-option v-for="dept in formDepartmentOptions" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!isStrangerCustomer" label="关联客户" prop="customer_id">
          <el-select v-model="form.customer_id" placeholder="选择客户" filterable clearable style="width: 100%"
            :disabled="!form.company_id && form.company_id !== 0">
            <el-option v-for="customer in formCustomerOptions" :key="customer.id" :label="customerLabel(customer)"
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
        <el-form-item label="销售图片">
          <el-upload class="sales__uploader" list-type="picture-card" accept="image/*" :limit="1"
            :file-list="formImageList" :auto-upload="false" :on-change="handleFormImageChange"
            :on-remove="handleFormImageRemove" :on-exceed="handleFormImageExceed"
            :on-preview="handlePictureCardPreview">
            <el-icon>
              <Plus />
            </el-icon>
          </el-upload>
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
    <el-dialog v-model="previewVisible" title="预览" width="560px">
      <img v-if="previewImageUrl" :src="previewImageUrl" style="width: 100%; display: block;" />
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </AppShell>
</template>

<script setup>

import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search, Download } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'
// CSV导出相关
async function downloadCsv() {
  if (!sales.value.length) {
    ElMessage.warning('暂无数据可导出')
    return
  }
  const headers = [
    '日期',
    '项目',
    '公司',
    '部门',
    '客户',
    '类型',
    '数量',
    '单价',
    '金额',
    '图片链接',
    '状态',
    '备注'
  ]
  const rows = sales.value.map(row => ({
    '日期': row.date || '',
    '项目': row.item_name || '',
    '公司': customerCompanyName(row.customer_id),
    '部门': row.customer_department?.name || '—',
    '客户': customerName(row.customer_id),
    '类型': typeName(row.type_id),
    '数量': row.items_count ?? '',
    '单价': row.unit_price !== undefined && row.unit_price !== null ? formatAmount(row.unit_price) : '',
    '金额': row.total_price !== undefined && row.total_price !== null ? formatAmount(row.total_price) : '',
    '图片链接': row.image_url || '',
    '状态': statusLabel(row.status),
    '备注': row.notes || ''
  }))
  // 使用SheetJS生成xlsx
  const ws = XLSX.utils.json_to_sheet(rows, { header: headers })
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, '销售表')
  const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' })
  const url = URL.createObjectURL(new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }))
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `销售表格_${new Date().toISOString().slice(0, 10)}.xlsx`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

import AppShell from '../components/AppShell.vue'
import { useAuthStore, api } from '../stores/auth'

const auth = useAuthStore()

const sales = ref([])
const companies = ref([])
const customers = ref([])
const types = ref([])
const departments = ref([])
const loading = ref(false)
const saving = ref(false)
const statusPopoverVisible = reactive({})
const editingStatus = reactive({})
const isUpdatingStatus = reactive({})

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formRef = ref()
const form = reactive(createDefaultForm())
const formImageList = ref([])
const formImageFile = ref(null)
const previewVisible = ref(false)
const previewImageUrl = ref('')
const isStrangerCustomer = ref(false)
const filters = reactive({
  customerType: 'company',
  keyword: '',
  customerId: null,
  companyId: null,
  departmentId: null,
  typeId: null,
  status: null,
  dateRange: [],
  amountMin: null,
  amountMax: null
})
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const rowImageUploading = reactive({})

const rules = {
  date: [{ required: true, message: '请选择销售日期', trigger: 'change' }],
  company_id: [{
    required: function () { return !isStrangerCustomer.value },
    message: '请选择公司',
    trigger: 'change'
  }],
  // department_id: [{
  // required: function () { return !isStrangerCustomer.value && form.company_id && form.company_id !== 0 },
  // message: '请选择部门',
  // trigger: 'change'
  // }],
  customer_id: [{
    required: function () { return !isStrangerCustomer.value },
    message: '请选择客户',
    trigger: 'change'
  }],
  item_name: [{ required: true, message: '请输入项目内容', trigger: 'blur' }],
  items_count: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  unit_price: [{ required: true, message: '请输入单价', trigger: 'blur' }]
}

const statusOptions = computed(() => ({
  paid: { label: '已支付', type: 'success' },
  draft: { label: '已下单', type: 'warning' },
  sent: { label: '已送货', type: 'info' }
}))

const departmentOptions = computed(() => {
  if (filters.companyId) {
    return departments.value.filter((d) => d.company_id === filters.companyId)
  }
  return {}
})

const formDepartmentOptions = computed(() => {
  if (form.company_id && form.company_id !== 0) {
    return departments.value.filter((d) => d.company_id === form.company_id)
  }
  return []
})

const formCustomerOptions = computed(() => {
  if (form.company_id === 0) {
    // 个人客户：无部门，所有company_id为0的客户
    return customers.value.filter((c) => c.company_id === 0)
  } else if (form.company_id && form.department_id) {
    // 选了公司和部门，筛选该公司该部门下的客户
    return customers.value.filter((c) => c.company_id === form.company_id && c.department_id === form.department_id)
  } else if (form.company_id) {
    // 只选了公司，显示该公司下所有客户
    return customers.value.filter((c) => c.company_id === form.company_id)
  }
  return []
})

const filterCustomerOptions = computed(() => {
  if (filters.customerType === 'personal') {
    return customers.value.filter((c) => c.company_id === 0)
  } else if (filters.customerType === 'company' && filters.companyId && filters.departmentId) {
    return customers.value.filter((c) => c.company_id === filters.companyId && c.department_id === filters.departmentId)
  } else if (filters.customerType === 'company' && filters.companyId) {
    return customers.value.filter((c) => c.company_id === filters.companyId)
  }
  return customers.value
})

const showDepartmentSelect = computed(() => {
  // 个人客户不显示部门
  return form.company_id && form.company_id !== 0 && formDepartmentOptions.value.length > 0
})

function createDefaultForm() {
  return {
    date: new Date().toISOString().slice(0, 10),
    company_id: null,
    department_id: null,
    customer_id: null,
    type_id: null,
    item_name: '',
    items_count: 1,
    unit_price: 0,
    total_price: 0,
    status: 'paid',
    notes: '',
    image_url: null
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

watch(
  () => form.image_url,
  (url) => {
    // When opening dialogs or after reload, reflect existing image
    if (!formImageFile.value) {
      formImageList.value = url ? [{ name: 'sale-image', url }] : []
    }
  },
  { immediate: true }
)

watch(
  () => filters.companyId,
  (companyId) => {
    if (companyId) {
      filters.departmentId = null
      filters.customerId = null
    }
  }
)
watch(
  () => isStrangerCustomer.value,
  (value) => {
    if (value) {
      form.company_id = null
      form.department_id = null
      form.customer_id = null
    }
  }
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

function handleStatusSelectVisibleChange(visible, id) {
  if (visible) {
    // 打开选择器时，设置初始值为当前行的状态
    const row = sales.value.find(item => item.id === id)
    if (row) {
      editingStatus[id] = row.status
    }
  }
  // 选择器关闭时，也关闭弹出框
  if (!visible) {
    setTimeout(() => {
      statusPopoverVisible[id] = false
    }, 100)
  }
}

async function handleStatusChange(id) {
  const newStatus = editingStatus[id]
  if (!newStatus) return

  // 找到对应的销售记录
  const rowIndex = sales.value.findIndex(item => item.id === id)
  if (rowIndex === -1) return

  const row = sales.value[rowIndex]
  // 如果状态没有变化，直接关闭弹出框
  if (row.status === newStatus) {
    statusPopoverVisible[id] = false
    return
  }

  try {
    // 设置加载状态
    isUpdatingStatus[id] = true

    // 调用后端API更新状态
    auth.ensureInterceptors()
    await api.put(`/sales/${id}`, { status: newStatus })

    // 更新本地数据
    row.status = newStatus

    // 显示成功消息
    ElMessage.success('状态更新成功')
  } catch (error) {
    // 显示错误消息
    const message = error?.response?.data?.detail || error?.message || '更新状态失败'
    ElMessage.error(message)

    // 恢复原来的状态
    editingStatus[id] = row.status
  } finally {
    // 重置加载状态
    isUpdatingStatus[id] = false

    // 关闭弹出框
    statusPopoverVisible[id] = false
  }
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
  return customer.name || `客户 #${customer.id}`
}

function customerName(id) {
  const customer = customers.value.find((item) => item.id === id)
  return customer ? customer.name : (id ? `客户 #${id}` : '陌生客户')
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
  isEditing.value = false
  editingId.value = null
  isStrangerCustomer.value = false
  dialogVisible.value = true
}

function openEditDialog(row) {
  // Find customer to get department and company
  const customer = customers.value.find((c) => c.id === row.customer_id)
  const company_id = customer?.company_id ?? null
  Object.assign(form, {
    date: row.date,
    company_id,
    department_id: row.customer_department_id ?? null,
    customer_id: row.customer_id ?? null,
    type_id: row.type_id ?? null,
    item_name: row.item_name || '',
    items_count: Number(row.items_count ?? 1),
    unit_price: Number(row.unit_price ?? 0),
    total_price: Number(row.total_price ?? 0),
    status: row.status || 'draft',
    notes: row.notes || '',
    image_url: row.image_url || null
  })
  isEditing.value = true
  editingId.value = row.id
  isStrangerCustomer.value = row.customer_id === null
  dialogVisible.value = true
}

function validateImageFile(file) {
  const isImage = file?.type?.startsWith('image/')
  if (!isImage) {
    ElMessage.error('仅支持图片文件')
    return false
  }
  return true
}

// 图片压缩大小限制
const MAX_IMAGE_SIZE = 200 * 1024

/**
 * 压缩图片到指定大小以下
 * @param {File} file - 原始图片文件
 * @returns {Promise<File>} - 压缩后的图片文件
 */
async function compressImage(file) {
  // 如果文件已经小于限制大小，直接返回
  if (file.size <= MAX_IMAGE_SIZE) {
    return file
  }

  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = function (event) {
      const img = new Image()
      img.onload = function () {
        // 创建Canvas元素
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')

        // 计算压缩后的尺寸（保持宽高比）
        let width = img.width
        let height = img.height
        const maxDimension = 1500 // 设置最大尺寸，避免图片过大

        if (width > height && width > maxDimension) {
          height = height * (maxDimension / width)
          width = maxDimension
        } else if (height > maxDimension) {
          width = width * (maxDimension / height)
          height = maxDimension
        }

        canvas.width = width
        canvas.height = height

        // 在Canvas上绘制图片
        ctx.drawImage(img, 0, 0, width, height)

        // 初始压缩质量
        let quality = 0.8
        let compressedDataUrl
        let compressedFile

        // 循环压缩直到文件大小小于限制大小
        function compressStep() {
          compressedDataUrl = canvas.toDataURL(file.type, quality)

          // 将DataURL转换为Blob
          const byteString = atob(compressedDataUrl.split(',')[1])
          const mimeString = compressedDataUrl.split(',')[0].split(':')[1].split(';')[0]
          const ab = new ArrayBuffer(byteString.length)
          const ia = new Uint8Array(ab)

          for (let i = 0; i < byteString.length; i++) {
            ia[i] = byteString.charCodeAt(i)
          }

          compressedFile = new File([ab], file.name, { type: mimeString })

          // 如果文件仍然大于限制大小，继续降低质量
          if (compressedFile.size > MAX_IMAGE_SIZE && quality > 0.1) {
            quality -= 0.1
            compressStep()
          } else {
            // 如果质量已经很低但文件仍然很大，进一步缩小尺寸
            if (compressedFile.size > MAX_IMAGE_SIZE && width > 800) {
              width *= 0.8
              height *= 0.8
              canvas.width = width
              canvas.height = height
              ctx.drawImage(img, 0, 0, width, height)
              quality = 0.8
              compressStep()
            } else {
              // 如果文件仍然大于限制大小但已经无法进一步压缩，返回当前文件
              resolve(compressedFile)
            }
          }
        }

        compressStep()
      }
      img.src = event.target.result
    }
    reader.readAsDataURL(file)
  })
}

async function handleFormImageChange(uploadFile) {
  const file = uploadFile?.raw || uploadFile
  if (!validateImageFile(file)) return false

  // 压缩图片
  try {
    const compressedFile = await compressImage(file)
    formImageFile.value = compressedFile
    const name = compressedFile.name || 'sale-image'
    const url = URL.createObjectURL(compressedFile)
    formImageList.value = [{ name, url }]

    // 如果图片被压缩了，显示提示信息
    if (compressedFile.size < file.size) {
      const originalSize = (file.size / 1024).toFixed(2)
      const compressedSize = (compressedFile.size / 1024).toFixed(2)
      ElMessage.success(`图片已压缩：${originalSize}KB → ${compressedSize}KB`)
    }
  } catch (error) {
    console.error('图片压缩失败:', error)
    ElMessage.error('图片处理失败，请重试')
    return false
  }

  return false
}

function handleFormImageRemove() {
  // Element Plus triggers on-remove after click; ask for confirmation first.
  ElMessageBox.confirm('确认删除当前图片？', '提示', { type: 'warning' })
    .then(async () => {
      try {
        // If removing a persisted image on an existing record, also clear it on the server (and Qiniu)
        const removingPersisted = isEditing.value && editingId.value && !!form.image_url && !formImageFile.value
        if (removingPersisted) {
          // Backend will clear DB field and delete the remote image
          await api.put(`/sales/${editingId.value}`, { image_url: null })
          form.image_url = null
        }
        // Clear local selection/list regardless
        formImageFile.value = null
        formImageList.value = []
        ElMessage.success('图片已删除')
      } catch (error) {
        const message = error?.response?.data?.detail || error?.message || '删除失败'
        ElMessage.error(message)
        // Restore previous list on failure
        if (form.image_url) {
          formImageList.value = [{ name: 'sale-image', url: form.image_url }]
        } else if (formImageFile.value) {
          const url = URL.createObjectURL(formImageFile.value)
          formImageList.value = [{ name: formImageFile.value.name || 'sale-image', url }]
        }
      }
    })
    .catch(() => {
      // User canceled: restore current view
      if (form.image_url) {
        formImageList.value = [{ name: 'sale-image', url: form.image_url }]
      } else if (formImageFile.value) {
        const url = URL.createObjectURL(formImageFile.value)
        formImageList.value = [{ name: formImageFile.value.name || 'sale-image', url }]
      } else {
        formImageList.value = []
      }
    })
}

async function handleFormImageExceed(files) {
  const file = Array.isArray(files) ? files[0] : files
  if (!file) return
  if (!validateImageFile(file)) return
  // Replace the previous selection with the new file
  formImageFile.value = null
  formImageList.value = []
  // 直接调用handleFormImageChange来处理文件，这样可以利用压缩功能
  await handleFormImageChange(file)
}

async function handleRowImageUpload({ file, onError, onSuccess }, row) {
  if (!validateImageFile(file)) {
    onError?.(new Error('invalid file'))
    return
  }
  rowImageUploading[row.id] = true
  try {
    // 压缩图片
    const compressedFile = await compressImage(file)

    const formData = new FormData()
    formData.append('image_file', compressedFile)

    // 如果图片被压缩了，显示提示信息
    if (compressedFile.size < file.size) {
      const originalSize = (file.size / 1024).toFixed(2)
      const compressedSize = (compressedFile.size / 1024).toFixed(2)
      ElMessage.success(`图片已压缩：${originalSize}KB → ${compressedSize}KB`)
    }

    auth.ensureInterceptors()
    const { data } = await api.put(`/sales/${row.id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const url = data?.image_url || null
    row.image_url = url
    onSuccess?.({ url })
    ElMessage.success('图片已更新')
  } catch (error) {
    onError?.(error)
    const message = error?.response?.data?.detail || error?.message || '上传失败'
    ElMessage.error(message)
  } finally {
    rowImageUploading[row.id] = false
  }
}

function handleRowImageExceed(files, row) {
  const file = Array.isArray(files) ? files[0] : files
  if (!file) return
  handleRowImageUpload({ file }, row)
}

function handlePictureCardPreview(file) {
  const url = file?.url
  if (!url) return
  previewImageUrl.value = url
  previewVisible.value = true
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

async function loadDepartments() {
  try {
    const { data } = await api.get('/departments/', { params: { limit: 300 } })
    departments.value = data || []
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || error?.message || '加载部门失败')
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

    // 处理客户类型过滤
    if (filters.customerType === 'personal') {
      // 个人客户：获取所有个人客户（company_id=0）和陌生客户（customer_id=null）的销售记录
      // 由于API不支持同时查询两种条件，我们需要获取所有记录然后在前端过滤
      // 这里我们可以不传customer_id，让API返回所有记录，然后在前端过滤
      // 或者我们可以添加一个特殊的参数来标识这是个人客户查询
      // 暂时不传customer_id，让API返回所有记录
    } else if (filters.customerType === 'company') {
      // 公司客户：根据公司和部门过滤
      if (filters.customerId) params.customer_id = filters.customerId
      if (filters.companyId) params.company_id = filters.companyId
    }

    if (filters.typeId) params.type_id = filters.typeId
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
    let items = Array.isArray(data?.items) ? data.items : []

    // 如果是个人客户类型，在前端过滤出个人客户和陌生客户的记录
    if (filters.customerType === 'personal') {
      items = items.filter(item => {
        // 陌生客户：customer_id为null
        if (item.customer_id === null) return true

        // 个人客户：需要检查customer的company_id是否为0
        const customer = customers.value.find(c => c.id === item.customer_id)
        return customer && customer.company_id === 0
      })
    }

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

    // 如果是陌生客户，设置customer_id为null
    if (isStrangerCustomer.value) {
      payload.customer_id = null
      payload.company_id = null
      payload.department_id = null
    } else {
      if (payload.customer_id !== null && payload.customer_id !== undefined) {
        payload.customer_id = Number(payload.customer_id)
      }
    }

    if (!payload.type_id) payload.type_id = null
    else payload.type_id = Number(payload.type_id)
    if (!payload.item_name) payload.item_name = null
    if (!payload.notes) payload.notes = null
    if (isEditing.value && editingId.value) {
      // If an image file is selected, send multipart with data+file; else JSON only
      if (formImageFile.value) {
        const formData = new FormData()
        formData.append('data', JSON.stringify(payload))
        formData.append('image_file', formImageFile.value)
        auth.ensureInterceptors()
        await api.put(`/sales/${editingId.value}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      } else {
        await api.put(`/sales/${editingId.value}`, payload)
      }
      ElMessage.success('修改销售成功')
    } else {
      // Create first, then if image selected, upload via update endpoint
      const { data: created } = await api.post('/sales/', payload)
      const newId = created?.id
      if (newId && formImageFile.value) {
        const formData = new FormData()
        formData.append('image_file', formImageFile.value)
        auth.ensureInterceptors()
        await api.put(`/sales/${newId}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      }
      ElMessage.success('创建销售成功')
    }
    dialogVisible.value = false
    isEditing.value = false
    editingId.value = null
    formImageFile.value = null
    pagination.page = 1
    await loadSales()
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || (isEditing.value ? '修改销售失败' : '创建销售失败')
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

function handleCustomerTypeChange() {
  filters.companyId = null
  filters.departmentId = null
  filters.customerId = null
  handleFilterChange()
}

onMounted(async () => {
  auth.ensureInterceptors()
  await loadLookups()
  await loadDepartments()
  await loadSales()
})
</script>

<style scoped>
.sales {
  width: 100%;

  /* 调整弹出框样式，确保显示在表格单元格上方 */
  :deep(.el-popover) {
    min-width: 140px;
    padding: 8px;
  }

  /* 确保标签可点击区域足够大 */
  :deep(.el-tag) {
    cursor: pointer;
    transition: all 0.3s;
  }

  :deep(.el-tag:hover) {
    opacity: 0.8;
  }

  /* 确保选择器在加载时有明显的指示 */
  :deep(.el-select__wrap) {
    min-height: 32px;
  }
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

.sales__image-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sales__image-thumb,
.sales__image-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  background: #f2f3f5;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #909399;
}

.sales__image-upload {
  margin: 0;
}

.sales__uploader :deep(.el-upload--picture-card) {
  border-radius: 8px;
}
</style>
