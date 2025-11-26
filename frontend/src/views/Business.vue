<template>
  <AppShell>
    <el-space direction="vertical" size="large" class="catalogs">
      <div class="catalogs__header">
        <div>
          <h2>业务资料管理</h2>
          <p>维护客户、供应商与物料，便于在采购与销售中快速引用。</p>
        </div>
        <el-button :loading="loading" type="primary" plain @click="loadAll">同步数据</el-button>
      </div>

      <el-card shadow="always" class="catalogs__card">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="客户" name="customers">
            <div class="catalogs__toolbar catalogs__toolbar--between">
              <div class="catalogs__filters">
                <el-input v-model="customerSearchKeyword" placeholder="搜索客户名称、电话、邮箱或职位"
                  style="width: 300px; margin-right: 16px" clearable>
                  <template #prefix>
                    <el-icon>
                      <Search />
                    </el-icon>
                  </template>
                </el-input>
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
            <div class="catalogs__table-grid">
              <el-table :data="filteredCustomers" border stripe v-loading="loadingCustomers"
                @current-change="handleCustomerSelect">
                <el-table-column prop="name" label="客户名称" min-width="200" />
                <el-table-column label="所属公司" min-width="180">
                  <template #default="{ row }">{{ getCompanyName(row.company_id) }}</template>
                </el-table-column>
                <el-table-column label="所属部门" min-width="160">
                  <template #default="{ row }">{{ getDepartmentName(row.department_id) }}</template>
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
            </div>
            <el-empty v-if="!customers.length && !loadingCustomers" description="暂无客户数据" />
            <el-pagination v-if="pagination.customers.total > 0" class="catalogs__pagination"
              :total="pagination.customers.total" :page-sizes="[10, 20, 50]" :page-size="pagination.customers.pageSize"
              :current-page="pagination.customers.page" layout="total, sizes, prev, pager, next"
              @current-change="handleCustomerPageChange" @size-change="handleCustomerPageSizeChange" />
          </el-tab-pane>

          <el-tab-pane label="公司" name="companies">
            <div class="catalogs__toolbar catalogs__toolbar--between">
              <div class="catalogs__filters">
                <el-input v-model="companySearchKeyword" placeholder="搜索公司名称、地址或联系人"
                  style="width: 300px; margin-right: 16px" clearable>
                  <template #prefix>
                    <el-icon>
                      <Search />
                    </el-icon>
                  </template>
                </el-input>
              </div>

              <el-button type="primary" @click="openCompanyDialog()">
                <el-icon>
                  <OfficeBuilding />
                </el-icon>
                新建公司
              </el-button>
              <el-button type="primary" :disabled="!selectedCompany"
                @click="openDepartmentDialog(null, selectedCompany?.id)">
                <el-icon>
                  <OfficeBuilding />
                </el-icon>
                新建部门
              </el-button>
            </div>
            <div class="catalogs__table-grid">
              <el-table :data="filteredCompanies" border stripe v-loading="loadingCompanies"
                @current-change="handleCompanySelect">
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
                <el-table-column label="操作" width="240" fixed="right">
                  <template #default="{ row }">
                    <el-space>
                      <el-button type="primary" link size="small" @click="openCompanyDialog(row)">编辑</el-button>
                      <el-button type="primary" link size="small"
                        @click="selectCompanyAndManageDepartments(row)">管理部门</el-button>
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
            </div>
            <el-empty v-if="!companies.length && !loadingCompanies" description="暂无公司数据" />
            <el-pagination v-if="pagination.companies.total > 0" class="catalogs__pagination"
              :total="pagination.companies.total" :page-sizes="[10, 20, 50]" :page-size="pagination.companies.pageSize"
              :current-page="pagination.companies.page" layout="total, sizes, prev, pager, next"
              @current-change="handleCompanyPageChange" @size-change="handleCompanyPageSizeChange" />

            <!-- 部门列表展示区域 -->
            <div v-if="selectedCompany" class="catalogs__card" style="margin-top: 16px;">
              <div class="catalogs__header">
                <h3>{{ selectedCompany.name }} - 部门列表</h3>
                <el-button type="primary" size="small" @click="openDepartmentDialog(null, selectedCompany.id)">
                  <el-icon>
                    <OfficeBuilding />
                  </el-icon>
                  新增部门
                </el-button>
              </div>
              <div class="catalogs__table-grid">
                <el-table :data="filteredDepartments" border stripe v-loading="loadingDepartments">
                  <el-table-column prop="name" label="部门名称" min-width="200" />
                  <el-table-column label="操作" width="160" fixed="right">
                    <template #default="{ row }">
                      <el-space>
                        <el-button type="primary" link size="small" @click="openDepartmentDialog(row)">编辑</el-button>
                        <el-popconfirm title="确认删除该部门？" confirm-button-text="删除" cancel-button-text="取消"
                          @confirm="removeDepartment(row.id)">
                          <template #reference>
                            <el-button type="danger" link size="small">删除</el-button>
                          </template>
                        </el-popconfirm>
                      </el-space>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <el-empty v-if="!filteredDepartments.length && !loadingDepartments" description="暂无部门数据" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 供应商和物料类型分离出来 -->
      <el-card shadow="always" class="catalogs__card" style="margin-top: 24px;">
        <el-tabs v-model="suppliersTab">
          <el-tab-pane label="供应商" name="suppliers">
            <div class="catalogs__toolbar catalogs__toolbar--between">
              <div class="catalogs__filters">
                <el-input v-model="supplierSearchKeyword" placeholder="搜索供应商名称、地址或联系人"
                  style="width: 300px; margin-right: 16px" clearable>
                  <template #prefix>
                    <el-icon>
                      <Search />
                    </el-icon>
                  </template>
                </el-input>
                <el-select v-model="supplierFilterCompanyId" placeholder="筛选公司" style="min-width: 200px">
                  <el-option :value="ALL_COMPANY_VALUE" label="全部供应商" />
                  <el-option v-for="item in companies" :key="item.id" :value="item.id" :label="item.name" />
                </el-select>
              </div>
              <el-button type="primary" @click="openSupplierDialog()">
                <el-icon>
                  <User />
                </el-icon>
                新建供应商
              </el-button>
            </div>
            <div class="catalogs__table-grid">
              <el-table :data="filteredSuppliers" border stripe v-loading="loadingSuppliers"
                @current-change="handleSupplierSelect">
                <el-table-column prop="name" label="供应商名称" min-width="200" />
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
                      <el-button type="primary" link size="small" @click="openSupplierDialog(row)">编辑</el-button>
                      <el-popconfirm title="确认删除该供应商？" confirm-button-text="删除" cancel-button-text="取消"
                        @confirm="removeSupplier(row.id)">
                        <template #reference>
                          <el-button type="danger" link size="small">删除</el-button>
                        </template>
                      </el-popconfirm>
                    </el-space>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <el-empty v-if="!suppliers.length && !loadingSuppliers" description="暂无供应商数据" />
            <el-pagination v-if="pagination.suppliers.total > 0" class="catalogs__pagination"
              :total="pagination.suppliers.total" :page-sizes="[10, 20, 50]" :page-size="pagination.suppliers.pageSize"
              :current-page="pagination.suppliers.page" layout="total, sizes, prev, pager, next"
              @current-change="handleSupplierPageChange" @size-change="handleSupplierPageSizeChange" />
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
            <div class="catalogs__table-grid">
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
            </div>
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
        <el-form-item label="所属部门" prop="department_id">
          <el-select v-model="customerDialog.form.department_id" placeholder="请选择部门"
            :disabled="customerDialog.form.company_id === PERSONAL_COMPANY_VALUE" clearable filterable>
            <el-option v-for="dept in customerDepartmentOptions" :key="dept.id" :value="dept.id" :label="dept.name" />
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

    <el-dialog v-model="supplierDialog.visible" :title="supplierDialog.isEdit ? '编辑供应商' : '新建供应商'" width="520px"
      destroy-on-close>
      <el-form ref="supplierFormRef" :model="supplierDialog.form" :rules="supplierRules" label-width="96px">
        <el-form-item label="供应商名称" prop="name">
          <el-input v-model="supplierDialog.form.name" placeholder="请输入供应商名称" />
        </el-form-item>
        <el-form-item label="职位">
          <el-input v-model="supplierDialog.form.position" placeholder="请输入职位" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="supplierDialog.form.phone_number" placeholder="请输入电话号码" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="supplierDialog.form.email" placeholder="name@example.com" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-space>
          <el-button @click="supplierDialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="supplierDialog.loading" @click="submitSupplier">保存</el-button>
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

    <el-dialog v-model="departmentDialog.visible" :title="departmentDialog.isEdit ? '编辑部门' : '新建部门'" width="540px"
      destroy-on-close>
      <el-form ref="departmentFormRef" :model="departmentDialog.form" :rules="departmentRules" label-width="96px">
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="departmentDialog.form.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="所属公司" prop="company_id">
          <el-select v-model="departmentDialog.form.company_id" placeholder="请选择公司">
            <el-option v-for="item in companies" :key="item.id" :value="item.id" :label="item.name" />
          </el-select>
        </el-form-item>

      </el-form>
      <template #footer>
        <el-space>
          <el-button @click="departmentDialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="departmentDialog.loading" @click="submitDepartment">保存</el-button>
        </el-space>
      </template>
    </el-dialog>
  </AppShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { OfficeBuilding, Ticket, User, Search } from '@element-plus/icons-vue'

import AppShell from '../components/AppShell.vue'
import { useAuthStore, api } from '../stores/auth'

const auth = useAuthStore()

const activeTab = ref('customers')
const suppliersTab = ref('suppliers')
const companies = ref([])
const types = ref([])
const loading = ref(false)
const loadingCompanies = ref(false)
const loadingCustomers = ref(false)
const loadingTypes = ref(false)
const loadingSuppliers = ref(false)
const loadingDepartments = ref(false)
const customers = ref([])
const suppliers = ref([])
const departments = ref([])
const selectedCompany = ref(null)

const ALL_COMPANY_VALUE = 'all'
const PERSONAL_COMPANY_VALUE = 0
const customerFilterCompanyId = ref(ALL_COMPANY_VALUE)
const supplierFilterCompanyId = ref(ALL_COMPANY_VALUE)
const customerSearchKeyword = ref('')
const companySearchKeyword = ref('')
const supplierSearchKeyword = ref('')

// 分页相关状态
const pagination = reactive({
  companies: {
    page: 1,
    pageSize: 10,
    total: 0
  },
  customers: {
    page: 1,
    pageSize: 10,
    total: 0
  },
  suppliers: {
    page: 1,
    pageSize: 10,
    total: 0
  }
})

const filteredCustomers = computed(() => {
  let result = customers.value

  // 应用公司筛选
  const companyFilter = customerFilterCompanyId.value
  if (companyFilter === ALL_COMPANY_VALUE) {
    result = customers.value
  } else if (companyFilter === PERSONAL_COMPANY_VALUE) {
    result = customers.value.filter((item) => item.company_id === 0)
  } else {
    result = customers.value.filter((item) => item.company_id === companyFilter)
  }

  // 应用搜索关键词
  const keyword = customerSearchKeyword.value.toLowerCase().trim()
  if (keyword) {
    result = result.filter((item) => {
      return (
        (item.name && item.name.toLowerCase().includes(keyword)) ||
        (item.phone_number && item.phone_number.toLowerCase().includes(keyword)) ||
        (item.email && item.email.toLowerCase().includes(keyword)) ||
        (item.position && item.position.toLowerCase().includes(keyword))
      )
    })
  }

  return result
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

const supplierDialog = reactive({
  visible: false,
  isEdit: false,
  loading: false,
  form: createSupplierForm()
})

const departmentDialog = reactive({
  visible: false,
  isEdit: false,
  loading: false,
  form: createDepartmentForm()
})

const companyFormRef = ref()
const customerFormRef = ref()
const typeFormRef = ref()
const supplierFormRef = ref()
const departmentFormRef = ref()

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

const supplierRules = {
  name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
  company_id: [{ required: true, message: '请选择所属公司', trigger: 'change' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] }]
}

const departmentRules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
  company_id: [{ required: true, message: '请选择所属公司', trigger: 'change' }]
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
    company_id: PERSONAL_COMPANY_VALUE,
    department_id: null
  }
}

function createTypeForm() {
  return {
    id: null,
    name: ''
  }
}

function createSupplierForm() {
  return {
    id: null,
    name: '',
    phone_number: '',
    email: '',
    position: '',
    company_id: PERSONAL_COMPANY_VALUE
  }
}

function createDepartmentForm() {
  return {
    id: null,
    name: '',
    company_id: null
  }
}

const customerDepartmentOptions = computed(() => {
  const companyId = customerDialog.form.company_id
  if (!companyId || companyId === PERSONAL_COMPANY_VALUE) return []
  return departments.value.filter((item) => item.company_id === companyId)
})

const filteredDepartments = computed(() => {
  if (!selectedCompany.value) return []
  return departments.value.filter((item) => item.company_id === selectedCompany.value.id)
})

const filteredCompanies = computed(() => {
  let result = companies.value

  // 应用搜索关键词
  const keyword = companySearchKeyword.value.toLowerCase().trim()
  if (keyword) {
    result = result.filter((item) => {
      return (
        (item.name && item.name.toLowerCase().includes(keyword)) ||
        (item.address && item.address.toLowerCase().includes(keyword)) ||
        (item.legal_person && item.legal_person.toLowerCase().includes(keyword)) ||
        (item.phone && item.phone.toLowerCase().includes(keyword))
      )
    })
  }

  return result
})

const filteredSuppliers = computed(() => {
  let result = suppliers.value

  // 应用公司筛选
  const companyFilter = supplierFilterCompanyId.value
  if (companyFilter === ALL_COMPANY_VALUE) {
    result = suppliers.value
  } else {
    result = suppliers.value.filter((item) => item.company_id === companyFilter)
  }

  // 应用搜索关键词
  const keyword = supplierSearchKeyword.value.toLowerCase().trim()
  if (keyword) {
    result = result.filter((item) => {
      return (
        (item.name && item.name.toLowerCase().includes(keyword)) ||
        (item.position && item.position.toLowerCase().includes(keyword)) ||
        (item.phone_number && item.phone_number.toLowerCase().includes(keyword)) ||
        (item.email && item.email.toLowerCase().includes(keyword))
      )
    })
  }

  return result
})

function getCompanyName(companyId) {
  if (companyId === 0) return '个人客户'
  if (companyId === null || companyId === undefined) return '—'
  const company = companies.value.find((item) => item.id === companyId)
  return company?.name || `公司 #${companyId}`
}

function getDepartmentName(departmentId) {
  if (!departmentId) return '—'
  const dept = departments.value.find((item) => item.id === departmentId)
  return dept?.name || `部门 #${departmentId}`
}

function handleCompanySelect(company) {
  selectedCompany.value = company
}

function handleCustomerSelect(customer) {
  // 客户选中处理
  console.log('选中客户:', customer)
}

// 客户分页处理函数
function handleCustomerPageChange(page) {
  pagination.customers.page = page
  loadCustomers()
}

function handleCustomerPageSizeChange(pageSize) {
  pagination.customers.pageSize = pageSize
  pagination.customers.page = 1
  loadCustomers()
}

// 客户筛选变更时重置分页
watch([customerFilterCompanyId, customerSearchKeyword], () => {
  pagination.customers.page = 1
  loadCustomers()
}, { deep: true })

// 供应商选择处理
function handleSupplierSelect(supplier) {
  console.log('选中供应商:', supplier)
}

// 供应商分页处理函数
function handleSupplierPageChange(page) {
  pagination.suppliers.page = page
  loadSuppliers()
}

function handleSupplierPageSizeChange(pageSize) {
  pagination.suppliers.pageSize = pageSize
  pagination.suppliers.page = 1
  loadSuppliers()
}

// 供应商筛选变更时重置分页
watch([supplierFilterCompanyId, supplierSearchKeyword], () => {
  pagination.suppliers.page = 1
  loadSuppliers()
}, { deep: true })

// 分页处理函数
function handleCompanyPageChange(page) {
  pagination.companies.page = page
  loadCompanies()
}

function handleCompanyPageSizeChange(pageSize) {
  pagination.companies.pageSize = pageSize
  pagination.companies.page = 1
  loadCompanies()
}

// 搜索和筛选变更时重置分页
watch(companySearchKeyword, () => {
  pagination.companies.page = 1
  loadCompanies()
})

function selectCompanyAndManageDepartments(company) {
  selectedCompany.value = company
  // 延迟滚动到部门列表区域，确保DOM已更新
  setTimeout(() => {
    const departmentsElement = document.querySelector('.catalogs__card .catalogs__header h3')
    if (departmentsElement) {
      departmentsElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, 100)
}



watch(
  () => departmentDialog.form.company_id,
  () => { }
)

watch(
  () => customerDialog.form.company_id,
  (companyId) => {
    if (!companyId || companyId === PERSONAL_COMPANY_VALUE) {
      customerDialog.form.department_id = null
      return
    }
    const dept = departments.value.find((item) => item.id === customerDialog.form.department_id)
    if (dept && dept.company_id !== companyId) {
      customerDialog.form.department_id = null
    }
  }
)

async function loadCompanies() {
  loadingCompanies.value = true
  try {
    const params = {
      skip: (pagination.companies.page - 1) * pagination.companies.pageSize,
      limit: pagination.companies.pageSize,
      q: companySearchKeyword.value.trim()
    }
    const { data } = await api.get('/companies/', { params })

    // 由于后端返回的是直接的数据数组，需要通过其他方式获取总数
    // 这里暂时使用获取所有数据的方式来计算总数
    const allCompanies = await api.get('/companies/', { params: { limit: 1000 } })
    pagination.companies.total = Array.isArray(allCompanies.data) ? allCompanies.data.length : 0

    companies.value = Array.isArray(data) ? data : []

    if (typeof customerFilterCompanyId.value === 'number' && customerFilterCompanyId.value > 0) {
      const exists = companies.value.some((item) => item.id === customerFilterCompanyId.value)
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
    const params = {
      skip: (pagination.customers.page - 1) * pagination.customers.pageSize,
      limit: pagination.customers.pageSize,
      q: customerSearchKeyword.value.trim()
    }

    // 添加公司筛选条件
    if (customerFilterCompanyId.value !== ALL_COMPANY_VALUE) {
      params.company_id = customerFilterCompanyId.value
    }

    const { data } = await api.get('/customers/', { params })

    // 获取总数（带筛选条件）
    const countParams = { limit: 1000 }
    if (customerFilterCompanyId.value !== ALL_COMPANY_VALUE) {
      countParams.company_id = customerFilterCompanyId.value
    }
    if (customerSearchKeyword.value.trim()) {
      countParams.q = customerSearchKeyword.value.trim()
    }

    const allCustomersData = await api.get('/customers/', { params: countParams })

    // 处理数据格式化，保持与原代码相同的格式转换逻辑
    const formattedData = (data || []).flatMap((group) => {
      const resolvedGroupCompanyId = typeof group.company_id === 'number' ? group.company_id : PERSONAL_COMPANY_VALUE
      return (group.customers || []).map((customer) => {
        const customerCompanyId = typeof customer.company_id === 'number' ? customer.company_id : resolvedGroupCompanyId
        return {
          ...customer,
          company_id: customerCompanyId
        }
      })
    })

    // 处理总数数据格式
    const allCustomers = (allCustomersData.data || []).flatMap((group) => {
      return (group.customers || [])
    })

    pagination.customers.total = Array.isArray(allCustomers) ? allCustomers.length : 0
    customers.value = formattedData.sort((a, b) => {
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

async function loadSuppliers() {
  loadingSuppliers.value = true
  try {
    const params = {
      skip: (pagination.suppliers.page - 1) * pagination.suppliers.pageSize,
      limit: pagination.suppliers.pageSize,
      q: supplierSearchKeyword.value.trim()
    }

    // 添加公司筛选条件
    if (supplierFilterCompanyId.value !== ALL_COMPANY_VALUE) {
      params.company_id = supplierFilterCompanyId.value
    }

    const { data } = await api.get('/suppliers/', { params })

    // 获取总数（带筛选条件）
    const countParams = { limit: 1000 }
    if (supplierFilterCompanyId.value !== ALL_COMPANY_VALUE) {
      countParams.company_id = supplierFilterCompanyId.value
    }
    if (supplierSearchKeyword.value.trim()) {
      countParams.q = supplierSearchKeyword.value.trim()
    }

    const allSuppliers = await api.get('/suppliers/', { params: countParams })
    pagination.suppliers.total = Array.isArray(allSuppliers.data) ? allSuppliers.data.length : 0

    suppliers.value = Array.isArray(data) ? data : []
    suppliers.value.sort((a, b) => (a.name || '').localeCompare(b.name || '', 'zh-CN'))
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载供应商列表失败'
    ElMessage.error(message)
  } finally {
    loadingSuppliers.value = false
  }
}

async function loadDepartments() {
  loadingDepartments.value = true
  try {
    const { data } = await api.get('/departments/', { params: { limit: 300 } })
    const entries = Array.isArray(data) ? data : []
    departments.value = entries
      .map((dept) => ({
        ...dept,
        partner_company_ids: Array.isArray(dept.partner_company_ids) ? dept.partner_company_ids : []
      }))
      .sort((a, b) => {
        const companyA = a.company_id ?? -1
        const companyB = b.company_id ?? -1
        if (companyA !== companyB) return companyA - companyB
        return (a.name || '').localeCompare(b.name || '', 'zh-CN')
      })
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载部门列表失败'
    ElMessage.error(message)
  } finally {
    loadingDepartments.value = false
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
    await Promise.all([loadCompanies(), loadCustomers(), loadSuppliers(), loadDepartments(), loadTypes()])
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
    customerDialog.form.department_id = customer.department_id ?? null
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

function openSupplierDialog(supplier) {
  supplierDialog.visible = true
  supplierDialog.isEdit = Boolean(supplier)
  Object.assign(supplierDialog.form, createSupplierForm())
  if (supplier) {
    supplierDialog.form.id = supplier.id
    supplierDialog.form.name = supplier.name || ''
    supplierDialog.form.phone_number = supplier.phone_number || ''
    supplierDialog.form.email = supplier.email || ''
    supplierDialog.form.position = supplier.position || ''
    supplierDialog.form.company_id = typeof supplier.company_id === 'number' ? supplier.company_id : PERSONAL_COMPANY_VALUE
  }
}

function openDepartmentDialog(department, companyId) {
  departmentDialog.visible = true
  departmentDialog.isEdit = Boolean(department)
  Object.assign(departmentDialog.form, createDepartmentForm())
  if (department) {
    departmentDialog.form.id = department.id
    departmentDialog.form.name = department.name || ''
    departmentDialog.form.company_id = department.company_id ?? null
  } else if (companyId) {
    departmentDialog.form.company_id = companyId
  }
}

function handleDepartmentEdit(department) {
  openDepartmentDialog(department)
}

function handleDepartmentDelete(department) {
  removeDepartment(department)
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
    payload.department_id = payload.department_id ? Number(payload.department_id) : null
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

async function submitSupplier() {
  if (!supplierFormRef.value) return
  try {
    await supplierFormRef.value.validate()
    supplierDialog.loading = true
    const payload = { ...supplierDialog.form }
    const supplierId = payload.id
    delete payload.id
    payload.name = payload.name?.trim() || ''
    if (!payload.name) {
      ElMessage.error('请输入供应商名称')
      return
    }
    const numericCompanyId = Number(payload.company_id)
    if (!Number.isFinite(numericCompanyId) || numericCompanyId < 0) {
      ElMessage.error('请选择所属公司')
      return
    }
    payload.company_id = numericCompanyId
    payload.phone_number = payload.phone_number?.trim() || null
    payload.email = payload.email?.trim() || null
    payload.position = payload.position?.trim() || null
    if (supplierDialog.isEdit && supplierId) {
      await api.put(`/suppliers/${supplierId}`, payload)
      ElMessage.success('更新供应商成功')
    } else {
      await api.post('/suppliers/', payload)
      ElMessage.success('创建供应商成功')
    }
    supplierDialog.visible = false
    await loadSuppliers()
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || '保存供应商失败'
    ElMessage.error(message)
  } finally {
    supplierDialog.loading = false
  }
}

async function removeSupplier(id) {
  try {
    await api.delete(`/suppliers/${id}`)
    ElMessage.success('删除供应商成功')
    await loadSuppliers()
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '删除供应商失败'
    ElMessage.error(message)
  }
}

async function submitDepartment() {
  if (!departmentFormRef.value) return
  try {
    await departmentFormRef.value.validate()
    departmentDialog.loading = true
    const payload = { ...departmentDialog.form }
    const departmentId = payload.id
    delete payload.id
    payload.name = payload.name?.trim() || ''
    if (!payload.name) {
      ElMessage.error('请输入部门名称')
      return
    }
    const numericCompanyId = Number(payload.company_id)
    if (!Number.isFinite(numericCompanyId) || numericCompanyId <= 0) {
      ElMessage.error('请选择所属公司')
      return
    }
    payload.company_id = numericCompanyId

    if (departmentDialog.isEdit && departmentId) {
      await api.put(`/departments/${departmentId}`, payload)
      ElMessage.success('更新部门成功')
    } else {
      await api.post('/departments/', payload)
      ElMessage.success('创建部门成功')
    }
    departmentDialog.visible = false
    // 重新加载部门列表，确保在公司tab中也能看到最新数据
    await loadDepartments()
  } catch (error) {
    if (error?.name === 'ElFormError') return
    const message = error?.response?.data?.detail || error?.message || '保存部门失败'
    ElMessage.error(message)
  } finally {
    departmentDialog.loading = false
  }
}

async function removeDepartment(id) {
  try {
    await api.delete(`/departments/${id}`)
    ElMessage.success('删除部门成功')
    // 重新加载部门列表，确保在公司tab中也能看到最新数据
    await loadDepartments()
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '删除部门失败'
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

.catalogs__table-grid {
  display: grid;
}
</style>
