# 🥈 白银分析系统 (Silver Analysis System)

## �  功能特性

### 核心分析功能
- **相关性分析**: 分析白银与13个主要金融品种的相关性
- **K线形态匹配**: 找到与白银最相似的历史形态
- **智能品种检测**: 自动识别MT5平台可用品种
- **实时数据分析**: 直接从MT5获取最新市场数据

### 支持的金融品种
- 贵金属: XAUUSD (黄金)
- 原油: XTIUSD (WTI), XBRUSD (布伦特)
- 股指: US500 (标普500), US30 (道指), NAS100 (纳指)
- 外汇: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD

## 🚀 快速开始

### 1. 启动主程序
```bash
# 双击运行
启动白银分析系统.bat

# 或使用Python
python main_launcher.py
```

### 2. 使用改进的分析工具
```bash
python tools/improved_silver_analysis.py
```

### 3. 快速形态匹配
```bash
python tools/quick_pattern_finder.py
```

## � 分析结r果示例

- **黄金4H相关性**: 0.7912 (强相关)
- **澳元美元4H**: 0.5656 (中等相关)
- **形态匹配最高相似度**: 0.933

## 💡 交易建议

### 主要策略
- 关注黄金4H走势 (最强相关指标)
- 参考澳元美元、纽元美元联动
- 结合美股指数风险情绪

### 风险管理
- 严格止损设置
- 合理仓位控制
- 多品种分散风险

## 📁 项目结构

```
silver_analysis_system/
├── core/                 # 核心分析模块
├── tools/                # 分析工具
├── visualizers/          # 可视化模块
├── config/               # 配置文件
├── market_data/          # 市场数据
├── outputs/              # 分析结果
└── docs/                 # 文档说明
```

## ⚠️ 使用要求

- Python 3.7+
- MetaTrader 5 终端
- 必要的Python包: pandas, numpy, matplotlib, MetaTrader5

## 📞 支持

如有问题，请查看 `docs/` 目录中的详细文档。

---

**免责声明**: 本系统仅供分析参考，不构成投资建议。交易有风险，投资需谨慎。