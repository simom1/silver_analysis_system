"""
增强版白银相关性分析器

支持配置文件、实时监控、历史回测等功能
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
from pathlib import Path
import time
import sys
import os

# 添加父目录到路径，以便导入 metatrader_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入MT5客户端
from metatrader_tools.mt5_client.client import MT5Client, MT5Credentials
from metatrader_tools.mt5_client.periods import timeframe_from_str

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('silver_correlation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnhancedSilverAnalyzer:
    """增强版白银相关性分析器"""
    
    def __init__(self, config_file: str = "correlation_config.json"):
        """
        初始化分析器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.mt5_client = None
        self.last_analysis_time = None
        self.historical_results = []
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"配置文件加载成功: {self.config_file}")
                return config
            else:
                logger.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
                return self.get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "silver_config": {
                "symbol": "XAGUSD",
                "timeframe": "H4",
                "bars_count": 50
            },
            "target_symbols": {
                "XAUUSD": {"name": "黄金", "timeframes": ["H1"]},
                "USOIL": {"name": "WTI原油", "timeframes": ["H1", "H4"]},
                "UKOUSD": {"name": "布伦特原油", "timeframes": ["H1", "H4"]},
                "SPX500": {"name": "标普500", "timeframes": ["H1", "H4"]},
                "US30": {"name": "道琼斯", "timeframes": ["H1", "H4"]},
                "NAS100": {"name": "纳斯达克100", "timeframes": ["H1", "H4"]}
            },
            "analysis_settings": {
                "min_data_points": 50,
                "correlation_thresholds": {"strong": 0.7, "moderate": 0.5, "weak": 0.3},
                "max_bars_to_fetch": 5000
            }
        }
    
    def connect_mt5(self) -> bool:
        """连接MT5"""
        try:
            if self.mt5_client is None:
                self.mt5_client = MT5Client()
                self.mt5_client.initialize()
            return True
        except Exception as e:
            logger.error(f"MT5连接失败: {e}")
            return False
    
    def disconnect_mt5(self):
        """断开MT5连接"""
        if self.mt5_client:
            try:
                self.mt5_client.shutdown()
                self.mt5_client = None
            except Exception as e:
                logger.error(f"断开MT5连接失败: {e}")
    
    def get_market_data(self, symbol: str, timeframe: str, count: int) -> Optional[pd.DataFrame]:
        """获取市场数据"""
        try:
            if not self.connect_mt5():
                return None
            
            tf_const = timeframe_from_str(timeframe)
            data = self.mt5_client.get_rates(symbol, tf_const, count=count)
            
            if data.empty:
                logger.warning(f"未获取到 {symbol} {timeframe} 的数据")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"获取 {symbol} {timeframe} 数据失败: {e}")
            return None
    
    def calculate_correlation_metrics(self, series1: pd.Series, series2: pd.Series) -> Dict[str, float]:
        """计算相关性指标"""
        if len(series1) < 10 or len(series2) < 10:
            return {"correlation": 0.0, "p_value": 1.0, "r_squared": 0.0}
        
        try:
            # 皮尔逊相关系数
            correlation = series1.corr(series2)
            
            # R平方
            r_squared = correlation ** 2
            
            # 尝试计算p值
            p_value = 0.0
            try:
                from scipy.stats import pearsonr
                _, p_value = pearsonr(series1, series2)
            except ImportError:
                pass
            
            return {
                "correlation": correlation,
                "p_value": p_value,
                "r_squared": r_squared
            }
            
        except Exception as e:
            logger.error(f"计算相关性指标失败: {e}")
            return {"correlation": 0.0, "p_value": 1.0, "r_squared": 0.0}
    
    def analyze_correlation(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """分析单个品种的相关性"""
        try:
            # 获取白银数据
            silver_config = self.config["silver_config"]
            silver_data = self.get_market_data(
                silver_config["symbol"],
                silver_config["timeframe"],
                silver_config["bars_count"]
            )
            
            if silver_data is None:
                return None
            
            # 获取目标品种数据
            target_data = self.get_market_data(
                symbol,
                timeframe,
                self.config["analysis_settings"]["max_bars_to_fetch"]
            )
            
            if target_data is None:
                return None
            
            # 计算收益率
            silver_returns = np.log(silver_data['close'] / silver_data['close'].shift(1)).dropna()
            target_returns = np.log(target_data['close'] / target_data['close'].shift(1)).dropna()
            
            # 对齐时间
            common_times = silver_returns.index.intersection(target_returns.index)
            
            if len(common_times) < self.config["analysis_settings"]["min_data_points"]:
                logger.warning(f"{symbol} {timeframe} 共同时间点不足: {len(common_times)}")
                return None
            
            # 获取对齐的数据
            aligned_silver = silver_returns.loc[common_times]
            aligned_target = target_returns.loc[common_times]
            
            # 计算相关性指标
            metrics = self.calculate_correlation_metrics(aligned_silver, aligned_target)
            
            # 构建结果
            result = {
                "symbol": symbol,
                "symbol_name": self.config["target_symbols"].get(symbol, {}).get("name", symbol),
                "timeframe": timeframe,
                "correlation": metrics["correlation"],
                "p_value": metrics["p_value"],
                "r_squared": metrics["r_squared"],
                "data_points": len(common_times),
                "start_time": common_times.min().isoformat(),
                "end_time": common_times.max().isoformat(),
                "analysis_time": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"分析 {symbol} {timeframe} 相关性失败: {e}")
            return None
    
    def run_full_analysis(self) -> List[Dict[str, Any]]:
        """运行完整分析"""
        logger.info("开始白银相关性分析...")
        
        results = []
        
        # 分析所有配置的品种
        for symbol, config in self.config["target_symbols"].items():
            for timeframe in config["timeframes"]:
                try:
                    result = self.analyze_correlation(symbol, timeframe)
                    if result:
                        results.append(result)
                        logger.info(f"{symbol} {timeframe}: 相关性={result['correlation']:.4f}")
                except Exception as e:
                    logger.error(f"分析 {symbol} {timeframe} 时出错: {e}")
                    continue
        
        # 按相关性绝对值排序
        results.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        # 记录分析时间
        self.last_analysis_time = datetime.now()
        
        # 保存到历史记录
        self.historical_results.append({
            "timestamp": self.last_analysis_time.isoformat(),
            "results": results
        })
        
        logger.info(f"分析完成，共获得 {len(results)} 个有效结果")
        
        return results
    
    def print_analysis_results(self, results: List[Dict[str, Any]]):
        """打印分析结果"""
        if not results:
            print("❌ 没有有效的分析结果")
            return
        
        silver_config = self.config["silver_config"]
        thresholds = self.config["analysis_settings"]["correlation_thresholds"]
        
        print(f"\n{'='*80}")
        print(f"🥈 白银相关性分析报告")
        print(f"{'='*80}")
        print(f"检测标的: {silver_config['symbol']} ({silver_config['timeframe']}) - 最后{silver_config['bars_count']}根K线")
        print(f"对比品种: 使用大量历史数据确保分析准确性")
        print(f"分析时间: {self.last_analysis_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"有效结果: {len(results)} 个")
        
        print(f"\n📊 相关性排行榜:")
        print("-" * 80)
        print(f"{'排名':<4} {'品种':<12} {'时间框架':<8} {'相关系数':<10} {'R²':<8} {'数据点':<8} {'强度'}")
        print("-" * 80)
        
        for i, result in enumerate(results[:10], 1):  # 显示前10个
            corr = result['correlation']
            abs_corr = abs(corr)
            
            # 判断强度
            if abs_corr >= thresholds['strong']:
                strength = "🔴强"
            elif abs_corr >= thresholds['moderate']:
                strength = "🟡中"
            elif abs_corr >= thresholds['weak']:
                strength = "🟢弱"
            else:
                strength = "⚪微"
            
            # 方向
            direction = "↗" if corr > 0 else "↘"
            strength_desc = f"{direction}{strength}"
            
            print(f"{i:<4} {result['symbol_name']:<12} {result['timeframe']:<8} "
                  f"{corr:<10.4f} {result['r_squared']:<8.3f} "
                  f"{result['data_points']:<8} {strength_desc}")
        
        # 显示最强相关的详细信息
        if results:
            best = results[0]
            print(f"\n🎯 最强相关品种详情:")
            print(f"   品种: {best['symbol_name']} ({best['symbol']})")
            print(f"   时间框架: {best['timeframe']}")
            print(f"   相关系数: {best['correlation']:.4f}")
            print(f"   R平方: {best['r_squared']:.4f}")
            print(f"   数据点数: {best['data_points']}")
            
            # 交易建议
            self.print_trading_suggestions(results[:3])
    
    def print_trading_suggestions(self, top_results: List[Dict[str, Any]]):
        """打印交易建议"""
        if not top_results:
            return
        
        print(f"\n💡 交易建议:")
        print("-" * 50)
        
        thresholds = self.config["analysis_settings"]["correlation_thresholds"]
        
        for i, result in enumerate(top_results, 1):
            corr = result['correlation']
            abs_corr = abs(corr)
            symbol_name = result['symbol_name']
            
            if abs_corr >= thresholds['moderate']:
                print(f"{i}. {symbol_name} ({result['timeframe']}) - 相关性: {corr:.3f}")
                
                if corr > 0:
                    print(f"   📈 正相关策略:")
                    print(f"   • {symbol_name}上涨 → 考虑做多白银")
                    print(f"   • {symbol_name}下跌 → 考虑做空白银")
                else:
                    print(f"   📉 负相关策略:")
                    print(f"   • {symbol_name}上涨 → 考虑做空白银")
                    print(f"   • {symbol_name}下跌 → 考虑做多白银")
                
                print()
        
        print("⚠️  风险提示:")
        print("• 相关性会随市场环境变化")
        print("• 建议结合技术分析和基本面分析")
        print("• 严格执行风险管理和止损策略")
    
    def save_results(self, results: List[Dict[str, Any]], filename: Optional[str] = None):
        """保存分析结果"""
        if not filename:
            filename = f"silver_correlation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            data = {
                "analysis_info": {
                    "timestamp": datetime.now().isoformat(),
                    "silver_symbol": self.config["silver_config"]["symbol"],
                    "silver_timeframe": self.config["silver_config"]["timeframe"],
                    "silver_bars": self.config["silver_config"]["bars_count"],
                    "total_results": len(results)
                },
                "results": results,
                "config": self.config
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"结果已保存到: {filename}")
            print(f"💾 结果已保存到: {filename}")
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def monitor_mode(self, interval_minutes: int = 60):
        """监控模式 - 定期分析相关性"""
        print(f"🔄 启动监控模式，每 {interval_minutes} 分钟分析一次")
        print("按 Ctrl+C 停止监控")
        
        try:
            while True:
                print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 开始分析...")
                
                results = self.run_full_analysis()
                
                if results:
                    # 只显示前3个最相关的
                    print(f"📊 前3个最相关品种:")
                    for i, result in enumerate(results[:3], 1):
                        print(f"{i}. {result['symbol_name']} ({result['timeframe']}): {result['correlation']:.4f}")
                    
                    # 保存结果
                    self.save_results(results)
                
                print(f"⏳ 等待 {interval_minutes} 分钟后进行下次分析...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n🛑 监控已停止")
        finally:
            self.disconnect_mt5()
    
    def __del__(self):
        """析构函数"""
        self.disconnect_mt5()


def main():
    """主函数"""
    print("🥈 增强版白银相关性分析器")
    print("=" * 50)
    
    analyzer = EnhancedSilverAnalyzer()
    
    try:
        # 显示菜单
        while True:
            print(f"\n请选择操作:")
            print("1. 运行一次完整分析")
            print("2. 启动监控模式")
            print("3. 查看配置信息")
            print("4. 退出")
            
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == '1':
                print("\n🔍 开始分析...")
                results = analyzer.run_full_analysis()
                analyzer.print_analysis_results(results)
                analyzer.save_results(results)
                
            elif choice == '2':
                interval = input("请输入监控间隔(分钟，默认60): ").strip()
                try:
                    interval = int(interval) if interval else 60
                    analyzer.monitor_mode(interval)
                except ValueError:
                    print("❌ 无效的间隔时间")
                
            elif choice == '3':
                print(f"\n📋 当前配置:")
                print(f"白银品种: {analyzer.config['silver_config']['symbol']}")
                print(f"白银时间框架: {analyzer.config['silver_config']['timeframe']}")
                print(f"分析K线数: {analyzer.config['silver_config']['bars_count']}")
                print(f"监测品种数: {len(analyzer.config['target_symbols'])}")
                
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
        analyzer.disconnect_mt5()


if __name__ == "__main__":
    main()