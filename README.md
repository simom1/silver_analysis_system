# 白银分析系统 (Silver Analysis System)

基于历史K线形态相似性的白银价格分析和预测系统。

## 功能特点

### 1. 形态相似性分析
- 使用改进的多维度相似性算法
- Z-score标准化保留形态特征
- 综合评估形状、趋势、波动率相似度
- 自动排除同期数据，确保预测价值

### 2. 未来走势预测
- 基于历史相似形态预测未来走势
- 加权平均多个历史案例
- 提供价格变化、最大涨跌幅、波动率预测
- 生成详细的预测报告和可视化图表

### 3. 相关性分析
- 分析白银与其他品种的相关性
- 支持多时间周期分析
- 识别领先/滞后关系

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动系统

**Windows用户：**
```bash
启动白银分析系统V2.bat
```

**命令行启动：**
```bash
python main_launcher_v2.py
```

## 主要模块

### 核心模块 (core/)
- `improved_pattern_matcher.py` - 改进版形态匹配器
- `pattern_future_predictor.py` - 未来走势预测器
- `silver_data_manager.py` - 数据管理器
- `silver_correlation_analyzer.py` - 相关性分析器

### 可视化模块 (visualizers/)
- `improved_pattern_visualizer.py` - 改进版形态可视化工具

### 工具模块 (tools/)
- `comprehensive_analysis.py` - 综合分析工具
- `visualization_and_prediction.py` - 可视化和预测工具

## 使用说明

### 1. 形态匹配分析

系统会自动：
1. 获取白银(XAGUSD) H4周期最新50根K线作为基准
2. 在其他品种历史数据中搜索相似形态
3. 返回相似度最高的前N个匹配结果

**参数设置：**
- 返回结果数：建议 5-10 个
- 相似度阈值：建议 0.3-0.5（排除同期数据后）

### 2. 未来走势预测

基于历史相似形态的后续走势，预测白银未来可能的价格变化：
- 预测K线数量：建议 10-20 根
- 加权平均：相似度越高权重越大
- 输出：预测报告 + 可视化图表

### 3. 数据更新

系统支持从 MetaTrader 5 自动获取最新数据：
```bash
python core/silver_data_manager.py
```

## 相似度算法

系统使用多维度综合评分：

```
综合相似度 = 形状相似度 × 0.5 + 趋势相似度 × 0.3 + 波动率相似度 × 0.2
```

### 形状相似度
- 使用 Pearson 相关系数
- Z-score 标准化后计算

### 趋势相似度
- 总体涨跌幅相似度
- 趋势斜率相似度
- 上涨K线比例相似度

### 波动率相似度
- 波动率（标准差）相似度
- 最大涨跌幅相似度
- 转折点数量相似度

## 输出文件

所有分析结果保存在 `outputs/` 目录：
- `improved_pattern_visualization_*.png` - 形态对比图
- `silver_prediction_report_*.txt` - 预测报告
- `improved_pattern_matches_*.json` - 匹配结果数据

## 系统要求

- Python 3.8+
- MetaTrader 5 (可选，用于数据更新)
- Windows 系统（推荐）

## 依赖库

主要依赖：
- pandas - 数据处理
- numpy - 数值计算
- matplotlib - 图表绘制
- MetaTrader5 - MT5数据接口（可选）

## 版本历史

### V2.0 (2026-02-06)
- 改进形态匹配算法
- 添加未来走势预测功能
- 优化可视化效果
- 自动排除同期数据

### V1.0
- 基础形态匹配功能
- 相关性分析
- 数据管理

## 注意事项

⚠️ **免责声明**
- 本系统基于历史数据分析，不构成投资建议
- 市场有风险，投资需谨慎
- 请结合其他分析方法和风险管理策略

## 技术支持

如有问题或建议，请提交 Issue。

## 许可证

MIT License
