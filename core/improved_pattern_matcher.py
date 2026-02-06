"""
改进版白银K线形态相似性分析器

主要改进：
1. 更好的标准化方法（Z-score标准化）
2. 考虑形态特征（涨跌幅、波动率、趋势方向）
3. 改进的相似度计算
4. 更合理的权重分配
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import json
import sys
import os
import warnings

# 过滤numpy的警告
warnings.filterwarnings('ignore', category=RuntimeWarning, module='numpy')
warnings.filterwarnings('ignore', message='Degrees of freedom <= 0 for slice')
warnings.filterwarnings('ignore', message='divide by zero encountered')
warnings.filterwarnings('ignore', message='invalid value encountered')

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据管理器 - 支持直接运行和模块导入
try:
    from .silver_data_manager import DataManager
except ImportError:
    from silver_data_manager import DataManager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """形态匹配结果"""
    symbol: str
    timeframe: str
    similarity_score: float
    match_method: str
    start_index: int
    end_index: int
    start_time: datetime
    end_time: datetime
    pattern_length: int
    trend_similarity: float  # 趋势相似度
    volatility_similarity: float  # 波动率相似度
    shape_similarity: float  # 形状相似度


class ImprovedPatternMatcher:
    """改进版白银K线形态相似性分析器"""
    
    def __init__(self, data_dir: str = "market_data"):
        """初始化形态匹配器"""
        self.data_manager = DataManager(data_dir)
        
        # 白银品种 - 基准形态
        self.silver_symbol = 'XAGUSD'
        self.silver_timeframe = 'H4'
        self.silver_bars = 50  # 基准形态长度
        
        # 自动检测可用的品种和时间框架
        self.target_symbols = self.detect_available_symbols()
    
    def detect_available_symbols(self) -> Dict[str, List[str]]:
        """
        自动检测本地可用的品种和时间框架
        
        Returns:
            可用品种字典 {symbol: [timeframes]}
        """
        import os
        from pathlib import Path
        
        available_symbols = {}
        
        # 检查本地数据目录
        raw_data_dir = Path(self.data_manager.data_dir) / "raw_data"
        
        if not raw_data_dir.exists():
            logger.warning("本地数据目录不存在，使用默认品种列表")
            return self.get_default_symbols()
        
        # 扫描所有CSV文件
        for csv_file in raw_data_dir.glob("*.csv"):
            filename = csv_file.stem  # 不含扩展名的文件名
            
            # 解析文件名: SYMBOL_TIMEFRAME.csv
            parts = filename.split('_')
            if len(parts) >= 2:
                symbol = '_'.join(parts[:-1])  # 品种名（可能包含下划线）
                timeframe = parts[-1]  # 时间框架
                
                # 排除白银自己
                if symbol == self.silver_symbol:
                    continue
                
                # 只保留常用时间框架
                if timeframe in ['H1', 'H4', 'D1']:
                    if symbol not in available_symbols:
                        available_symbols[symbol] = []
                    if timeframe not in available_symbols[symbol]:
                        available_symbols[symbol].append(timeframe)
        
        if not available_symbols:
            logger.warning("未找到可用的本地数据，使用默认品种列表")
            return self.get_default_symbols()
        
        logger.info(f"检测到 {len(available_symbols)} 个可用品种")
        for symbol, timeframes in available_symbols.items():
            logger.info(f"  - {symbol}: {', '.join(timeframes)}")
        
        return available_symbols
    
    def get_default_symbols(self) -> Dict[str, List[str]]:
        """
        获取默认品种列表（当无法检测本地数据时使用）
        
        Returns:
            默认品种字典
        """
        return {
            'XAUUSD': ['H1', 'H4'],  # 黄金
            'USOIL': ['H1', 'H4'],   # WTI原油
            'UKOUSD': ['H1', 'H4'],  # 布伦特原油
        }
    
    def normalize_price_series(self, prices: pd.Series) -> np.ndarray:
        """
        价格序列标准化
        转换为相对于第一个价格的百分比变化
        
        Args:
            prices: 价格序列
            
        Returns:
            标准化后的价格数组
        """
        if len(prices) < 2:
            return np.array([0])
        
        first_price = prices.iloc[0]
        normalized = ((prices - first_price) / first_price * 100).values
        return normalized
    
    def normalize_pattern_zscore(self, prices: pd.Series) -> pd.Series:
        """
        Z-score标准化 - 更好地保留形态特征
        
        Args:
            prices: 价格序列
            
        Returns:
            标准化后的价格序列
        """
        if len(prices) < 2:
            return prices
        
        mean = prices.mean()
        std = prices.std()
        
        if std == 0:
            return pd.Series(np.zeros(len(prices)), index=prices.index)
        
        normalized = (prices - mean) / std
        return normalized
    
    def normalize_pattern_minmax(self, prices: pd.Series) -> pd.Series:
        """
        Min-Max标准化到0-1范围
        
        Args:
            prices: 价格序列
            
        Returns:
            标准化后的价格序列
        """
        if len(prices) < 2:
            return prices
        
        min_price = prices.min()
        max_price = prices.max()
        
        if max_price == min_price:
            return pd.Series(np.zeros(len(prices)), index=prices.index)
        
        normalized = (prices - min_price) / (max_price - min_price)
        return normalized
    
    def extract_pattern_features(self, data: pd.DataFrame) -> Dict:
        """
        提取形态特征
        
        Args:
            data: OHLC数据
            
        Returns:
            特征字典
        """
        close_prices = data['close']
        high_prices = data['high']
        low_prices = data['low']
        
        # 1. 总体涨跌幅
        total_return = (close_prices.iloc[-1] - close_prices.iloc[0]) / close_prices.iloc[0]
        
        # 2. 波动率（标准差）
        returns = close_prices.pct_change().dropna()
        volatility = returns.std()
        
        # 3. 最大涨幅和最大跌幅
        max_gain = (high_prices.max() - close_prices.iloc[0]) / close_prices.iloc[0]
        max_loss = (low_prices.min() - close_prices.iloc[0]) / close_prices.iloc[0]
        
        # 4. 趋势方向（线性回归斜率）
        x = np.arange(len(close_prices))
        y = close_prices.values
        trend_slope = np.polyfit(x, y, 1)[0]
        
        # 5. 转折点数量（价格方向改变的次数）
        price_changes = np.diff(close_prices.values)
        direction_changes = np.sum(np.diff(np.sign(price_changes)) != 0)
        
        # 6. 上涨K线和下跌K线比例
        shifted_prices = np.roll(close_prices.values, 1)
        up_bars = np.sum(close_prices.values[1:] > shifted_prices[1:])
        down_bars = len(close_prices) - 1 - up_bars
        up_ratio = up_bars / (len(close_prices) - 1) if len(close_prices) > 1 else 0.5
        
        return {
            'total_return': total_return,
            'volatility': volatility,
            'max_gain': max_gain,
            'max_loss': max_loss,
            'trend_slope': trend_slope,
            'direction_changes': direction_changes,
            'up_ratio': up_ratio
        }
    
    def calculate_shape_similarity(self, pattern1: pd.Series, pattern2: pd.Series) -> float:
        """
        计算形状相似度（使用归一化后的皮尔逊相关系数）
        
        Args:
            pattern1: 形态1（已标准化）
            pattern2: 形态2（已标准化）
            
        Returns:
            相似性分数 (0-1)
        """
        if len(pattern1) != len(pattern2) or len(pattern1) < 3:
            return 0.0
        
        # 检查标准差是否为0（避免除零警告）
        if pattern1.std() == 0 or pattern2.std() == 0:
            return 0.0
        
        try:
            correlation = pattern1.corr(pattern2)
            
            if pd.isna(correlation) or np.isinf(correlation):
                return 0.0
            
            # 相关系数范围 [-1, 1]，转换到 [0, 1]
            # 注意：我们只关心正相关（形态相似），负相关表示反向形态
            return max(0, correlation)
        except:
            return 0.0
    
    def calculate_trend_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        计算趋势相似度
        
        Args:
            features1: 形态1的特征
            features2: 形态2的特征
            
        Returns:
            相似性分数 (0-1)
        """
        # 1. 总体涨跌幅相似度
        return_diff = abs(features1['total_return'] - features2['total_return'])
        return_sim = 1 / (1 + return_diff * 10)  # 差异越小，相似度越高
        
        # 2. 趋势斜率相似度
        slope_diff = abs(features1['trend_slope'] - features2['trend_slope'])
        slope_sim = 1 / (1 + slope_diff * 100)
        
        # 3. 上涨比例相似度
        up_ratio_diff = abs(features1['up_ratio'] - features2['up_ratio'])
        up_ratio_sim = 1 - up_ratio_diff
        
        # 综合趋势相似度
        trend_similarity = (return_sim * 0.4 + slope_sim * 0.4 + up_ratio_sim * 0.2)
        
        return trend_similarity
    
    def calculate_volatility_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        计算波动率相似度
        
        Args:
            features1: 形态1的特征
            features2: 形态2的特征
            
        Returns:
            相似性分数 (0-1)
        """
        # 1. 波动率相似度
        vol_diff = abs(features1['volatility'] - features2['volatility'])
        vol_sim = 1 / (1 + vol_diff * 50)
        
        # 2. 最大涨幅相似度
        max_gain_diff = abs(features1['max_gain'] - features2['max_gain'])
        max_gain_sim = 1 / (1 + max_gain_diff * 10)
        
        # 3. 最大跌幅相似度
        max_loss_diff = abs(features1['max_loss'] - features2['max_loss'])
        max_loss_sim = 1 / (1 + max_loss_diff * 10)
        
        # 4. 转折点数量相似度
        direction_diff = abs(features1['direction_changes'] - features2['direction_changes'])
        direction_sim = 1 / (1 + direction_diff * 0.1)
        
        # 综合波动率相似度
        volatility_similarity = (vol_sim * 0.3 + max_gain_sim * 0.25 + 
                                max_loss_sim * 0.25 + direction_sim * 0.2)
        
        return volatility_similarity
    
    def find_similar_patterns(self, target_data: pd.DataFrame, silver_pattern: pd.Series,
                            silver_features: Dict, symbol: str, timeframe: str, 
                            window_size: int = 50) -> List[PatternMatch]:
        """
        在目标数据中寻找相似形态
        
        Args:
            target_data: 目标品种数据
            silver_pattern: 白银基准形态（已标准化）
            silver_features: 白银形态特征
            symbol: 品种代码
            timeframe: 时间框架
            window_size: 滑动窗口大小
            
        Returns:
            相似形态匹配结果列表
        """
        matches = []
        
        if len(target_data) < window_size:
            logger.warning(f"{symbol} {timeframe} 数据不足，跳过")
            return matches
        
        # 滑动窗口搜索
        # 步长设置：每次移动1根K线，确保不遗漏任何可能的匹配
        # 如果数据量太大可以设置为3-5，但会降低精度
        step = 1
        total_windows = len(target_data) - window_size + 1
        
        for i in range(0, total_windows, step):
            window_data = target_data.iloc[i:i + window_size]
            
            # 标准化价格形态
            window_pattern = self.normalize_pattern_zscore(window_data['close'])
            
            # 提取特征
            window_features = self.extract_pattern_features(window_data)
            
            # 计算三种相似度
            shape_sim = self.calculate_shape_similarity(silver_pattern, window_pattern)
            trend_sim = self.calculate_trend_similarity(silver_features, window_features)
            vol_sim = self.calculate_volatility_similarity(silver_features, window_features)
            
            # 综合相似性分数（新的权重分配）
            weights = {
                'shape': 0.5,      # 形状最重要
                'trend': 0.3,      # 趋势次之
                'volatility': 0.2  # 波动率
            }
            
            combined_score = (
                shape_sim * weights['shape'] +
                trend_sim * weights['trend'] +
                vol_sim * weights['volatility']
            )
            
            # 如果形状相似度很低，但趋势和波动相似，也给一定分数
            # 这样可以找到"走势方向相似"的形态，即使具体形状不完全一样
            if shape_sim < 0.3 and trend_sim > 0.5 and vol_sim > 0.5:
                # 给予趋势和波动更高的权重
                alternative_score = trend_sim * 0.5 + vol_sim * 0.5
                combined_score = max(combined_score, alternative_score * 0.8)  # 最多给到0.8的权重
            
            # 创建匹配结果
            match = PatternMatch(
                symbol=symbol,
                timeframe=timeframe,
                similarity_score=combined_score,
                match_method=f"形状:{shape_sim:.3f} 趋势:{trend_sim:.3f} 波动:{vol_sim:.3f}",
                start_index=i,
                end_index=i + window_size - 1,
                start_time=window_data.index[0],
                end_time=window_data.index[-1],
                pattern_length=window_size,
                trend_similarity=trend_sim,
                volatility_similarity=vol_sim,
                shape_similarity=shape_sim
            )
            
            matches.append(match)
        
        return matches
    
    def run_pattern_matching(self, top_n: int = 10, min_similarity: float = 0.3, 
                           exclude_recent: bool = True, show_all_top: bool = False) -> List[PatternMatch]:
        """
        运行形态匹配分析
        
        核心逻辑：
        1. 获取白银(XAGUSD) 4H周期的最新50根K线作为基准形态
        2. 在其他品种的历史数据中，用50根K线的滑动窗口搜索相似形态
        3. 返回相似度最高的前N个匹配结果
        
        Args:
            top_n: 返回前N个最相似的形态
            min_similarity: 最小相似性阈值（建议0.3-0.5，排除同期后建议0.3）
            exclude_recent: 是否排除与白银同期的数据（避免找到同步走势）
            show_all_top: 是否显示前N个结果（即使低于阈值）
            
        Returns:
            形态匹配结果列表
        """
        logger.info("=" * 80)
        logger.info("开始改进版白银K线形态相似性分析...")
        logger.info("=" * 80)
        
        # ========== 步骤1: 获取白银最新50根4H K线作为基准 ==========
        logger.info(f"📊 步骤1: 获取白银基准形态")
        logger.info(f"   品种: {self.silver_symbol}")
        logger.info(f"   周期: {self.silver_timeframe}")
        logger.info(f"   K线数: 最新 {self.silver_bars} 根")
        
        silver_data_full = self.data_manager.get_data(
            self.silver_symbol, 
            self.silver_timeframe, 
            count=self.silver_bars
        )
        
        if silver_data_full is None or len(silver_data_full) < self.silver_bars:
            logger.error("❌ 无法获取白银基准数据")
            return []
        
        # 重要：只取最后50根K线作为基准
        silver_data = silver_data_full.iloc[-self.silver_bars:]
        
        # 确认获取的是最新数据
        logger.info(f"✅ 成功获取白银数据")
        logger.info(f"   时间范围: {silver_data.index[0]} 到 {silver_data.index[-1]}")
        logger.info(f"   数据条数: {len(silver_data)} 根K线")
        logger.info(f"   最新价格: {silver_data['close'].iloc[-1]:.2f}")
        
        # 标准化白银价格形态
        silver_pattern = self.normalize_pattern_zscore(silver_data['close'])
        
        # 提取白银形态特征
        silver_features = self.extract_pattern_features(silver_data)
        
        logger.info(f"   形态特征:")
        logger.info(f"   - 总涨跌幅: {silver_features['total_return']:.2%}")
        logger.info(f"   - 波动率: {silver_features['volatility']:.4f}")
        logger.info(f"   - 趋势斜率: {silver_features['trend_slope']:.6f}")
        logger.info(f"   - 转折点数: {silver_features['direction_changes']}")
        logger.info(f"   - 上涨K线比例: {silver_features['up_ratio']:.2%}")
        
        all_matches = []
        
        # ========== 步骤2: 在其他品种历史数据中搜索相似形态 ==========
        logger.info(f"\n📊 步骤2: 在其他品种历史数据中搜索相似形态")
        logger.info(f"   滑动窗口大小: {self.silver_bars} 根K线")
        logger.info(f"   最小相似度阈值: {min_similarity}")
        logger.info("")
        # 搜索所有目标品种
        for symbol, timeframes in self.target_symbols.items():
            for timeframe in timeframes:
                try:
                    logger.info(f"🔍 搜索 {symbol} {timeframe}...")
                    
                    # 获取目标品种的历史数据（足够多的数据用于滑动窗口搜索）
                    target_data = self.data_manager.get_data(symbol, timeframe, count=5000)
                    
                    if target_data is None:
                        logger.warning(f"   ⚠️  无法获取 {symbol} {timeframe} 数据")
                        continue
                    
                    logger.info(f"   获取到 {len(target_data)} 根K线数据")
                    
                    # 检查数据量是否足够
                    if len(target_data) < 1000:
                        logger.warning(f"   ⚠️  数据量不足 ({len(target_data)} < 1000)，建议更新数据")
                        if len(target_data) < 100:
                            logger.warning(f"   ⚠️  数据量太少，跳过此品种")
                            continue
                    
                    logger.info(f"   时间范围: {target_data.index[0]} 到 {target_data.index[-1]}")
                    
                    # 排除与白银基准时间段重叠的数据
                    silver_start_time = silver_data.index[0]
                    silver_end_time = silver_data.index[-1]
                    
                    # 过滤掉与白银时间段重叠的数据
                    # 只保留结束时间早于白银开始时间的数据
                    original_count = len(target_data)
                    target_data = target_data[target_data.index < silver_start_time]
                    excluded_count = original_count - len(target_data)
                    
                    if len(target_data) < self.silver_bars:
                        logger.warning(f"   ⚠️  排除同期数据后，剩余数据不足 ({len(target_data)} < {self.silver_bars})，跳过")
                        continue
                    
                    logger.info(f"   ✅ 排除同期数据 ({silver_start_time} 之后)，排除了 {excluded_count} 根K线")
                    logger.info(f"   搜索范围: {target_data.index[0]} 到 {target_data.index[-1]}")
                    logger.info(f"   可搜索数据: {len(target_data)} 根K线")
                    
                    # 在历史数据中用50根K线的滑动窗口搜索相似形态
                    matches = self.find_similar_patterns(
                        target_data, 
                        silver_pattern, 
                        silver_features,
                        symbol, 
                        timeframe, 
                        window_size=self.silver_bars  # 固定使用50根K线窗口
                    )
                    
                    # 显示所有匹配的最高相似度和详细信息（用于调试）
                    if matches:
                        best_match = max(matches, key=lambda x: x.similarity_score)
                        logger.info(f"   📊 最高相似度: {best_match.similarity_score:.3f}")
                        logger.info(f"      - 形状: {best_match.shape_similarity:.3f}")
                        logger.info(f"      - 趋势: {best_match.trend_similarity:.3f}")
                        logger.info(f"      - 波动: {best_match.volatility_similarity:.3f}")
                    
                    # 过滤低相似性结果
                    filtered_matches = [m for m in matches if m.similarity_score >= min_similarity]
                    
                    if filtered_matches:
                        logger.info(f"   ✅ 找到 {len(filtered_matches)} 个相似形态 (>= {min_similarity})")
                    else:
                        if matches:
                            logger.info(f"   ℹ️  未找到相似度 >= {min_similarity} 的形态")
                        else:
                            logger.info(f"   ℹ️  未找到任何匹配")
                    
                    all_matches.extend(filtered_matches)
                    
                except Exception as e:
                    logger.error(f"   ❌ 搜索 {symbol} {timeframe} 时出错: {e}")
                    continue
        
        # ========== 步骤3: 排序并返回结果 ==========
        logger.info(f"\n📊 步骤3: 汇总结果")
        logger.info(f"   总共找到 {len(all_matches)} 个相似形态 (>= {min_similarity})")
        
        # 按相似性分数排序
        all_matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        if all_matches:
            logger.info(f"   最高相似度: {all_matches[0].similarity_score:.3f} ({all_matches[0].symbol} {all_matches[0].timeframe})")
            logger.info(f"   返回前 {min(top_n, len(all_matches))} 个结果")
        else:
            logger.warning(f"   ⚠️  没有找到相似度 >= {min_similarity} 的形态")
            if show_all_top:
                logger.info(f"   💡 提示: 可以尝试降低阈值或查看所有结果")
        
        logger.info("=" * 80)
        logger.info("✅ 形态匹配分析完成")
        logger.info("=" * 80)
        
        return all_matches[:top_n]
    
    def print_pattern_results(self, matches: List[PatternMatch]):
        """打印形态匹配结果"""
        if not matches:
            print("❌ 没有找到相似的K线形态")
            return
        
        print(f"\n{'='*100}")
        print(f"🥈 改进版白银K线形态相似性分析结果")
        print(f"{'='*100}")
        print(f"基准形态: {self.silver_symbol} {self.silver_timeframe} 最后{self.silver_bars}根K线")
        print(f"搜索结果: 找到 {len(matches)} 个最相似的形态")
        print(f"{'='*100}")
        
        print(f"\n📊 最相似的K线形态:")
        print("-" * 100)
        print(f"{'排名':<4} {'品种':<8} {'时间框架':<8} {'综合相似度':<10} {'形状':<8} {'趋势':<8} {'波动':<8} {'时间段':<32}")
        print("-" * 100)
        
        for i, match in enumerate(matches, 1):
            # 相似度等级
            if match.similarity_score >= 0.8:
                level = "🔴"
            elif match.similarity_score >= 0.7:
                level = "🟠"
            elif match.similarity_score >= 0.6:
                level = "🟡"
            else:
                level = "🟢"
            
            time_range = f"{match.start_time.strftime('%m-%d %H:%M')} ~ {match.end_time.strftime('%m-%d %H:%M')}"
            
            print(f"{i:<4} {match.symbol:<8} {match.timeframe:<8} "
                  f"{level}{match.similarity_score:<9.3f} "
                  f"{match.shape_similarity:<8.3f} {match.trend_similarity:<8.3f} "
                  f"{match.volatility_similarity:<8.3f} {time_range:<32}")
        
        # 显示最佳匹配详情
        if matches:
            best = matches[0]
            print(f"\n🎯 最相似形态详情:")
            print(f"   品种: {best.symbol} ({best.timeframe})")
            print(f"   综合相似度: {best.similarity_score:.4f}")
            print(f"   - 形状相似度: {best.shape_similarity:.4f}")
            print(f"   - 趋势相似度: {best.trend_similarity:.4f}")
            print(f"   - 波动相似度: {best.volatility_similarity:.4f}")
            print(f"   时间段: {best.start_time} 到 {best.end_time}")
            print(f"   形态长度: {best.pattern_length} 根K线")
            
            if best.similarity_score >= 0.7:
                print(f"\n💡 形态分析:")
                print(f"   • 该时间段的 {best.symbol} 走势与当前白银形态高度相似")
                print(f"   • 可以参考该时间段后续的价格走势")
                print(f"   • 建议结合当时的市场环境进行分析")
            else:
                print(f"\n⚠️  注意: 相似度中等，建议谨慎参考")
    
    def save_pattern_results(self, matches: List[PatternMatch], filename: Optional[str] = None):
        """保存形态匹配结果"""
        # 确保 outputs 目录存在
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
        os.makedirs(output_dir, exist_ok=True)
        
        if not filename:
            filename = f"improved_pattern_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 使用完整路径
        filepath = os.path.join(output_dir, filename)
        
        try:
            data = {
                "analysis_info": {
                    "timestamp": datetime.now().isoformat(),
                    "silver_symbol": self.silver_symbol,
                    "silver_timeframe": self.silver_timeframe,
                    "silver_bars": self.silver_bars,
                    "total_matches": len(matches),
                    "analysis_type": "improved_pattern_similarity",
                    "algorithm_version": "2.0"
                },
                "matches": []
            }
            
            for match in matches:
                data["matches"].append({
                    "symbol": match.symbol,
                    "timeframe": match.timeframe,
                    "similarity_score": match.similarity_score,
                    "shape_similarity": match.shape_similarity,
                    "trend_similarity": match.trend_similarity,
                    "volatility_similarity": match.volatility_similarity,
                    "match_method": match.match_method,
                    "start_time": match.start_time.isoformat(),
                    "end_time": match.end_time.isoformat(),
                    "pattern_length": match.pattern_length
                })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"形态匹配结果已保存到: {filepath}")
            print(f"💾 结果已保存到: {filepath}")
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")


def main():
    """主函数"""
    print("🔍 改进版白银K线形态相似性分析器")
    print("=" * 60)
    print("改进点:")
    print("1. 使用Z-score标准化，更好地保留形态特征")
    print("2. 提取多维度特征（涨跌幅、波动率、趋势、转折点）")
    print("3. 分别计算形状、趋势、波动率相似度")
    print("4. 更合理的权重分配和阈值设置")
    print("=" * 60)
    
    # 创建形态匹配器
    matcher = ImprovedPatternMatcher()
    
    try:
        while True:
            print(f"\n请选择操作:")
            print("1. 运行改进版形态匹配分析")
            print("2. 查看本地数据状态")
            print("3. 更新数据")
            print("4. 退出")
            
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == '1':
                print("\n🔍 开始改进版形态匹配分析...")
                
                # 设置参数
                print("\n" + "=" * 60)
                print("📋 参数说明")
                print("=" * 60)
                print("1️⃣  返回结果数:")
                print("   - 找到多少个相似的历史形态")
                print("   - 每个形态 = 50根连续K线")
                print("   - 例如: 输入10 = 找10个历史形态")
                print()
                print("2️⃣  相似度阈值:")
                print("   - 过滤掉相似度低的形态")
                print("   - 范围: 0.0 - 1.0 (越高越相似)")
                print("   - 推荐: 0.3-0.5 (排除同期数据后建议降低)")
                print()
                print("⚠️  注意: 系统会自动排除与白银同期的数据")
                print("   这样找到的都是历史形态，有预测价值")
                print("   但可能导致相似度整体偏低，建议阈值设为0.3")
                print("=" * 60)
                print()
                
                top_n = int(input("返回多少个相似形态 (默认10): ") or "10")
                min_similarity = float(input("最小相似度阈值 (默认0.3，建议0.3-0.5): ") or "0.3")
                
                # 运行分析
                matches = matcher.run_pattern_matching(top_n=top_n, min_similarity=min_similarity)
                
                # 显示结果
                matcher.print_pattern_results(matches)
                
                # 保存结果
                if matches:
                    save = input("\n是否保存结果? (y/N): ").strip().lower()
                    if save in ['y', 'yes', '是']:
                        matcher.save_pattern_results(matches)
                
            elif choice == '2':
                print("\n📊 本地数据状态:")
                matcher.data_manager.print_data_summary()
                
            elif choice == '3':
                print("\n🔄 更新数据...")
                all_symbols = dict(matcher.target_symbols)
                all_symbols[matcher.silver_symbol] = [matcher.silver_timeframe]
                
                results = matcher.data_manager.batch_update_data(all_symbols, count=5000)
                
                print(f"\n📊 更新结果:")
                for symbol, symbol_results in results.items():
                    for timeframe, success in symbol_results.items():
                        status = "✅" if success else "❌"
                        print(f"{status} {symbol} {timeframe}")
                
            elif choice == '4':
                print("👋 再见!")
                break
                
            else:
                print("❌ 无效选择，请重新输入")
                
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        logger.error(f"程序运行错误: {e}")
        print(f"❌ 程序错误: {e}")
    finally:
        matcher.data_manager.disconnect_mt5()


if __name__ == "__main__":
    main()
