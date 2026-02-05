"""
白银K线形态相似性分析器

找到与白银4H最后50根K线形态最相似的其他品种K线段
使用多种相似性度量方法进行形态匹配
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

# 添加父目录到路径，以便导入 metatrader_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据管理器
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


class SilverPatternMatcher:
    """白银K线形态相似性分析器"""
    
    def __init__(self, data_dir: str = "market_data"):
        """
        初始化形态匹配器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_manager = DataManager(data_dir)
        
        # 监测的品种和时间框架
        self.target_symbols = {
            'XAUUSD': ['H1', 'H4'],  # 黄金
            'USOIL': ['H1', 'H4'],   # WTI原油
            'UKOUSD': ['H1', 'H4'],  # 布伦特原油
            'SPX500': ['H1', 'H4', 'D1'],  # 标普500
            'US30': ['H1', 'H4', 'D1'],    # 道琼斯
            'NAS100': ['H1', 'H4', 'D1'],  # 纳斯达克100
        }
        
        # 白银品种 - 基准形态
        self.silver_symbol = 'XAGUSD'
        self.silver_timeframe = 'H4'
        self.silver_bars = 50  # 基准形态长度
        
    def normalize_prices(self, prices: pd.Series) -> pd.Series:
        """
        价格标准化 - 转换为相对变化
        
        Args:
            prices: 价格序列
            
        Returns:
            标准化后的价格序列
        """
        if len(prices) < 2:
            return prices
        
        # 方法1: 相对于第一个价格的百分比变化
        first_price = prices.iloc[0]
        normalized = (prices - first_price) / first_price * 100
        
        return normalized
    
    def extract_price_pattern(self, data: pd.DataFrame, use_close: bool = True) -> pd.Series:
        """
        提取价格形态
        
        Args:
            data: OHLC数据
            use_close: 是否使用收盘价，否则使用典型价格
            
        Returns:
            价格形态序列
        """
        if use_close:
            pattern = data['close']
        else:
            # 使用典型价格 (HLC/3)
            pattern = (data['high'] + data['low'] + data['close']) / 3
        
        return self.normalize_prices(pattern)
    
    def calculate_euclidean_similarity(self, pattern1: pd.Series, pattern2: pd.Series) -> float:
        """
        计算欧几里得距离相似性
        
        Args:
            pattern1: 形态1
            pattern2: 形态2
            
        Returns:
            相似性分数 (0-1，1表示完全相似)
        """
        if len(pattern1) != len(pattern2):
            return 0.0
        
        # 计算欧几里得距离
        distance = np.sqrt(np.sum((pattern1 - pattern2) ** 2))
        
        # 转换为相似性分数 (距离越小，相似性越高)
        max_possible_distance = np.sqrt(len(pattern1) * (100 ** 2))  # 假设最大变化100%
        similarity = 1 - (distance / max_possible_distance)
        
        return max(0, similarity)
    
    def calculate_cosine_similarity(self, pattern1: pd.Series, pattern2: pd.Series) -> float:
        """
        计算余弦相似性
        
        Args:
            pattern1: 形态1
            pattern2: 形态2
            
        Returns:
            相似性分数 (0-1)
        """
        if len(pattern1) != len(pattern2):
            return 0.0
        
        # 计算余弦相似性
        dot_product = np.dot(pattern1, pattern2)
        norm1 = np.linalg.norm(pattern1)
        norm2 = np.linalg.norm(pattern2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_sim = dot_product / (norm1 * norm2)
        
        # 转换到0-1范围
        return (cosine_sim + 1) / 2
    
    def calculate_dtw_similarity(self, pattern1: pd.Series, pattern2: pd.Series) -> float:
        """
        计算动态时间规整(DTW)相似性
        简化版DTW实现
        
        Args:
            pattern1: 形态1
            pattern2: 形态2
            
        Returns:
            相似性分数 (0-1)
        """
        if len(pattern1) != len(pattern2):
            return 0.0
        
        n, m = len(pattern1), len(pattern2)
        
        # 创建DTW矩阵
        dtw_matrix = np.full((n + 1, m + 1), np.inf)
        dtw_matrix[0, 0] = 0
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = abs(pattern1.iloc[i-1] - pattern2.iloc[j-1])
                dtw_matrix[i, j] = cost + min(
                    dtw_matrix[i-1, j],      # 插入
                    dtw_matrix[i, j-1],      # 删除
                    dtw_matrix[i-1, j-1]     # 匹配
                )
        
        # 转换为相似性分数
        max_possible_cost = n * 100  # 假设最大差异100%
        similarity = 1 - (dtw_matrix[n, m] / max_possible_cost)
        
        return max(0, similarity)
    
    def calculate_pattern_correlation(self, pattern1: pd.Series, pattern2: pd.Series) -> float:
        """
        计算形态相关性
        
        Args:
            pattern1: 形态1
            pattern2: 形态2
            
        Returns:
            相关性分数 (0-1)
        """
        if len(pattern1) != len(pattern2) or len(pattern1) < 2:
            return 0.0
        
        correlation = pattern1.corr(pattern2)
        
        if pd.isna(correlation):
            return 0.0
        
        # 转换到0-1范围，取绝对值（形态相似不区分正负相关）
        return abs(correlation)
    
    def find_similar_patterns(self, target_data: pd.DataFrame, silver_pattern: pd.Series, 
                            symbol: str, timeframe: str, window_size: int = 50) -> List[PatternMatch]:
        """
        在目标数据中寻找相似形态
        
        Args:
            target_data: 目标品种数据
            silver_pattern: 白银基准形态
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
        for i in range(len(target_data) - window_size + 1):
            window_data = target_data.iloc[i:i + window_size]
            window_pattern = self.extract_price_pattern(window_data)
            
            # 计算多种相似性度量
            euclidean_sim = self.calculate_euclidean_similarity(silver_pattern, window_pattern)
            cosine_sim = self.calculate_cosine_similarity(silver_pattern, window_pattern)
            correlation_sim = self.calculate_pattern_correlation(silver_pattern, window_pattern)
            dtw_sim = self.calculate_dtw_similarity(silver_pattern, window_pattern)
            
            # 综合相似性分数 (加权平均)
            weights = {
                'euclidean': 0.3,
                'cosine': 0.3,
                'correlation': 0.2,
                'dtw': 0.2
            }
            
            combined_score = (
                euclidean_sim * weights['euclidean'] +
                cosine_sim * weights['cosine'] +
                correlation_sim * weights['correlation'] +
                dtw_sim * weights['dtw']
            )
            
            # 创建匹配结果
            match = PatternMatch(
                symbol=symbol,
                timeframe=timeframe,
                similarity_score=combined_score,
                match_method=f"E:{euclidean_sim:.3f} C:{cosine_sim:.3f} R:{correlation_sim:.3f} D:{dtw_sim:.3f}",
                start_index=i,
                end_index=i + window_size - 1,
                start_time=window_data.index[0],
                end_time=window_data.index[-1],
                pattern_length=window_size
            )
            
            matches.append(match)
        
        return matches
    
    def run_pattern_matching(self, top_n: int = 10, min_similarity: float = 0.3) -> List[PatternMatch]:
        """
        运行形态匹配分析
        
        Args:
            top_n: 返回前N个最相似的形态
            min_similarity: 最小相似性阈值
            
        Returns:
            形态匹配结果列表
        """
        logger.info("开始白银K线形态相似性分析...")
        
        # 获取白银基准形态
        logger.info(f"获取白银基准形态: {self.silver_symbol} {self.silver_timeframe} 最后{self.silver_bars}根K线")
        silver_data = self.data_manager.get_data(
            self.silver_symbol, 
            self.silver_timeframe, 
            count=self.silver_bars
        )
        
        if silver_data is None or len(silver_data) < self.silver_bars:
            logger.error("无法获取白银基准数据")
            return []
        
        # 提取白银价格形态
        silver_pattern = self.extract_price_pattern(silver_data)
        logger.info(f"白银基准形态时间范围: {silver_data.index[0]} 到 {silver_data.index[-1]}")
        
        all_matches = []
        
        # 搜索所有目标品种
        for symbol, timeframes in self.target_symbols.items():
            for timeframe in timeframes:
                try:
                    logger.info(f"搜索 {symbol} {timeframe} 中的相似形态...")
                    
                    # 获取目标品种数据
                    target_data = self.data_manager.get_data(symbol, timeframe, count=5000)
                    
                    if target_data is None:
                        logger.warning(f"无法获取 {symbol} {timeframe} 数据")
                        continue
                    
                    # 寻找相似形态
                    matches = self.find_similar_patterns(
                        target_data, silver_pattern, symbol, timeframe, self.silver_bars
                    )
                    
                    # 过滤低相似性结果
                    filtered_matches = [m for m in matches if m.similarity_score >= min_similarity]
                    
                    logger.info(f"{symbol} {timeframe}: 找到 {len(filtered_matches)} 个相似形态")
                    all_matches.extend(filtered_matches)
                    
                except Exception as e:
                    logger.error(f"搜索 {symbol} {timeframe} 时出错: {e}")
                    continue
        
        # 按相似性分数排序
        all_matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        logger.info(f"形态匹配完成，共找到 {len(all_matches)} 个相似形态")
        
        return all_matches[:top_n]
    
    def print_pattern_results(self, matches: List[PatternMatch]):
        """
        打印形态匹配结果
        
        Args:
            matches: 形态匹配结果列表
        """
        if not matches:
            print("❌ 没有找到相似的K线形态")
            return
        
        print(f"\n{'='*90}")
        print(f"🥈 白银K线形态相似性分析结果")
        print(f"{'='*90}")
        print(f"基准形态: {self.silver_symbol} {self.silver_timeframe} 最后{self.silver_bars}根K线")
        print(f"搜索结果: 找到 {len(matches)} 个最相似的形态")
        print(f"{'='*90}")
        
        print(f"\n📊 最相似的K线形态:")
        print("-" * 90)
        print(f"{'排名':<4} {'品种':<8} {'时间框架':<8} {'相似度':<8} {'时间段':<32} {'详细分数'}")
        print("-" * 90)
        
        for i, match in enumerate(matches, 1):
            # 相似度等级
            if match.similarity_score >= 0.8:
                level = "🔴极高"
            elif match.similarity_score >= 0.6:
                level = "🟡较高"
            elif match.similarity_score >= 0.4:
                level = "🟢中等"
            else:
                level = "⚪较低"
            
            time_range = f"{match.start_time.strftime('%m-%d %H:%M')} ~ {match.end_time.strftime('%m-%d %H:%M')}"
            
            print(f"{i:<4} {match.symbol:<8} {match.timeframe:<8} "
                  f"{match.similarity_score:<8.3f} {time_range:<32} {match.match_method}")
        
        # 显示最佳匹配详情
        if matches:
            best = matches[0]
            print(f"\n🎯 最相似形态详情:")
            print(f"   品种: {best.symbol} ({best.timeframe})")
            print(f"   相似度: {best.similarity_score:.4f}")
            print(f"   时间段: {best.start_time} 到 {best.end_time}")
            print(f"   形态长度: {best.pattern_length} 根K线")
            print(f"   详细分数: {best.match_method}")
            
            if best.similarity_score >= 0.6:
                print(f"\n💡 形态分析:")
                print(f"   • 该时间段的 {best.symbol} 走势与当前白银形态高度相似")
                print(f"   • 可以参考该时间段后续的价格走势")
                print(f"   • 建议结合当时的市场环境进行分析")
            else:
                print(f"\n⚠️  注意: 相似度相对较低，建议谨慎参考")
    
    def save_pattern_results(self, matches: List[PatternMatch], filename: Optional[str] = None):
        """
        保存形态匹配结果
        
        Args:
            matches: 形态匹配结果列表
            filename: 保存文件名
        """
        if not filename:
            filename = f"silver_pattern_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            data = {
                "analysis_info": {
                    "timestamp": datetime.now().isoformat(),
                    "silver_symbol": self.silver_symbol,
                    "silver_timeframe": self.silver_timeframe,
                    "silver_bars": self.silver_bars,
                    "total_matches": len(matches),
                    "analysis_type": "pattern_similarity"
                },
                "matches": []
            }
            
            for match in matches:
                data["matches"].append({
                    "symbol": match.symbol,
                    "timeframe": match.timeframe,
                    "similarity_score": match.similarity_score,
                    "match_method": match.match_method,
                    "start_time": match.start_time.isoformat(),
                    "end_time": match.end_time.isoformat(),
                    "pattern_length": match.pattern_length
                })
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"形态匹配结果已保存到: {filename}")
            print(f"💾 结果已保存到: {filename}")
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")


def main():
    """主函数"""
    print("🔍 白银K线形态相似性分析器")
    print("=" * 50)
    print("功能: 找到与白银4H最后50根K线形态最相似的其他品种K线段")
    print("=" * 50)
    
    # 创建形态匹配器
    matcher = SilverPatternMatcher()
    
    try:
        while True:
            print(f"\n请选择操作:")
            print("1. 运行形态匹配分析")
            print("2. 查看本地数据状态")
            print("3. 更新数据")
            print("4. 退出")
            
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == '1':
                print("\n🔍 开始形态匹配分析...")
                
                # 设置参数
                top_n = int(input("返回前几个最相似形态 (默认10): ") or "10")
                min_similarity = float(input("最小相似度阈值 (默认0.3): ") or "0.3")
                
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