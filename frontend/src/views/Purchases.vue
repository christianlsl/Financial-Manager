<template>
  <AppShell>
    <el-space direction="vertical" size="large" class="purchases">
      <div class="purchases__header">
        <div>
          <h2>采购管理</h2>
          <p>跟踪每一笔采购，从下单到收货保持透明。</p>
        </div>
        <el-space>
          <el-button :loading="loading" plain @click="loadPurchases">
            <el-icon>
              <Refresh />
            </el-icon>
            刷新
          </el-button>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon>
              <Plus />
            </el-icon>
            新建采购
          </el-button>
        </el-space>
      </div>

      <el-card shadow="always" class="purchases__filters">
        <el-form :inline="false" :model="filters" label-width="90px" class="purchases__filters-form">
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
          <!-- 第二排：供应商，公司 -->
          <el-row :gutter="16" class="filters-row">
            <el-col :xs="24" :sm="12">
              <el-form-item label="供应商">
                <el-select v-model="filters.supplierId" placeholder="全部供应商" clearable filterable style="width: 100%"
                  @change="handleFilterChange">
                  <el-option v-for="supplier in suppliers" :key="supplier.id" :label="supplierLabel(supplier)"
                    :value="supplier.id" />
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
                  <el-option v-for="(opt, key) in statusOptions" :key="key" :label="opt.label" :value="key" />
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
                <div class="purchases__amount-range">
                  <el-input-number v-model="filters.amountMin" :min="0" :max="999999999" :controls="false"
                    placeholder="最小值" style="width: 120px" @change="handleFilterChange" />
                  <span class="purchases__amount-separator">-</span>
                  <el-input-number v-model="filters.amountMax" :min="0" :max="999999999" :controls="false"
                    placeholder="最大值" style="width: 120px" @change="handleFilterChange" />
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <el-card shadow="always" class="purchases__table" v-loading="loading" style="overflow:auto">
        <template #header>
          <div class="purchases__table-header">采购列表</div>
        </template>
        <el-empty v-if="!purchases.length && !loading" description="暂无采购记录" />
        <div v-else class="purchases__table-grid">
          <el-table :data="purchases" border stripe>
            <el-table-column prop="date" label="日期" width="120" />
            <el-table-column label="项目">
              <template #default="{ row }">{{ row.item_name || '未填写' }}</template>
            </el-table-column>
            <el-table-column label="供应商" width="180">
              <template #default="{ row }">{{ row.supplier_name || '—' }}</template>
            </el-table-column>
            <el-table-column label="类型" width="140">
              <template #default="{ row }">{{ row.type_name || '—' }}</template>
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
                <div class="purchases__image-cell">
                  <el-image v-if="row.image_url" :src="row.image_url" class="purchases__image-thumb" fit="cover"
                    :preview-src-list="[row.image_url]" />
                  <div v-else class="purchases__image-placeholder">无</div>
                  <el-upload class="purchases__image-upload" accept="image/*" :limit="1" :show-file-list="false"
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
                <el-popover v-model:visible="statusPopoverVisible[row.id]" placement="top" trigger="click"
                  popper-class="status-popover">
                  <template #reference>
                    <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
                  </template>
                  <el-select v-model="editingStatus[row.id]" :loading="isUpdatingStatus[row.id]"
                    :disabled="isUpdatingStatus[row.id]" placeholder="选择状态" style="width: 100%"
                    @change="() => handleStatusChange(row.id, editingStatus[row.id])"
                    @visible-change="(visible) => handleStatusSelectVisibleChange(visible, row)">
                    <el-option v-for="(option, key) in statusOptions" :key="key" :label="option.label" :value="key" />
                  </el-select>
                </el-popover>
              </template>
            </el-table-column>
            <el-table-column label="备注">
              <template #default="{ row }">{{ row.notes || '—' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button type="warning" link size="small" @click="openEditDialog(row)">修改</el-button>
                <el-popconfirm title="确认删除该采购记录？" confirm-button-text="删除" cancel-button-text="取消"
                  @confirm="removePurchase(row.id)">
                  <template #reference>
                    <el-button type="danger" link size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-pagination v-if="pagination.total > 0" class="purchases__pagination" :total="pagination.total"
          :page-sizes="[10, 20, 50]" :page-size="pagination.pageSize" :current-page="pagination.page"
          layout="total, sizes, prev, pager, next" @current-change="handlePageChange"
          @size-change="handlePageSizeChange" />
      </el-card>
    </el-space>

    <el-dialog v-model="dialogVisible" title="新建采购" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="采购日期" prop="date">
          <el-date-picker v-model="form.date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期"
            style="width: 100%" />
        </el-form-item>
        <el-form-item label="关联供应商" prop="supplier_id">
          <el-select v-model="form.supplier_id" placeholder="选择供应商" filterable>
            <el-option v-for="supplier in suppliers" :key="supplier.id" :label="supplierLabel(supplier)"
              :value="supplier.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="采购类型" prop="type_id">
          <el-select v-model="form.type_id" placeholder="选择类型" clearable filterable>
            <el-option v-for="type in types" :key="type.id" :label="type.name" :value="type.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="采购项目" prop="item_name">
          <el-input v-model="form.item_name" placeholder="如：办公设备、原材料" />
        </el-form-item>
        <el-form-item label="采购数量" prop="items_count">
          <el-input-number v-model="form.items_count" :min="1" :max="999999" />
        </el-form-item>
        <el-form-item label="采购单价" prop="unit_price">
          <el-input-number v-model="form.unit_price" :min="0" :step="10" :precision="2" />
        </el-form-item>
        <el-form-item label="采购金额" prop="total_price">
          <el-input-number v-model="form.total_price" :min="0" :step="10" :precision="2" disabled />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio-button :value="'pending'">待处理</el-radio-button>
            <el-radio-button :value="'ordered'">已下单</el-radio-button>
            <el-radio-button :value="'received'">已收货</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="采购图片">
          <el-upload class="purchases__uploader" list-type="picture-card" accept="image/*" :limit="1"
            :file-list="formImageList" :auto-upload="false" :on-change="handleFormImageChange"
            :on-remove="handleFormImageRemove" :on-exceed="handleFormImageExceed"
            :on-preview="handlePictureCardPreview">
            <el-icon>
              <Plus />
            </el-icon>
          </el-upload>
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
import { Plus, Refresh, Search } from '@element-plus/icons-vue'

import AppShell from '../components/AppShell.vue'
import { useAuthStore, api } from '../stores/auth'

const auth = useAuthStore()

const purchases = ref([])
const suppliers = ref([])
const types = ref([])
const loading = ref(false)
const saving = ref(false)

const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const formRef = ref()
const form = reactive(createDefaultForm())
const formImageList = ref([])
const formImageFile = ref(null)
const previewVisible = ref(false)
const previewImageUrl = ref('')
const filters = reactive({
  keyword: '',
  supplierId: null,
  typeId: null,
  status: null,
  dateRange: [],
  amountMin: null,
  amountMax: null
})
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const rowImageUploading = reactive({})
// 状态编辑相关变量
const statusPopoverVisible = reactive({})
const editingStatus = reactive({})
const isUpdatingStatus = reactive({})

const rules = {
  date: [{ required: true, message: '请选择采购日期', trigger: 'change' }],
  supplier_id: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  items_count: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  unit_price: [{ required: true, message: '请输入单价', trigger: 'blur' }]
}

const statusOptions = computed(() => ({
  pending: { label: '待处理', type: 'info' },
  ordered: { label: '已下单', type: 'warning' },
  received: { label: '已收货', type: 'success' }
}))

function createDefaultForm() {
  return {
    date: new Date().toISOString().slice(0, 10),
    supplier_id: null,
    type_id: null,
    item_name: '',
    items_count: 1,
    unit_price: 0,
    total_price: 0,
    status: 'pending',
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
    if (!formImageFile.value) {
      formImageList.value = url ? [{ name: 'purchase-image', url }] : []
    }
  },
  { immediate: true }
)

function formatAmount(value) {
  return Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function statusLabel(status) {
  return statusOptions.value[status]?.label || '待处理'
}

function statusType(status) {
  return statusOptions.value[status]?.type || 'info'
}

// 处理状态选择器显示状态变化
function handleStatusSelectVisibleChange(visible, row) {
  if (visible) {
    // 选择器打开时，设置初始值为当前状态
    editingStatus[row.id] = row.status
  }
}

// 处理状态变更
async function handleStatusChange(id, newStatus) {
  const purchase = purchases.value.find(item => item.id === id)
  if (!purchase || purchase.status === newStatus) {
    // 状态未变化，直接关闭弹出框
    statusPopoverVisible[id] = false
    return
  }

  try {
    // 设置加载状态
    isUpdatingStatus[id] = true

    // 调用API更新状态
    auth.ensureInterceptors()
    await api.put(`/purchases/${id}`, { status: newStatus })

    // 更新本地数据
    purchase.status = newStatus

    // 显示成功提示
    ElMessage.success('状态更新成功')
  } catch (error) {
    // 显示错误提示
    const message = error?.response?.data?.detail || error?.message || '状态更新失败'
    ElMessage.error(message)
  } finally {
    // 清除加载状态
    isUpdatingStatus[id] = false
    // 关闭弹出框
    statusPopoverVisible[id] = false
  }
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
const MAX_IMAGE_SIZE = 50 * 1024

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
        // 创建Canvas元素（需要在压缩过程中可重新赋值）
        let canvas = document.createElement('canvas')
        let ctx = canvas.getContext('2d')

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
              canvas = document.createElement('canvas')
              ctx = canvas.getContext('2d')
              canvas.width = width
              canvas.height = height
              ctx.drawImage(img, 0, 0, width, height)
              quality = 0.8 // 重置质量
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

  try {
    // 压缩图片
    const originalSize = file.size
    const compressedFile = await compressImage(file)
    formImageFile.value = compressedFile

    // 显示压缩成功提示（如果进行了压缩）
    if (originalSize !== compressedFile.size) {
      const originalSizeKB = (originalSize / 1024).toFixed(1)
      const compressedSizeKB = (compressedFile.size / 1024).toFixed(1)
      ElMessage.success(`图片已压缩：${originalSizeKB}KB → ${compressedSizeKB}KB`)
    }

    const name = compressedFile.name || 'purchase-image'
    const url = URL.createObjectURL(compressedFile)
    formImageList.value = [{ name, url }]
    return false
  } catch (error) {
    ElMessage.error('图片处理失败：' + (error?.message || '未知错误'))
    return false
  }
}

function handleFormImageRemove() {
  ElMessageBox.confirm('确认删除当前图片？', '提示', { type: 'warning' })
    .then(async () => {
      try {
        const removingPersisted = isEditing.value && editingId.value && !!form.image_url && !formImageFile.value
        if (removingPersisted) {
          await api.put(`/purchases/${editingId.value}`, { image_url: null })
          form.image_url = null
        }
        formImageFile.value = null
        formImageList.value = []
        ElMessage.success('图片已删除')
      } catch (error) {
        const message = error?.response?.data?.detail || error?.message || '删除失败'
        ElMessage.error(message)
        if (form.image_url) {
          formImageList.value = [{ name: 'purchase-image', url: form.image_url }]
        } else if (formImageFile.value) {
          const url = URL.createObjectURL(formImageFile.value)
          formImageList.value = [{ name: formImageFile.value.name || 'purchase-image', url }]
        }
      }
    })
    .catch(() => {
      if (form.image_url) {
        formImageList.value = [{ name: 'purchase-image', url: form.image_url }]
      } else if (formImageFile.value) {
        const url = URL.createObjectURL(formImageFile.value)
        formImageList.value = [{ name: formImageFile.value.name || 'purchase-image', url }]
      } else {
        formImageList.value = []
      }
    })
}

async function handleFormImageExceed(files) {
  const file = Array.isArray(files) ? files[0] : files
  if (!file) return
  // 直接调用已集成压缩功能的handleFormImageChange
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
    const originalSize = file.size
    const compressedFile = await compressImage(file)

    // 显示压缩成功提示（如果进行了压缩）
    if (originalSize !== compressedFile.size) {
      const originalSizeKB = (originalSize / 1024).toFixed(1)
      const compressedSizeKB = (compressedFile.size / 1024).toFixed(1)
      ElMessage.success(`图片已压缩：${originalSizeKB}KB → ${compressedSizeKB}KB`)
    }

    const formData = new FormData()
    formData.append('image_file', compressedFile)
    auth.ensureInterceptors()
    const { data } = await api.put(`/purchases/${row.id}`, formData, {
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

function openCreateDialog() {
  Object.assign(form, createDefaultForm())
  isEditing.value = false
  editingId.value = null
  formImageFile.value = null
  formImageList.value = []
  dialogVisible.value = true
}

function openEditDialog(row) {
  Object.assign(form, {
    date: row.date,
    supplier_id: row.supplier_id ?? null,
    type_id: row.type_id ?? null,
    item_name: row.item_name || '',
    items_count: Number(row.items_count ?? 1),
    unit_price: Number(row.unit_price ?? 0),
    total_price: Number(row.total_price ?? 0),
    status: row.status || 'pending',
    notes: row.notes || '',
    image_url: row.image_url || null,
  })
  isEditing.value = true
  editingId.value = row.id
  formImageFile.value = null
  formImageList.value = row.image_url ? [{ name: 'purchase-image', url: row.image_url }] : []
  dialogVisible.value = true
}

async function loadLookups() {
  try {
    const [{ data: supplierGroups }, { data: typeData }] = await Promise.all([
      api.get('/suppliers/', { params: { limit: 300 } }),
      api.get('/types/', { params: { limit: 200 } })
    ])
    suppliers.value = supplierGroups || []
    types.value = typeData || []
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载基础数据失败'
    ElMessage.error(message)
  }
}

async function loadPurchases() {
  loading.value = true
  try {
    auth.ensureInterceptors()
    const params = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    }
    if (filters.supplierId) params.supplier_id = filters.supplierId
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
    const { data } = await api.get('/purchases/', { params })
    const items = Array.isArray(data?.items) ? data.items : []
    purchases.value = items
    pagination.total = Number(data?.total ?? items.length)
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载采购数据失败'
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
    if (payload.supplier_id !== null && payload.supplier_id !== undefined) {
      payload.supplier_id = Number(payload.supplier_id)
    }
    if (!payload.type_id) payload.type_id = null
    else payload.type_id = Number(payload.type_id)
    if (!payload.item_name) payload.item_name = null
    if (!payload.notes) payload.notes = null
    if (isEditing.value && editingId.value) {
      if (formImageFile.value) {
        const formData = new FormData()
        formData.append('data', JSON.stringify(payload))
        formData.append('image_file', formImageFile.value)
        auth.ensureInterceptors()
        await api.put(`/purchases/${editingId.value}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      } else {
        await api.put(`/purchases/${editingId.value}`, payload)
      }
      ElMessage.success('修改采购成功')
    } else {
      const { data: created } = await api.post('/purchases/', payload)
      const newId = created?.id
      if (newId && formImageFile.value) {
        const formData = new FormData()
        formData.append('image_file', formImageFile.value)
        auth.ensureInterceptors()
        await api.put(`/purchases/${newId}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      }
      ElMessage.success('创建采购成功')
    }
    dialogVisible.value = false
    isEditing.value = false
    editingId.value = null
    formImageFile.value = null
    formImageList.value = []
    pagination.page = 1
    await loadPurchases()
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message =
      error?.response?.data?.detail || error?.message || (isEditing.value ? '修改采购失败' : '创建采购失败')
    ElMessage.error(message)
  } finally {
    saving.value = false
  }
}

async function removePurchase(id) {
  try {
    await api.delete(`/purchases/${id}`)
    ElMessage.success('删除成功')
    pagination.total = Math.max(0, pagination.total - 1)
    purchases.value = purchases.value.filter((item) => item.id !== id)
    if (!purchases.value.length && pagination.page > 1) {
      pagination.page -= 1
      await loadPurchases()
    }
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '删除失败'
    ElMessage.error(message)
  }
}

function handleFilterChange() {
  pagination.page = 1
  loadPurchases()
}

function handlePageChange(page) {
  pagination.page = page
  loadPurchases()
}

function handlePageSizeChange(size) {
  pagination.pageSize = size
  pagination.page = 1
  loadPurchases()
}

onMounted(async () => {
  auth.ensureInterceptors()
  await loadLookups()
  await loadPurchases()
})

function supplierLabel(supplier) {
  if (!supplier) return '—'
  return supplier.name || `供应商 #${supplier.id}`
}

</script>

<style scoped>
.purchases {
  width: 100%;

  /* 调整弹出框样式，确保显示在表格单元格上方 */
  :deep(.status-popover) {
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

.purchases__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.purchases__header h2 {
  margin: 0;
  font-size: 26px;
  color: #1f2d3d;
}

.purchases__header p {
  margin: 6px 0 0;
  color: #66757f;
}

.purchases__filters,
.purchases__table {
  border-radius: 14px;
  border: none;
  background: #ffffff;
  margin: 0 auto;
  box-sizing: border-box;
}

.purchases__filters-form {
  display: block;
}

.filters-row+.filters-row {
  margin-top: 8px;
}

.purchases__filters-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.purchases__amount-range {
  display: flex;
  align-items: center;
  gap: 6px;
}

.purchases__amount-separator {
  color: #909399;
}

.purchases__table-header {
  font-weight: 600;
}

.purchases__pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.purchases__table-grid {
  display: grid;
  grid-template-columns: 1fr;
  width: 100%;
  min-width: 0;
  overflow: auto;
}
</style>
