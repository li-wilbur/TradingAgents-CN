<template>
  <div class="quant-paper-trading">
    <el-card class="action-card">
      <template #header>
        <div class="card-header">
          <span>策略模拟交易</span>
          <el-button type="primary" icon="Plus" @click="openCreateDialog">新建策略账户</el-button>
        </div>
      </template>
      
      <!-- Account List (Mocked for now as we don't have list endpoint yet, only create/get) -->
      <!-- We will fetch a specific account for demo -->
      <div class="search-bar" style="margin-bottom: 20px;">
        <el-input v-model="searchUserId" placeholder="输入用户ID查询" style="width: 200px; margin-right: 10px;" />
        <el-select v-model="searchStrategyId" placeholder="选择策略" style="width: 200px; margin-right: 10px;">
             <el-option v-for="s in strategies" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-button type="primary" icon="Search" @click="fetchAccount">查询</el-button>
      </div>

      <el-descriptions v-if="account" title="账户详情" border :column="3">
        <el-descriptions-item label="用户ID">{{ account.user_id }}</el-descriptions-item>
        <el-descriptions-item label="策略ID">{{ account.strategy_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
           <el-tag :type="account.status === 'active' ? 'success' : 'info'">{{ account.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="总资产">{{ fmtMoney(account.total_assets) }}</el-descriptions-item>
        <el-descriptions-item label="现金">{{ fmtMoney(account.cash) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ fmtDate(account.created_at) }}</el-descriptions-item>
      </el-descriptions>
      
      <el-divider v-if="account" content-position="left">持仓详情</el-divider>
      
      <el-table v-if="account" :data="Object.values(account.positions)" border style="margin-top: 10px;">
        <el-table-column prop="symbol" label="代码" />
        <el-table-column prop="quantity" label="数量" />
        <el-table-column prop="cost_price" label="成本价">
          <template #default="{ row }">{{ fmtMoney(row.cost_price) }}</template>
        </el-table-column>
        <el-table-column label="当前价值">
           <template #default="{ row }">-</template> 
        </el-table-column>
      </el-table>

      <el-empty v-if="!account && !loading" description="请输入用户ID和策略ID进行查询" />

    </el-card>

    <!-- Create Dialog -->
    <el-dialog v-model="dialogVisible" title="创建策略账户" width="500px">
      <el-form label-width="100px">
        <el-form-item label="策略">
          <el-select v-model="newAccount.strategy_id" placeholder="选择策略" style="width: 100%">
             <el-option v-for="s in strategies" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="初始资金">
          <el-input-number v-model="newAccount.initial_capital" :step="10000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="用户ID">
          <el-input v-model="newAccount.user_id" placeholder="当前用户" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createAccount">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { quantApi, type StrategySchema, type PaperAccount } from '@/api/quant'
import { Search, Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const strategies = ref<StrategySchema[]>([])
const account = ref<PaperAccount | null>(null)

// Search
const searchUserId = ref('user_001') // Default for demo
const searchStrategyId = ref('')

// Create
const dialogVisible = ref(false)
const newAccount = ref({
  user_id: 'user_001',
  strategy_id: '',
  initial_capital: 100000
})

onMounted(() => {
  fetchStrategies()
})

async function fetchStrategies() {
  try {
    const res = await quantApi.getStrategies()
    strategies.value = res as any
    if (strategies.value.length > 0) {
      searchStrategyId.value = strategies.value[0].id
      newAccount.value.strategy_id = strategies.value[0].id
    }
  } catch (e) {
    ElMessage.error('获取策略列表失败')
  }
}

async function fetchAccount() {
  if (!searchUserId.value || !searchStrategyId.value) {
    ElMessage.warning('请输入用户ID和策略')
    return
  }
  
  loading.value = true
  account.value = null
  try {
    const res = await quantApi.getAccount(searchUserId.value, searchStrategyId.value)
    account.value = res as any
  } catch (e) {
    ElMessage.error('未找到账户或获取失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  dialogVisible.value = true
}

async function createAccount() {
  try {
    await quantApi.createAccount({
      user_id: newAccount.value.user_id,
      strategy_id: newAccount.value.strategy_id,
      initial_capital: newAccount.value.initial_capital
    })
    ElMessage.success('账户创建成功')
    dialogVisible.value = false
    
    // Auto search
    searchUserId.value = newAccount.value.user_id
    searchStrategyId.value = newAccount.value.strategy_id
    fetchAccount()
    
  } catch (e: any) {
    ElMessage.error('创建失败: ' + (e.message || '未知错误'))
  }
}

// Formatters
function fmtMoney(val: number | undefined) {
  if (val === undefined) return '-'
  return '¥' + val.toFixed(2)
}
function fmtDate(val: string | undefined) {
  if (!val) return '-'
  return new Date(val).toLocaleString()
}
</script>

<style scoped lang="scss">
.quant-paper-trading {
  padding: 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
