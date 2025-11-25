<template>
    <AppShell>
        <div class="statistics-page">
            <el-space direction="vertical" class="financial__header">
                <div>
                    <h2>财务统计分析</h2>
                </div>
                <div>
                    <el-radio-group v-model="analysisType" @change="handleAnalysisTypeChange">
                        <el-radio-button value="yearly">年度分析</el-radio-button>
                        <el-radio-button value="monthly">月度分析</el-radio-button>
                    </el-radio-group>
                </div>
                <div>
                    <el-date-picker v-model="dateRange" :type="analysisType === 'monthly' ? 'daterange' : 'monthrange'"
                        unlink-panels range-separator="至"
                        :start-placeholder="analysisType === 'monthly' ? '开始日期' : '开始月份'"
                        :end-placeholder="analysisType === 'monthly' ? '结束日期' : '结束月份'" @change="fetchStatistics" />
                </div>
            </el-space>

            <!-- 概览卡片 -->
            <div class="overview-cards">
                <el-card class="stat-card">
                    <div class="card-content">
                        <div class="card-icon purchase">
                            <el-icon>
                                <ShoppingCart />
                            </el-icon>
                        </div>
                        <div class="card-info">
                            <div class="card-label">采购总额</div>
                            <div class="card-value">¥{{ formatNumber(overview.purchaseTotal) }}</div>
                        </div>
                    </div>
                </el-card>

                <el-card class="stat-card">
                    <div class="card-content">
                        <div class="card-icon sale">
                            <el-icon>
                                <TrendCharts />
                            </el-icon>
                        </div>
                        <div class="card-info">
                            <div class="card-label">销售总额</div>
                            <div class="card-value">¥{{ formatNumber(overview.saleTotal) }}</div>
                        </div>
                    </div>
                </el-card>

                <el-card class="stat-card">
                    <div class="card-content">
                        <div class="card-icon profit">
                            <el-icon>
                                <Money />
                            </el-icon>
                        </div>
                        <div class="card-info">
                            <div class="card-label">利润</div>
                            <div class="card-value"
                                :class="{ positive: overview.profit >= 0, negative: overview.profit < 0 }">
                                ¥{{ formatNumber(overview.profit) }}
                            </div>
                        </div>
                    </div>
                </el-card>

                <el-card class="stat-card">
                    <div class="card-content">
                        <div class="card-icon rate">
                            <el-icon>
                                <PieChart />
                            </el-icon>
                        </div>
                        <div class="card-info">
                            <div class="card-label">利润率</div>
                            <div class="card-value">{{ formatPercent(overview.profitRate) }}</div>
                        </div>
                    </div>
                </el-card>
            </div>

            <!-- 图表区域 -->
            <div class="charts-container">
                <el-row :gutter="20">
                    <el-col :span="12">
                        <el-card class="chart-card">
                            <template #header>
                                <span>采购销售利润趋势分析</span>
                            </template>
                            <div ref="trendChart" class="chart"></div>
                        </el-card>
                    </el-col>

                    <el-col :span="12">
                        <el-card class="chart-card">
                            <template #header>
                                <span>采购销售对比</span>
                            </template>
                            <div ref="comparisonChart" class="chart"></div>
                        </el-card>
                    </el-col>
                </el-row>



                <!-- 客户销售额分析 -->
                <el-row :gutter="20" style="margin-top: 20px;">
                    <el-col :span="24">
                        <el-card class="chart-card">
                            <template #header>
                                <span>{{ analysisType === 'monthly' ? '月度' : '年度' }}客户销售分析</span>
                            </template>
                            <div class="customer-charts-container">
                                <div ref="customerChart" class="chart half-chart"></div>
                                <div ref="customerPieChart" class="chart half-chart"></div>
                            </div>
                        </el-card>
                    </el-col>
                </el-row>
            </div>

            <!-- 加载状态 -->
            <div v-loading="loading" element-loading-text="加载中..." style="min-height: 200px;"></div>
        </div>
    </AppShell>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { ShoppingCart, TrendCharts, Money, PieChart } from '@element-plus/icons-vue'
import { useAuthStore, api } from '../stores/auth'
import AppShell from '../components/AppShell.vue'

// 响应式数据
const auth = useAuthStore()
const loading = ref(false)
const analysisType = ref('yearly') // yearly: 年度分析, monthly: 月度分析
const dateRange = ref([])
const overview = ref({
    purchaseTotal: 0,
    saleTotal: 0,
    profit: 0,
    profitRate: 0
})

// 图表引用
const trendChart = ref(null)
const comparisonChart = ref(null)
const customerChart = ref(null)
const customerPieChart = ref(null)

// 图表实例
let trendChartInstance = null
let comparisonChartInstance = null
let customerChartInstance = null
let customerPieChartInstance = null

// 格式化数字
const formatNumber = (num) => {
    return new Intl.NumberFormat('zh-CN').format(num || 0)
}

// 格式化百分比
const formatPercent = (num) => {
    return `${(num * 100).toFixed(2)}%`
}

// 渲染客户销售额折线图
const renderCustomerChart = (data) => {
    if (!customerChart.value) return

    if (!customerChartInstance) {
        customerChartInstance = echarts.init(customerChart.value)
    }

    const isMonthly = data.analysisType === 'monthly'
    const title = isMonthly ? '月度客户销售额分析' : '年度客户销售额分析'
    const xAxisLabel = isMonthly ? '月份' : '年份'

    // 构建dataset数据
    const categories = data.categories || []
    const series = data.series || []

    // 准备dataset数据源，第一行为年份/月份，后续行为客户数据
    const datasetSource = [
        ['customer', ...categories]
    ]

    // 添加客户数据行
    series.forEach(s => {
        datasetSource.push([s.name, ...s.data])
    })

    const option = {
        title: {
            text: title,
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            showContent: false // 不显示默认内容，通过事件处理
        },
        legend: {
            data: series.map(s => s.name),
            bottom: 10,
            type: 'scroll',
            orient: 'horizontal'
        },
        dataset: {
            source: datasetSource
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            name: xAxisLabel,
            axisLabel: {
                rotate: isMonthly ? 45 : 0,
                formatter: function (value) {
                    if (isMonthly && value.length === 7) {
                        // 简化月份显示为 MM
                        return value.split('-')[1]
                    }
                    return value
                }
            }
        },
        yAxis: {
            type: 'value',
            name: '销售额(元)'
        },
        series: series.map((s, index) => ({
            name: s.name,
            type: 'line',
            smooth: true,
            seriesLayoutBy: 'row',
            emphasis: {
                focus: 'series'
            }
        }))
    }

    customerChartInstance.setOption(option)

    // 添加updateAxisPointer事件监听，实现鼠标悬停交互
    customerChartInstance.off('updateAxisPointer') // 移除已存在的监听器，避免重复绑定
    customerChartInstance.on('updateAxisPointer', function (event) {
        const xAxisInfo = event.axesInfo[0]
        if (xAxisInfo && customerPieChartInstance) {
            // 获取当前悬停的时间维度索引（加1是因为dataset中第一列是客户名称）
            const dimensionIndex = xAxisInfo.value + 1

            // 更新饼图，显示对应时间维度的数据
            customerPieChartInstance.setOption({
                series: {
                    id: 'customerPie',
                    label: {
                        formatter: '{b}: {@[' + dimensionIndex + ']} ({d}%)'
                    },
                    encode: {
                        value: dimensionIndex,
                        tooltip: dimensionIndex
                    }
                }
            })
        }
    })

    // 添加tooltip事件，显示当前悬停的数据
    customerChartInstance.off('tooltip') // 移除已存在的监听器
    customerChartInstance.on('tooltip', function (params) {
        if (params.type === 'show') {
            // 可以在这里添加自定义的tooltip逻辑
        }
    })
}

// 渲染客户销售占比饼图
const renderCustomerPieChart = (data) => {
    if (!customerPieChart.value) return

    if (!customerPieChartInstance) {
        customerPieChartInstance = echarts.init(customerPieChart.value)
    }

    const isMonthly = data.analysisType === 'monthly'
    const categories = data.categories || []
    const series = data.series || []

    // 构建dataset数据（与折线图相同）
    const datasetSource = [
        ['customer', ...categories]
    ]

    series.forEach(s => {
        datasetSource.push([s.name, ...s.data])
    })

    // 默认显示第一个时间维度的数据
    const defaultDimensionIndex = 1 // 0是客户名称，1是第一个时间维度

    const option = {
        title: {
            text: isMonthly ? '月度客户销售占比' : '年度客户销售占比',
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            showContent: false
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            top: 'middle',
            type: 'scroll'
        },
        dataset: {
            source: datasetSource
        },
        series: [
            {
                id: 'customerPie', // 添加id以便后续通过id更新
                name: '客户销售占比',
                type: 'pie',
                radius: '60%',
                center: ['50%', '50%'],
                emphasis: {
                    focus: 'self',
                    itemStyle: {
                        shadowBlur: 10,
                        shadowOffsetX: 0,
                        shadowColor: 'rgba(0, 0, 0, 0.5)'
                    }
                },
                label: {
                    formatter: `{b}: {@${defaultDimensionIndex}} ({d}%)`
                },
                encode: {
                    itemName: 'customer',
                    value: defaultDimensionIndex,
                    tooltip: defaultDimensionIndex
                }
            }
        ]
    }

    customerPieChartInstance.setOption(option)
}

// 处理分析类型变化
const handleAnalysisTypeChange = () => {
    // 重置日期范围
    const end = new Date()
    const start = new Date()
    if (analysisType.value === 'monthly') {
        // 月度分析：最近30天
        start.setDate(start.getDate() - 30)
    } else {
        // 年度分析：最近6个月
        start.setMonth(start.getMonth() - 6)
    }
    dateRange.value = [start, end]

    // 重新获取数据
    fetchStatistics()
}

// 获取统计数据
const fetchStatistics = async () => {
    loading.value = true
    try {
        const params = {
            analysis_type: analysisType.value
        }
        if (dateRange.value && dateRange.value.length === 2) {
            params.start_date = dateRange.value[0].toISOString().split('T')[0]
            params.end_date = dateRange.value[1].toISOString().split('T')[0]
        }

        auth.ensureInterceptors()
        const response = await api.get('/statistics/', { params })
        overview.value = response.data.overview

        // 渲染图表
        nextTick(() => {
            renderTrendChart(response.data.trend)
            renderComparisonChart(response.data.comparison)
            if (response.data.customerAnalysis) {
                renderCustomerChart(response.data.customerAnalysis)
                renderCustomerPieChart(response.data.customerAnalysis)
            }
        })
    } catch (error) {
        ElMessage.error('获取统计数据失败')
        console.error('Statistics error:', error)
    } finally {
        loading.value = false
    }
}

// 渲染趋势图表（包含利润数据）
const renderTrendChart = (data) => {
    if (!trendChart.value) return

    if (!trendChartInstance) {
        trendChartInstance = echarts.init(trendChart.value)
    }

    const isMonthly = data.analysisType === 'monthly'
    const title = isMonthly ? '每日采购销售利润趋势' : '月度采购销售利润趋势'
    const xAxisLabel = isMonthly ? '日期' : '月份'

    // 计算利润数据
    const profitData = (data.purchaseData || []).map((purchase, index) => {
        return (data.saleData || [])[index] - purchase
    })

    const option = {
        title: {
            text: title,
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            formatter: function (params) {
                let result = `${params[0].axisValue}<br/>`
                params.forEach(param => {
                    result += `${param.marker} ${param.seriesName}: ¥${formatNumber(param.value)}<br/>`
                })
                return result
            }
        },
        legend: {
            data: ['采购金额', '销售金额', '利润'],
            bottom: 10
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.categories || [],
            name: xAxisLabel,
            axisLabel: {
                rotate: isMonthly ? 45 : 0,
                formatter: function (value) {
                    if (isMonthly) {
                        // 简化日期显示
                        return value.split('-').slice(1).join('-')
                    }
                    return value
                }
            }
        },
        yAxis: {
            type: 'value',
            name: '金额(元)'
        },
        series: [
            {
                name: '采购金额',
                type: 'line',
                data: data.purchaseData || [],
                itemStyle: {
                    color: '#fb7960'
                },
                smooth: true
            },
            {
                name: '销售金额',
                type: 'line',
                data: data.saleData || [],
                itemStyle: {
                    color: '#63b931'
                },
                smooth: true
            },
            {
                name: '利润',
                type: 'line',
                data: profitData,
                smooth: true,
                itemStyle: {
                    color: '#bef1ed'
                },
                // 为负利润添加特殊样式
                lineStyle: {
                    width: 3
                },
                markLine: {
                    silent: true,
                    data: [{
                        yAxis: 0,
                        lineStyle: {
                            color: '#333'
                        }
                    }]
                }
            }
        ]
    }

    trendChartInstance.setOption(option)
}

// 渲染对比图表
const renderComparisonChart = (data) => {
    if (!comparisonChart.value) return

    if (!comparisonChartInstance) {
        comparisonChartInstance = echarts.init(comparisonChart.value)
    }

    const isMonthly = data.analysisType === 'monthly'
    const title = isMonthly ? '近期采购销售对比' : '采购销售对比'
    const xAxisLabel = isMonthly ? '日期' : '月份'

    const option = {
        title: {
            text: title,
            left: 'center'
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function (params) {
                let result = `${params[0].axisValue}<br/>`
                params.forEach(param => {
                    result += `${param.marker} ${param.seriesName}: ¥${formatNumber(param.value)}<br/>`
                })
                return result
            }
        },
        legend: {
            data: ['采购', '销售'],
            bottom: 10
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: data.categories || [],
            name: xAxisLabel,
            axisLabel: {
                rotate: isMonthly ? 45 : 0,
                formatter: function (value) {
                    if (isMonthly) {
                        // 简化日期显示
                        return value.split('-').slice(1).join('-')
                    }
                    return value
                }
            }
        },
        yAxis: {
            type: 'value',
            name: '金额(元)'
        },
        series: [
            {
                name: '采购',
                type: 'bar',
                data: data.purchaseData || [],
                itemStyle: {
                    color: '#fb7960'
                }
            },
            {
                name: '销售',
                type: 'bar',
                data: data.saleData || [],
                itemStyle: {
                    color: '#63b931'
                }
            }
        ]
    }

    comparisonChartInstance.setOption(option)
}

// 利润分析已合并到趋势分析图表中

// 占比分析图表已删除

// 监听窗口大小变化，重新渲染图表
const handleResize = () => {
    trendChartInstance?.resize()
    comparisonChartInstance?.resize()
    customerChartInstance?.resize()
    customerPieChartInstance?.resize()
}

// 组件挂载时初始化
onMounted(() => {
    // 设置默认日期范围
    const end = new Date()
    const start = new Date()
    if (analysisType.value === 'monthly') {
        // 月度分析：最近30天
        start.setDate(start.getDate() - 30)
    } else {
        // 年度分析：最近6个月
        start.setMonth(start.getMonth() - 6)
    }
    dateRange.value = [start, end]

    fetchStatistics()

    window.addEventListener('resize', handleResize)
})

// 组件卸载时销毁图表实例
import { onUnmounted } from 'vue'
onUnmounted(() => {
    trendChartInstance?.dispose()
    comparisonChartInstance?.dispose()
    customerChartInstance?.dispose()
    customerPieChartInstance?.dispose()
    // 移除窗口大小变化监听
    window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.statistics-page {
    padding: 0;
}

.customer-charts-container {
    display: flex;
    gap: 20px;
    width: 100%;
    height: 400px;
    /* 设置固定高度 */
}

.half-chart {
    flex: 1;
    min-height: 350px;
    /* 设置最小高度确保图表正常显示 */
}

.financial__header {
    display: flex;
    justify-content: center;
    flex-direction: column;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
}

.statistics-header {
    margin-bottom: 20px;
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-content h1 {
    margin: 0;
    color: #2c3e50;
    font-size: 24px;
    font-weight: 600;
}

.overview-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 20px;
}

.stat-card {
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
}

.card-content {
    display: flex;
    align-items: center;
    padding: 16px;
}

.card-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 16px;
    font-size: 24px;
    color: white;
}

.card-icon.purchase {
    background: linear-gradient(135deg, #ff6b6b, #ee5a52);
}

.card-icon.sale {
    background: linear-gradient(135deg, #4ecdc4, #44a08d);
}

.card-icon.profit {
    background: linear-gradient(135deg, #45b7d1, #96c93d);
}

.card-icon.rate {
    background: linear-gradient(135deg, #a166ab, #5073b8);
}

.card-info {
    flex: 1;
}

.card-label {
    font-size: 14px;
    color: #666;
    margin-bottom: 4px;
}

.card-value {
    font-size: 24px;
    font-weight: 600;
    color: #2c3e50;
}

.card-value.positive {
    color: #27ae60;
}

.card-value.negative {
    color: #e74c3c;
}

.charts-container {
    margin-top: 20px;
}

.chart-card {
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.chart {
    width: 100%;
    height: 400px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
    .overview-cards {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .overview-cards {
        grid-template-columns: 1fr;
    }

    .header-content {
        flex-direction: column;
        gap: 16px;
        align-items: flex-start;
    }

    .chart {
        height: 300px;
    }
}
</style>