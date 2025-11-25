<template>
  <AppShell>
    <el-space direction="vertical" size="large" class="dashboard">
      <div class="dashboard__header">
        <div>
          <h2>业务总览</h2>
          <p>快速了解当前采购与销售的运行情况。</p>
        </div>
        <el-button :loading="loading" type="primary" plain @click="loadData">
          <el-icon>
            <Refresh />
          </el-icon>
          刷新数据
        </el-button>
      </div>

      <el-card shadow="hover" class="dashboard__metric">
        <el-row :gutter="18">
          <el-col :xs="24" :md="8">
            <el-statistic title="当月采购总额" :value="statistics.monthly.purchase_total" :precision="2" prefix="¥">
            </el-statistic>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-statistic title="当月销售总额" :value="statistics.monthly.sale_total" :precision="2" prefix="¥">
            </el-statistic>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-statistic title="当月利润" :value="statistics.monthly.profit" :precision="2" prefix="¥"
              :value-style="{ color: statistics.monthly.profit >= 0 ? '#67c23a' : '#f56c6c' }">
            </el-statistic>
          </el-col>
        </el-row>
      </el-card>

      <el-card shadow="hover" class="dashboard__metric">
        <el-row :gutter="18">
          <el-col :xs="24" :md="6">
            <el-statistic title="年度采购总额" :value="statistics.yearly.purchase_total" :precision="2" prefix="¥">
            </el-statistic>
          </el-col>
          <el-col :xs="24" :md="6">
            <el-statistic title="年度销售总额" :value="statistics.yearly.sale_total" :precision="2" prefix="¥">
            </el-statistic>
          </el-col>
          <el-col :xs="24" :md="6">
            <el-statistic title="年度利润" :value="statistics.yearly.profit" :precision="2" prefix="¥"
              :value-style="{ color: statistics.yearly.profit >= 0 ? '#67c23a' : '#f56c6c' }">
            </el-statistic>
          </el-col>
          <el-col :xs="24" :md="6">
            <el-statistic title="利润率" :value="profitRate" suffix="%" :precision="2">
            </el-statistic>
          </el-col>
        </el-row>
      </el-card>

      <el-row :gutter="18">
        <el-col :xs="24" :lg="12">
          <el-card shadow="always" class="dashboard__panel" v-loading="loadingPurchases">
            <template #header>
              <div class="dashboard__panel-header">
                <span>最近采购</span>
                <el-button type="primary" text size="small" @click="go('/purchases')">查看全部</el-button>
              </div>
            </template>
            <el-empty v-if="!recentPurchases.length && !loadingPurchases" description="暂无采购数据" />
            <el-table v-else :data="recentPurchases" size="small" border>
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column label="项目">
                <template #default="{ row }">{{ row.item_name || '未填写' }}</template>
              </el-table-column>
              <el-table-column label="公司" width="140">
                <template #default="{ row }">{{ customerCompanyName(row.customer_id) }}</template>
              </el-table-column>
              <el-table-column prop="total_price" label="金额" width="100">
                <template #default="{ row }">¥ {{ formatAmount(row.total_price) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="purchaseStatusType(row.status)" size="small">{{ purchaseStatusLabel(row.status)
                  }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <el-card shadow="always" class="dashboard__panel" v-loading="loadingSales">
            <template #header>
              <div class="dashboard__panel-header">
                <span>最近销售</span>
                <el-button type="primary" text size="small" @click="go('/sales')">查看全部</el-button>
              </div>
            </template>
            <el-empty v-if="!recentSales.length && !loadingSales" description="暂无销售数据" />
            <el-table v-else :data="recentSales" size="small" border>
              <el-table-column prop="date" label="日期" width="120" />
              <el-table-column label="项目">
                <template #default="{ row }">{{ row.item_name || '未填写' }}</template>
              </el-table-column>
              <el-table-column label="公司" width="140">
                <template #default="{ row }">{{ customerCompanyName(row.customer_id) }}</template>
              </el-table-column>
              <el-table-column prop="total_price" label="金额" width="100">
                <template #default="{ row }">¥ {{ formatAmount(row.total_price) }}</template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="saleStatusType(row.status)" size="small">{{ saleStatusLabel(row.status) }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </el-space>
  </AppShell>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import AppShell from '../components/AppShell.vue'
import { useAuthStore, api } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const purchases = ref([])
const sales = ref([])
const customers = ref([])
const statistics = ref({
  monthly: {
    purchase_total: 0,
    sale_total: 0,
    profit: 0
  },
  yearly: {
    purchase_total: 0,
    sale_total: 0,
    profit: 0
  }
})
const loading = ref(false)
const loadingPurchases = ref(false)
const loadingSales = ref(false)

const profitRate = computed(() => {
  if (statistics.value.yearly.sale_total === 0) return 0
  return parseFloat(((statistics.value.yearly.profit / statistics.value.yearly.sale_total) * 100).toFixed(2))
})

const recentPurchases = computed(() => purchases.value.slice(0, 5))
const recentSales = computed(() => sales.value.slice(0, 5))

function formatAmount(value) {
  return Number(value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function customerCompanyName(customerId) {
  const customer = customers.value.find((c) => c.id === customerId)
  if (!customer) return '—'
  return customer.company_name || '—'
}

function purchaseStatusLabel(status) {
  switch (status) {
    case 'ordered':
      return '已下单'
    case 'received':
      return '已收货'
    default:
      return '待处理'
  }
}

function purchaseStatusType(status) {
  if (status === 'received') return 'success'
  if (status === 'ordered') return 'warning'
  return 'info'
}

function saleStatusLabel(status) {
  switch (status) {
    case 'sent':
      return '已送货'
    case 'paid':
      return '已支付'
    default:
      return '已下单'
  }
}

function saleStatusType(status) {
  if (status === 'paid') return 'success'
  if (status === 'sent') return 'warning'
  return 'info'
}

async function loadData() {
  loading.value = true
  loadingPurchases.value = true
  loadingSales.value = true
  try {
    auth.ensureInterceptors()
    const [
      { data: purchaseData },
      { data: saleData },
      { data: customerGroups },
      { data: statisticsData }
    ] = await Promise.all([
      api.get('/purchases/', { params: { limit: 100, skip: 0 } }),
      api.get('/sales/', { params: { limit: 100, skip: 0 } }),
      api.get('/customers/', { params: { limit: 300 } }),
      api.get('/statistics/summary')
    ])
    const purchaseItems = Array.isArray(purchaseData?.items) ? purchaseData.items : (Array.isArray(purchaseData) ? purchaseData : [])
    const saleItems = Array.isArray(saleData?.items) ? saleData.items : (Array.isArray(saleData) ? saleData : [])
    purchases.value = purchaseItems.sort((a, b) => new Date(b.date) - new Date(a.date))
    sales.value = saleItems.sort((a, b) => new Date(b.date) - new Date(a.date))
    customers.value = (customerGroups || []).flatMap((group) => {
      const groupCompanyId = typeof group.company_id === 'number' ? group.company_id : 0
      return (group.customers || []).map((c) => ({ ...c, company_id: typeof c.company_id === 'number' ? c.company_id : groupCompanyId }))
    })

    // 更新统计数据并确保数值类型正确
    if (statisticsData) {
      // 递归转换对象中的字符串数字为Number类型
      const convertNumbers = (obj) => {
        if (typeof obj === 'object' && obj !== null) {
          Object.keys(obj).forEach(key => {
            if (typeof obj[key] === 'string' && !isNaN(parseFloat(obj[key])) && isFinite(obj[key])) {
              obj[key] = parseFloat(obj[key]);
            } else if (typeof obj[key] === 'object') {
              convertNumbers(obj[key]);
            }
          });
        }
        return obj;
      };
      statistics.value = convertNumbers(statisticsData);
    }
  } catch (error) {
    const message = error?.response?.data?.detail || error?.message || '加载数据失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
    loadingPurchases.value = false
    loadingSales.value = false
  }
}

function go(path) {
  router.push(path)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard {
  width: 100%;
}

.dashboard__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.dashboard__header h2 {
  margin: 0;
  font-size: 26px;
  color: #1f2d3d;
}

.dashboard__header p {
  margin: 6px 0 0;
  color: #66757f;
}

.dashboard__metric {
  border-radius: 14px;
  border: none;
  background: #ffffff;
  width: 600px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dashboard__metric-label {
  margin: 0;
  color: #6b7a88;
  font-size: 14px;
}

.dashboard__metric-value {
  margin: 12px 0 4px;
  font-size: 28px;
  font-weight: 600;
  color: #213547;
}

.dashboard__metric-sub {
  margin: 0;
  color: #8592a3;
  font-size: 13px;
}

.profit-positive {
  color: #67c23a;
}

.profit-negative {
  color: #f56c6c;
}

.dashboard__panel {
  border-radius: 14px;
  border: none;
  background: #ffffff;
  margin-bottom: 16px;
}

.dashboard__panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
</style>
