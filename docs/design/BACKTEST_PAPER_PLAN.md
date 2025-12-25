# 策略回测与模拟交易系统开发计划

## 1. 总体架构

本计划旨在为 TradingAgents-CN 增加专业的量化回测与模拟交易能力。系统采用 **"AI + 量化"** 双引擎架构：AI 负责定性分析，量化引擎负责定量回测与执行。

- **核心引擎**: Backtrader (Python)
- **数据存储**: MongoDB (复用现有架构)
- **策略架构**: 插件化策略工厂 (Plugin-based Strategy Factory)
- **模拟交易**: 独立调度器 + 虚拟券商 (Virtual Broker) + 实时数据泵

## 2. 模块设计

建议新增 `app/backtest` 顶级模块，保持与 `app/services` 的清晰边界。

```text
app/
├── backtest/                  # 回测与策略核心模块
│   ├── __init__.py
│   ├── engine.py             # 回测引擎封装 (Backtrader Cerebro)
│   ├── feeds.py              # 数据适配器 (Mongo -> Backtrader)
│   ├── analyzer.py           # 结果分析器 (JSON 格式化)
│   ├── exceptions.py         # 异常定义
│   └── strategies/           # 策略插件目录
│       ├── __init__.py
│       ├── base.py           # 策略基类 (BaseStrategy)
│       ├── registry.py       # 策略注册与发现
│       └── examples/         # 示例策略
│           ├── ma_cross.py
│           └── boll_breakout.py
├── services/
│   ├── backtest_service.py   # 回测业务逻辑 (API 接口调用层)
│   └── paper_trading/        # 模拟交易服务模块
│       ├── __init__.py
│       ├── service.py        # 模拟交易主服务
│       ├── broker.py         # 虚拟券商 (VirtualBroker)
│       ├── scheduler.py      # 交易调度器
│       └── data_pump.py      # 实时数据泵
```

## 3. 开发阶段规划

### 阶段一：基础设施与数据适配 (Infrastructure & Data)
**目标**: 打通 MongoDB 到 Backtrader 的数据链路，跑通最简单的回测。

1.  **项目结构搭建**: 创建 `app/backtest` 目录结构。
2.  **数据适配器 (`MongoPandasData`)**:
    - 继承 `backtrader.feeds.PandasData`。
    - 调用 `HistoricalDataService` 获取 DataFrame。
    - 适配 A股/港股/美股 的字段映射（OHLCV）。
    - 处理复权因子（若有）。
3.  **回测引擎封装 (`BacktestEngine`)**:
    - 封装 `cerebro` 的初始化、资金设置、手续费设置。
    - 实现 `run(strategy_cls, data, **kwargs)` 方法。

### 阶段二：策略工厂与基类设计 (Strategy Factory)
**目标**: 实现"插件化"开发体验，只需继承基类即可写策略。

1.  **策略基类 (`BaseStrategy`)**:
    - 封装 `buy/sell` 操作，增加日志记录。
    - 自动处理订单状态 (`notify_order`, `notify_trade`)。
    - 提供标准化的参数定义 (`params`)。
2.  **策略注册机制 (`Registry`)**:
    - 实现策略自动发现（扫描 `app/backtest/strategies` 目录）。
    - 提供 `get_strategy_schema(name)` 方法，供前端生成表单。
3.  **结果分析器 (`JsonAnalyzer`)**:
    - 自定义 Backtrader Analyzer，提取净值曲线、最大回撤、夏普比率等指标。
    - 输出前端友好的 JSON 格式。

### 阶段三：模拟交易系统 (Paper Trading)
**目标**: 复用策略逻辑，实现基于实时数据的模拟交易。

1.  **数据库设计**:
    - `paper_accounts`: 账户余额、持仓快照。
    - `paper_orders`: 委托与成交记录。
    - `paper_daily_snapshots`: 每日资产曲线。
2.  **虚拟券商 (`VirtualBroker`)**:
    - 实现模拟撮合逻辑（拦截策略信号 -> 读写 MongoDB）。
    - 支持市价单/限价单模拟。
3.  **实时数据泵 (`RealtimeDataPump`)**:
    - 集成 AkShare/Tushare 实时接口。
    - 将实时 Tick/K线 转换为 Backtrader 数据流。
4.  **调度器 (`PaperScheduler`)**:
    - 使用 `APScheduler` 管理策略运行周期（如每分钟、每日收盘前）。

### 阶段四：API 与前端集成 (API & Frontend)
**目标**: 提供 Web 界面供用户交互。

1.  **后端 API**:
    - `POST /api/backtest/run`: 运行回测。
    - `GET /api/strategies`: 获取可用策略列表及参数定义。
    - `POST /api/paper/accounts`: 创建模拟账户。
    - `GET /api/paper/dashboard`: 获取模拟交易看板数据。
2.  **前端页面**:
    - 策略配置与回测运行页。
    - 回测结果展示页（K线图买卖点标记、收益曲线）。
    - 模拟交易监控看板。

## 4. 风险控制与注意事项

1.  **数据一致性**: 确保回测数据与实盘数据源的一致性，避免"未来函数"。
2.  **内存管理**: Backtrader 回测大周期数据时可能占用较多内存，需注意 DataFrame 的优化。
3.  **系统隔离**: 模拟交易模块应具备容错性，单一策略的崩溃不应影响整个系统运行。
