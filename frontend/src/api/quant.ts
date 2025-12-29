import { ApiClient } from './request'

export interface StrategyParam {
  name: string
  default: any
  type: string
}

export interface StrategySchema {
  id: string
  name: string
  description: string
  params: StrategyParam[]
}

export interface BacktestRequest {
  strategy_id: string
  symbol: string
  start_date: string
  end_date: string
  initial_cash: number
  commission: number
  params: Record<string, any>
}

export interface BacktestMetrics {
  sharpe_ratio?: number
  max_drawdown?: number
  max_drawdown_len?: number
  total_trades?: number
  won_trades?: number
  lost_trades?: number
  win_rate?: number
  profit_factor?: number
  initial_cash?: number
  final_value?: number
  pnl?: number
  return_pct?: number
}

export interface BacktestResponse {
  status: string
  metrics?: BacktestMetrics
  error?: string
}

export interface PaperAccount {
  user_id: string
  strategy_id: string
  status: string
  initial_capital: number
  cash: number
  total_assets: number
  positions: Record<string, any>
  created_at: string
  updated_at: string
}

export const quantApi = {
  // Backtest APIs
  async getStrategies() {
    return ApiClient.get<StrategySchema[]>('/api/backtest/strategies')
  },
  
  async runBacktest(data: BacktestRequest) {
    return ApiClient.post<BacktestResponse>('/api/backtest/run', data)
  },

  // Paper Trading APIs
  async createAccount(data: { user_id: string, strategy_id: string, initial_capital: number }) {
    return ApiClient.post<PaperAccount>('/api/paper-trading/accounts', data)
  },

  async getAccount(user_id: string, strategy_id: string) {
    return ApiClient.get<PaperAccount>(`/api/paper-trading/accounts/${user_id}/${strategy_id}`)
  }
}
