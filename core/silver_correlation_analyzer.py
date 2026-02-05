"""
白银相关性分析器

分析白银1H最后50根K线与其他金融产品的相关性
监测标的：黄金1H、原油1H、标普500、US30、US100的1H、4H、日线
找到最相关的时间框架和品种

支持本地数据缓存，避免重复拉取数据
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import json

# 导入数据管理器
from silver_data_manager import DataManager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CorrelationResult:
    """相关性分析结果"""
    symbol: str
    timeframe: str
    correlation: float
    p_value: float
    data_points: int
    start_time: datetime
    end_time: datetime


class SilverCorrelationAnalyzer:
    """白银相关性分析器"""
    
    def __init__(self, data_dir: str = "market_data"):
        """
        初始化分析器
        
        Args:
            data_dir: 数据存储目录
        """
        # 使用数据管理器
        self.data_manager = DataManager(data_dir)
        
        # 监测的品种和时间框架 - 根据MT5经纪商支持的代码
        self.target_symbols = {
            'XAUUSD': ['H1', 'H4'],   # 黄金
            'XTIUSD': ['H1', 'H4'],   # WTI原油
            'XBRUSD': ['H1', 'H4'],   # 布伦特原油
            'US500': ['H1', 'H4'],    # 标普500
            'US30': ['H1', 'H4'],     # 道琼斯
            'NAS100': ['H1', 'H4'],   # 纳斯达克100
            'EURUSD': ['H1', 'H4'],   # 欧元美元
            'GBPUSD': ['H1', 'H4'],   # 英镑美元
        }
        
        # 白银品种 - 检测标的
        self.silver_symbol = 'XAGUSD'
        self.silver_timeframe = 'H4'  # 4小时图
        self.silver_bars = 50  # 分析最后50根K线 - 检测标的保持不变
        
    def get_price_data(self, symbol: str, timeframe: str, count: int = 3000, 
                      force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """
        获取价格数据 - 优先使用本地缓存
        
        Args:
            symbol: 品种代码
            timeframe: 时间框架
            count: 获取的K线数量
            force_refresh: 强制刷新数据
            
        Returns:
            价格数据DataFrame或None
        """
        try:
            # 使用数据管理器获取数据
            df = self.data_manager.get_data(
                symbol=symbol,
                timeframe=timeframe,
                count=count,
                force_refresh=force_refresh,
                max_age_hours=1  # 数据1小时内有效
            )
            
            if df is None or df.empty:
                logger.warning(f"未获取到 {symbol} {timeframe} 的数据")
                return None
                
            logger.info(f"获取到 {symbol} {timeframe} 数据: {len(df)} 根K线 (本地缓存)")
            return df
                
        except Exception as e:
            logger.error(f"获取 {symbol} {timeframe} 数据失败: {e}")
            return None
    
    def calculate_returns(self, df: pd.DataFrame) -> pd.Series:
        """
        计算收益率
        
        Args:
            df: 价格数据DataFrame
            
        Returns:
            收益率序列
        """
        if df.empty or 'close' not in df.columns:
            return pd.Series(dtype=float)
            
        # 计算对数收益率
        returns = np.log(df['close'] / df['close'].shift(1)).dropna()
        return returns
    
    def align_data_by_time(self, silver_data: pd.DataFrame, other_data: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        按时间对齐两个数据集
        
        Args:
            silver_data: 白银数据
            other_data: 其他品种数据
            
        Returns:
            对齐后的收益率序列元组
        """
        # 计算收益率
        silver_returns = self.calculate_returns(silver_data)
        other_returns = self.calculate_returns(other_data)
        
        if silver_returns.empty or other_returns.empty:
            return pd.Series(dtype=float), pd.Series(dtype=float)
        
        # 找到共同的时间范围
        common_times = silver_returns.index.intersection(other_returns.index)
        
        if len(common_times) < 10:  # 至少需要10个数据点
            logger.warning(f"共同时间点太少: {len(common_times)}")
            return pd.Series(dtype=float), pd.Series(dtype=float)
        
        # 对齐数据
        aligned_silver = silver_returns.loc[common_times]
        aligned_other = other_returns.loc[common_times]
        
        return aligned_silver, aligned_other
    
    def calculate_correlation(self, series1: pd.Series, series2: pd.Series) -> Tuple[float, float]:
        """
        计算相关系数和p值
        
        Args:
            series1: 第一个序列
            series2: 第二个序列
            
        Returns:
            (相关系数, p值)
        """
        if len(series1) < 10 or len(series2) < 10:
            return 0.0, 1.0
        
        try:
            from scipy.stats import pearsonr
            correlation, p_value = pearsonr(series1, series2)
            return correlation, p_value
        except ImportError:
            # 如果没有scipy，使用pandas的相关系数
            correlation = series1.corr(series2)
            return correlation, 0.0  # 无法计算p值
        except Exception as e:
            logger.error(f"计算相关性失败: {e}")
            return 0.0, 1.0
    
    def analyze_single_correlation(self, symbol: str, timeframe: str, silver_data: pd.DataFrame) -> Optional[CorrelationResult]:
        """
        分析单个品种的相关性
        
        Args:
            symbol: 品种代码
            timeframe: 时间框架
            silver_data: 白银数据
            
        Returns:
            相关性结果或None
        """
        logger.info(f"分析 {symbol} {timeframe} 与白银的相关性...")
        
        # 获取目标品种数据 - 获取更多数据以确保有足够的重叠时间
        other_data = self.get_price_data(symbol, timeframe, count=5000)
        if other_data is None:
            return None
        
        # 对齐数据
        silver_returns, other_returns = self.align_data_by_time(silver_data, other_data)
        
        if silver_returns.empty or other_returns.empty:
            logger.warning(f"{symbol} {timeframe} 数据对齐失败")
            return None
        
        # 计算相关性
        correlation, p_value = self.calculate_correlation(silver_returns, other_returns)
        
        # 创建结果
        result = CorrelationResult(
            symbol=symbol,
            timeframe=timeframe,
            correlation=correlation,
            p_value=p_value,
            data_points=len(silver_returns),
            start_time=silver_returns.index.min(),
            end_time=silver_returns.index.max()
        )
        
        logger.info(f"{symbol} {timeframe}: 相关性={correlation:.4f}, p值={p_value:.4f}, 数据点={len(silver_returns)}")
        
        return result
    
    def run_full_analysis(self, force_refresh: bool = False) -> List[CorrelationResult]:
        """
        运行完整的相关性分析
        
        Args:
            force_refresh: 强制刷新所有数据
            
        Returns:
            相关性结果列表
        """
        logger.info("开始白银相关性分析...")
        
        # 首先批量更新所有需要的数据
        if force_refresh:
            logger.info("强制刷新模式，批量更新所有数据...")
            all_symbols = dict(self.target_symbols)
            all_symbols[self.silver_symbol] = [self.silver_timeframe]
            
            update_results = self.data_manager.batch_update_data(all_symbols, count=5000)
            
            # 统计更新结果
            total_updates = sum(len(timeframes) for timeframes in all_symbols.values())
            successful_updates = sum(
                sum(1 for success in symbol_results.values() if success)
                for symbol_results in update_results.values()
            )
            logger.info(f"数据更新完成: {successful_updates}/{total_updates} 成功")
        
        # 获取白银数据 - 检测标的
        logger.info(f"获取白银 {self.silver_symbol} {self.silver_timeframe} 最后{self.silver_bars}根K线 (检测标的)...")
        silver_data = self.get_price_data(self.silver_symbol, self.silver_timeframe, count=self.silver_bars)
        
        if silver_data is None:
            logger.error("无法获取白银数据，分析终止")
            return []
        
        logger.info(f"白银数据时间范围: {silver_data.index.min()} 到 {silver_data.index.max()}")
        
        # 分析所有品种和时间框架
        results = []
        
        for symbol, timeframes in self.target_symbols.items():
            for timeframe in timeframes:
                try:
                    result = self.analyze_single_correlation(symbol, timeframe, silver_data)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"分析 {symbol} {timeframe} 时出错: {e}")
                    continue
        
        # 按相关性绝对值排序
        results.sort(key=lambda x: abs(x.correlation), reverse=True)
        
        logger.info(f"分析完成，共获得 {len(results)} 个有效结果")
        
        return results
    
    def print_results(self, results: List[CorrelationResult], top_n: int = 10):
        """
        打印分析结果
        
        Args:
            results: 相关性结果列表
            top_n: 显示前N个结果
        """
        if not results:
            print("没有有效的相关性分析结果")
            return
        
        print(f"\n{'='*80}")
        print(f"🥈 白银 ({self.silver_symbol}) 相关性分析结果")
        print(f"{'='*80}")
        print(f"检测标的: {self.silver_symbol} {self.silver_timeframe} (最后{self.silver_bars}根K线)")
        print(f"对比品种: 使用大量历史数据确保分析准确性")
        print(f"分析结果: {len(results)} 个有效相关性")
        print(f"{'='*80}")
        
        print(f"\n前 {min(top_n, len(results))} 个最相关的品种:")
        print(f"{'排名':<4} {'品种':<10} {'时间框架':<8} {'相关系数':<10} {'P值':<10} {'数据点':<8} {'关系强度'}")
        print("-" * 80)
        
        for i, result in enumerate(results[:top_n], 1):
            # 判断相关性强度
            abs_corr = abs(result.correlation)
            if abs_corr >= 0.7:
                strength = "强相关"
            elif abs_corr >= 0.5:
                strength = "中等相关"
            elif abs_corr >= 0.3:
                strength = "弱相关"
            else:
                strength = "几乎无关"
            
            # 判断正负相关
            direction = "正相关" if result.correlation > 0 else "负相关"
            strength_desc = f"{direction}-{strength}"
            
            print(f"{i:<4} {result.symbol:<10} {result.timeframe:<8} "
                  f"{result.correlation:<10.4f} {result.p_value:<10.4f} "
                  f"{result.data_points:<8} {strength_desc}")
        
        # 显示最强相关的详细信息
        if results:
            best = results[0]
            print(f"\n最强相关品种详情:")
            print(f"品种: {best.symbol}")
            print(f"时间框架: {best.timeframe}")
            print(f"相关系数: {best.correlation:.4f}")
            print(f"P值: {best.p_value:.4f}")
            print(f"数据点数量: {best.data_points}")
            print(f"数据时间范围: {best.start_time} 到 {best.end_time}")
            
            if abs(best.correlation) >= 0.5:
                print(f"\n💡 建议: {best.symbol} {best.timeframe} 与白银有较强相关性，")
                print(f"   可以作为白银交易的参考指标。")
                if best.correlation > 0:
                    print(f"   正相关关系：{best.symbol}上涨时，白银通常也会上涨")
                else:
                    print(f"   负相关关系：{best.symbol}上涨时，白银通常会下跌")
    
    def save_results_to_json(self, results: List[CorrelationResult], filename: str = "silver_correlation_results.json"):
        """
        保存结果到JSON文件
        
        Args:
            results: 相关性结果列表
            filename: 保存的文件名
        """
        try:
            data = {
                'analysis_time': datetime.now().isoformat(),
                'silver_symbol': self.silver_symbol,
                'silver_timeframe': self.silver_timeframe,
                'silver_bars': self.silver_bars,
                'results': []
            }
            
            for result in results:
                data['results'].append({
                    'symbol': result.symbol,
                    'timeframe': result.timeframe,
                    'correlation': result.correlation,
                    'p_value': result.p_value,
                    'data_points': result.data_points,
                    'start_time': result.start_time.isoformat(),
                    'end_time': result.end_time.isoformat()
                })
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"结果已保存到 {filename}")
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def get_trading_suggestions(self, results: List[CorrelationResult]) -> List[str]:
        """
        基于相关性分析给出交易建议
        
        Args:
            results: 相关性结果列表
            
        Returns:
            交易建议列表
        """
        suggestions = []
        
        if not results:
            return ["无法提供建议：没有有效的相关性数据"]
        
        # 找出强相关的品种
        strong_correlations = [r for r in results if abs(r.correlation) >= 0.5]
        
        if not strong_correlations:
            suggestions.append("⚠️  没有发现与白银强相关的品种，建议独立分析白银走势")
            return suggestions
        
        suggestions.append("📊 基于相关性分析的交易建议:")
        
        for i, result in enumerate(strong_correlations[:3], 1):  # 只显示前3个
            if result.correlation > 0.7:
                strength = "非常强"
            elif result.correlation > 0.5:
                strength = "较强"
            else:
                strength = "中等"
            
            if result.correlation > 0:
                suggestions.append(
                    f"{i}. {result.symbol} ({result.timeframe}) 与白银呈{strength}正相关 ({result.correlation:.3f})"
                )
                suggestions.append(f"   → 当{result.symbol}上涨时，考虑做多白银")
                suggestions.append(f"   → 当{result.symbol}下跌时，考虑做空白银")
            else:
                suggestions.append(
                    f"{i}. {result.symbol} ({result.timeframe}) 与白银呈{strength}负相关 ({result.correlation:.3f})"
                )
                suggestions.append(f"   → 当{result.symbol}上涨时，考虑做空白银")
                suggestions.append(f"   → 当{result.symbol}下跌时，考虑做多白银")
        
        # 添加风险提示
        suggestions.append("\n⚠️  风险提示:")
        suggestions.append("• 相关性会随时间变化，建议定期重新分析")
        suggestions.append("• 相关性不等于因果关系，需结合其他技术分析")
        suggestions.append("• 建议结合基本面分析和风险管理")
        
        return suggestions


def main():
    """主函数"""
    print("白银相关性分析器 (支持本地数据缓存)")
    print("=" * 50)
    
    # 创建分析器
    analyzer = SilverCorrelationAnalyzer()
    
    try:
        # 显示菜单
        while True:
            print(f"\n请选择操作:")
            print("1. 运行分析 (使用缓存数据)")
            print("2. 强制刷新并分析")
            print("3. 查看本地数据状态")
            print("4. 批量更新数据")
            print("5. 退出")
            
            choice = input("\n请输入选择 (1-5): ").strip()
            
            if choice == '1':
                print("\n🔍 开始分析 (使用缓存数据)...")
                results = analyzer.run_full_analysis(force_refresh=False)
                analyzer.print_results(results)
                analyzer.save_results_to_json(results)
                
                # 显示交易建议
                suggestions = analyzer.get_trading_suggestions(results)
                print(f"\n{'='*80}")
                for suggestion in suggestions:
                    print(suggestion)
                
            elif choice == '2':
                print("\n🔄 强制刷新数据并分析...")
                results = analyzer.run_full_analysis(force_refresh=True)
                analyzer.print_results(results)
                analyzer.save_results_to_json(results)
                
                # 显示交易建议
                suggestions = analyzer.get_trading_suggestions(results)
                print(f"\n{'='*80}")
                for suggestion in suggestions:
                    print(suggestion)
                
            elif choice == '3':
                print("\n📊 本地数据状态:")
                analyzer.data_manager.print_data_summary()
                
            elif choice == '4':
                print("\n🔄 批量更新数据...")
                all_symbols = dict(analyzer.target_symbols)
                all_symbols[analyzer.silver_symbol] = [analyzer.silver_timeframe]
                
                results = analyzer.data_manager.batch_update_data(all_symbols, count=200)
                
                print(f"\n📊 更新结果:")
                for symbol, symbol_results in results.items():
                    for timeframe, success in symbol_results.items():
                        status = "✅" if success else "❌"
                        print(f"{status} {symbol} {timeframe}")
                
            elif choice == '5':
                print("👋 再见!")
                break
                
            else:
                print("❌ 无效选择，请重新输入")
        
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        logger.error(f"分析过程中出现错误: {e}")
        print(f"错误: {e}")
    finally:
        # 清理资源
        analyzer.data_manager.disconnect_mt5()


if __name__ == "__main__":
    main()