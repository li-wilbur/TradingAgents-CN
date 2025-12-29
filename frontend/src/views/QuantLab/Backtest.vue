<template>
  <div class="quant-backtest">
    <el-row :gutter="20">
      <!-- Config Panel -->
      <el-col :span="6">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>回测配置</span>
              <el-button link icon="Refresh" @click="fetchStrategies"></el-button>
            </div>
          </template>
          
          <el-form label-position="top" size="default">
            <el-form-item label="策略选择">
              <el-select v-model="selectedStrategyId" placeholder="请选择策略" @change="onStrategyChange">
                <el-option
                  v-for="strat in strategies"
                  :key="strat.id"
                  :label="strat.name"
                  :value="strat.id"
                />
              </el-select>
              <div v-if="currentStrategy" class="strat-desc">{{ currentStrategy.description }}</div>
            </el-form-item>

            <template v-if="currentStrategy">
              <el-divider content-position="left">策略参数</el-divider>
              <div v-for="param in currentStrategy.params" :key="param.name" class="param-item">
                <el-form-item :label="param.name">
                  <el-input-number v-if="param.type === 'int'" v-model="formParams[param.name]" style="width: 100%" />
                  <el-input-number v-else-if="param.type === 'float'" v-model="formParams[param.name]" :precision="2" :step="0.1" style="width: 100%" />
                  <el-switch v-else-if="param.type === 'bool'" v-model="formParams[param.name]" />
                  <el-input v-else v-model="formParams[param.name]" />
                </el-form-item>
              </div>
            </template>

            <el-divider content-position="left">环境设置</el-divider>
            
            <el-form-item label="标的代码">
              <el-input v-model="config.symbol" placeholder="e.g. 000001.SZ">
                <template #append>
                   <el-button @click="openStockSelector">选择</el-button>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="初始资金">
              <el-input-number v-model="config.initial_cash" :step="10000" style="width: 100%" />
            </el-form-item>

            <el-button type="primary" class="run-btn" :loading="loading" @click="runBacktest" size="large">
              运行回测
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <!-- Results Panel -->
      <el-col :span="18">
        <el-card class="result-card" v-if="result" v-loading="loading">
           <template #header>
             <div class="card-header">
               <span>回测报告</span>
               <el-tag :type="result.metrics.return_pct >= 0 ? 'success' : 'danger'">
                  {{ fmtPct(result.metrics.return_pct) }}
               </el-tag>
             </div>
           </template>
           
           <!-- Metrics -->
           <el-descriptions :column="4" border class="metrics-desc">
             <el-descriptions-item label="总收益率">
               <span :class="getColor(result.metrics.return_pct)">{{ fmtPct(result.metrics.return_pct) }}</span>
             </el-descriptions-item>
             <el-descriptions-item label="夏普比率">{{ fmtNum(result.metrics.sharpe_ratio) }}</el-descriptions-item>
             <el-descriptions-item label="最大回撤">
               <span class="text-danger">{{ fmtNum(result.metrics.max_drawdown) }}%</span>
             </el-descriptions-item>
             <el-descriptions-item label="总交易数">{{ result.metrics.total_trades }}</el-descriptions-item>
             
             <el-descriptions-item label="胜率">{{ fmtPct(result.metrics.win_rate * 100) }}</el-descriptions-item>
             <el-descriptions-item label="盈亏比">{{ fmtNum(result.metrics.profit_factor) }}</el-descriptions-item>
             <el-descriptions-item label="最终权益">{{ fmtMoney(result.metrics.final_value) }}</el-descriptions-item>
             <el-descriptions-item label="净利润">
               <span :class="getColor(result.metrics.pnl)">{{ fmtMoney(result.metrics.pnl) }}</span>
             </el-descriptions-item>
           </el-descriptions>
           
           <!-- Charts placeholder -->
           <div class="chart-container">
             <el-empty description="图表功能开发中..." />
           </div>
        </el-card>
        
        <div v-else class="welcome-placeholder">
          <el-empty description="请在左侧配置策略并运行回测">
             <el-icon :size="60" class="placeholder-icon"><DataLine /></el-icon>
          </el-empty>
        </div>
      </el-col>
    </el-row>
    
    <!-- Stock Selector Dialog (Reuse existing if possible, or simple input) -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { quantApi, type StrategySchema, type BacktestResponse } from '@/api/quant'
import { DataLine, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const strategies = ref<StrategySchema[]>([])
const selectedStrategyId = ref('')
const formParams = ref<Record<string, any>>({})

const config = ref({
  symbol: '000001.SZ',
  initial_cash: 100000,
  commission: 0.0003
})

// Default date range: Past 1 year
const endDate = new Date()
const startDate = new Date()
startDate.setFullYear(endDate.getFullYear() - 1)

const dateRange = ref([
  startDate.toISOString().split('T')[0],
  endDate.toISOString().split('T')[0]
])

const result = ref<BacktestResponse | null>(null)

const currentStrategy = computed(() => {
  return strategies.value.find(s => s.id === selectedStrategyId.value)
})

onMounted(() => {
  fetchStrategies()
})

async function fetchStrategies() {
  try {
    const res = await quantApi.getStrategies()
    strategies.value = res as any // Adapt type if needed
    if (strategies.value.length > 0 && !selectedStrategyId.value) {
      selectedStrategyId.value = strategies.value[0].id
      onStrategyChange()
    }
  } catch (e) {
    ElMessage.error('获取策略列表失败')
  }
}

function onStrategyChange() {
  if (!currentStrategy.value) return
  // Reset params to defaults
  const defaults: Record<string, any> = {}
  currentStrategy.value.params.forEach(p => {
    defaults[p.name] = p.default
  })
  formParams.value = defaults
}

async function runBacktest() {
  if (!selectedStrategyId.value) {
    ElMessage.warning('请选择策略')
    return
  }
  if (!dateRange.value || dateRange.value.length !== 2) {
    ElMessage.warning('请选择时间范围')
    return
  }

  loading.value = true
  result.value = null
  
  try {
    const res = await quantApi.runBacktest({
      strategy_id: selectedStrategyId.value,
      symbol: config.value.symbol,
      start_date: dateRange.value[0],
      end_date: dateRange.value[1],
      initial_cash: config.value.initial_cash,
      commission: config.value.commission,
      params: formParams.value
    })
    
    if (res.status === 'success') {
      result.value = res
      ElMessage.success('回测完成')
    } else {
      ElMessage.error('回测失败: ' + res.error)
    }
  } catch (e: any) {
    ElMessage.error('运行出错: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

function openStockSelector() {
  ElMessage.info('股票选择器开发中，请手动输入代码')
}

// Formatters
function fmtPct(val: number | undefined) {
  if (val === undefined) return '-'
  return val.toFixed(2) + '%'
}
function fmtNum(val: number | undefined) {
  if (val === undefined) return '-'
  return val.toFixed(2)
}
function fmtMoney(val: number | undefined) {
  if (val === undefined) return '-'
  return val.toFixed(2)
}
function getColor(val: number | undefined) {
  if (val === undefined) return ''
  return val >= 0 ? 'text-success' : 'text-danger'
}
</script>

<style scoped lang="scss">
.quant-backtest {
  padding: 20px;
  
  .config-card {
    min-height: 600px;
  }
  
  .run-btn {
    width: 100%;
    margin-top: 20px;
  }
  
  .strat-desc {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
    line-height: 1.4;
  }
  
  .param-item {
    margin-bottom: 12px;
  }
  
  .result-card {
    min-height: 600px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
  }
  
  .metrics-desc {
    margin-bottom: 20px;
  }
  
  .chart-container {
    height: 400px;
    background: #f5f7fa;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .welcome-placeholder {
    height: 600px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fff;
    border-radius: 4px;
  }
  
  .text-success { color: #67C23A; }
  .text-danger { color: #F56C6C; }
}
</style>
