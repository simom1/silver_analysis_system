"""
白银相关性分析 - 数据管理器

负责从MT5拉取数据并保存到本地，支持数据缓存和增量更新
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json
import os
from pathlib import Path
import pickle
import sys

# 添加父目录到路径，以便导入 metatrader_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入MT5客户端
from metatrader_tools.mt5_client.client import MT5Client, MT5Credentials
from metatrader_tools.mt5_client.periods import timeframe_from_str

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataManager:
    """数据管理器 - 负责数据的获取、保存和加载"""
    
    def __init__(self, data_dir: str = "market_data"):
        """
        初始化数据管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (self.data_dir / "raw_data").mkdir(exist_ok=True)
        (self.data_dir / "processed_data").mkdir(exist_ok=True)
        (self.data_dir / "cache").mkdir(exist_ok=True)
        
        self.mt5_client = None
        
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
    
    def get_data_filename(self, symbol: str, timeframe: str) -> str:
        """生成数据文件名"""
        return f"{symbol}_{timeframe}.csv"
    
    def get_cache_filename(self, symbol: str, timeframe: str) -> str:
        """生成缓存文件名"""
        return f"{symbol}_{timeframe}_cache.pkl"
    
    def fetch_from_mt5(self, symbol: str, timeframe: str, count: int = 5000) -> Optional[pd.DataFrame]:
        """从MT5获取数据"""
        try:
            if not self.connect_mt5():
                return None
            
            logger.info(f"从MT5获取 {symbol} {timeframe} 数据，数量: {count}")
            
            tf_const = timeframe_from_str(timeframe)
            data = self.mt5_client.get_rates(symbol, tf_const, count=count)
            
            if data.empty:
                logger.warning(f"未获取到 {symbol} {timeframe} 的数据")
                return None
            
            logger.info(f"成功获取 {symbol} {timeframe} 数据: {len(data)} 根K线")
            logger.info(f"时间范围: {data.index.min()} 到 {data.index.max()}")
            
            return data
            
        except Exception as e:
            logger.error(f"从MT5获取 {symbol} {timeframe} 数据失败: {e}")
            return None
    
    def save_data_to_csv(self, data: pd.DataFrame, symbol: str, timeframe: str) -> bool:
        """保存数据到CSV文件"""
        try:
            filename = self.data_dir / "raw_data" / self.get_data_filename(symbol, timeframe)
            
            # 添加元数据
            data_with_meta = data.copy()
            data_with_meta.attrs = {
                'symbol': symbol,
                'timeframe': timeframe,
                'last_update': datetime.now().isoformat(),
                'total_bars': len(data)
            }
            
            # 保存到CSV
            data_with_meta.to_csv(filename)
            
            # 保存元数据到JSON
            meta_filename = filename.with_suffix('.json')
            with open(meta_filename, 'w', encoding='utf-8') as f:
                json.dump(data_with_meta.attrs, f, indent=2, ensure_ascii=False)
            
            logger.info(f"数据已保存到: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return False
    
    def load_data_from_csv(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """从CSV文件加载数据"""
        try:
            filename = self.data_dir / "raw_data" / self.get_data_filename(symbol, timeframe)
            
            if not filename.exists():
                logger.info(f"数据文件不存在: {filename}")
                return None
            
            # 加载数据
            data = pd.read_csv(filename, index_col=0, parse_dates=True)
            
            # 加载元数据
            meta_filename = filename.with_suffix('.json')
            if meta_filename.exists():
                with open(meta_filename, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    data.attrs = metadata
                    logger.info(f"加载数据: {symbol} {timeframe}, 最后更新: {metadata.get('last_update', 'N/A')}")
            
            return data
            
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            return None
    
    def is_data_fresh(self, symbol: str, timeframe: str, max_age_hours: int = 1) -> bool:
        """检查数据是否新鲜"""
        try:
            filename = self.data_dir / "raw_data" / self.get_data_filename(symbol, timeframe)
            meta_filename = filename.with_suffix('.json')
            
            if not meta_filename.exists():
                return False
            
            with open(meta_filename, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            last_update_str = metadata.get('last_update')
            if not last_update_str:
                return False
            
            last_update = datetime.fromisoformat(last_update_str)
            age_hours = (datetime.now() - last_update).total_seconds() / 3600
            
            is_fresh = age_hours < max_age_hours
            logger.info(f"{symbol} {timeframe} 数据年龄: {age_hours:.1f}小时, 是否新鲜: {is_fresh}")
            
            return is_fresh
            
        except Exception as e:
            logger.error(f"检查数据新鲜度失败: {e}")
            return False
    
    def get_data(self, symbol: str, timeframe: str, count: int = 5000, 
                 force_refresh: bool = False, max_age_hours: int = 1) -> Optional[pd.DataFrame]:
        """
        获取数据 - 优先从本地加载，必要时从MT5更新
        
        Args:
            symbol: 品种代码
            timeframe: 时间框架
            count: 获取的K线数量（最小需要）
            force_refresh: 强制刷新数据
            max_age_hours: 数据最大年龄（小时）
            
        Returns:
            数据DataFrame或None
        """
        # 如果强制刷新或数据不新鲜，从MT5获取
        if force_refresh or not self.is_data_fresh(symbol, timeframe, max_age_hours):
            logger.info(f"需要更新 {symbol} {timeframe} 数据")
            
            # 从MT5获取数据
            data = self.fetch_from_mt5(symbol, timeframe, count)
            
            if data is not None:
                # 保存到本地
                self.save_data_to_csv(data, symbol, timeframe)
                return data
            else:
                # 如果MT5获取失败，尝试加载本地数据
                logger.warning(f"MT5获取失败，尝试加载本地数据")
                return self.load_data_from_csv(symbol, timeframe)
        else:
            # 数据新鲜，直接从本地加载
            logger.info(f"从本地加载 {symbol} {timeframe} 数据")
            data = self.load_data_from_csv(symbol, timeframe)
            
            # 检查数据量是否足够
            if data is not None and len(data) < count:
                logger.warning(f"{symbol} {timeframe} 本地数据只有 {len(data)} 根，少于需要的 {count} 根")
                logger.info(f"尝试从MT5获取更多数据...")
                
                # 尝试从MT5获取更多数据
                new_data = self.fetch_from_mt5(symbol, timeframe, count)
                if new_data is not None and len(new_data) > len(data):
                    logger.info(f"成功获取 {len(new_data)} 根K线")
                    self.save_data_to_csv(new_data, symbol, timeframe)
                    return new_data
                else:
                    logger.warning(f"无法获取更多数据，使用现有的 {len(data)} 根K线")
            
            return data
    
    def batch_update_data(self, symbols_config: Dict[str, List[str]], count: int = 5000) -> Dict[str, Dict[str, bool]]:
        """
        批量更新数据
        
        Args:
            symbols_config: 品种配置 {symbol: [timeframes]}
            count: 获取的K线数量
            
        Returns:
            更新结果 {symbol: {timeframe: success}}
        """
        results = {}
        
        logger.info(f"开始批量更新数据...")
        
        for symbol, timeframes in symbols_config.items():
            results[symbol] = {}
            
            for timeframe in timeframes:
                try:
                    logger.info(f"更新 {symbol} {timeframe}...")
                    
                    data = self.fetch_from_mt5(symbol, timeframe, count)
                    
                    if data is not None:
                        success = self.save_data_to_csv(data, symbol, timeframe)
                        results[symbol][timeframe] = success
                    else:
                        results[symbol][timeframe] = False
                        
                except Exception as e:
                    logger.error(f"更新 {symbol} {timeframe} 失败: {e}")
                    results[symbol][timeframe] = False
        
        # 统计结果
        total_tasks = sum(len(timeframes) for timeframes in symbols_config.values())
        successful_tasks = sum(
            sum(1 for success in symbol_results.values() if success)
            for symbol_results in results.values()
        )
        
        logger.info(f"批量更新完成: {successful_tasks}/{total_tasks} 成功")
        
        return results
    
    def get_data_summary(self) -> Dict[str, any]:
        """获取数据摘要"""
        summary = {
            'total_files': 0,
            'symbols': set(),
            'timeframes': set(),
            'data_details': []
        }
        
        raw_data_dir = self.data_dir / "raw_data"
        
        for csv_file in raw_data_dir.glob("*.csv"):
            try:
                # 解析文件名
                name_parts = csv_file.stem.split('_')
                if len(name_parts) >= 2:
                    symbol = name_parts[0]
                    timeframe = '_'.join(name_parts[1:])
                    
                    summary['symbols'].add(symbol)
                    summary['timeframes'].add(timeframe)
                    summary['total_files'] += 1
                    
                    # 获取文件信息
                    meta_file = csv_file.with_suffix('.json')
                    if meta_file.exists():
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        summary['data_details'].append({
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'last_update': metadata.get('last_update', 'N/A'),
                            'total_bars': metadata.get('total_bars', 0),
                            'file_size': csv_file.stat().st_size
                        })
                        
            except Exception as e:
                logger.error(f"处理文件 {csv_file} 时出错: {e}")
        
        summary['symbols'] = sorted(list(summary['symbols']))
        summary['timeframes'] = sorted(list(summary['timeframes']))
        
        return summary
    
    def print_data_summary(self):
        """打印数据摘要"""
        summary = self.get_data_summary()
        
        print(f"\n{'='*60}")
        print(f"📊 本地数据摘要")
        print(f"{'='*60}")
        print(f"数据文件总数: {summary['total_files']}")
        print(f"品种数量: {len(summary['symbols'])}")
        print(f"时间框架数量: {len(summary['timeframes'])}")
        
        print(f"\n📈 品种列表: {', '.join(summary['symbols'])}")
        print(f"⏰ 时间框架: {', '.join(summary['timeframes'])}")
        
        print(f"\n📋 详细信息:")
        print("-" * 80)
        print(f"{'品种':<10} {'时间框架':<8} {'最后更新':<20} {'K线数':<8} {'文件大小'}")
        print("-" * 80)
        
        for detail in summary['data_details']:
            last_update = detail['last_update']
            if last_update != 'N/A':
                try:
                    update_time = datetime.fromisoformat(last_update)
                    last_update = update_time.strftime('%m-%d %H:%M')
                except:
                    pass
            
            file_size = detail['file_size']
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024*1024):.1f}MB"
            elif file_size > 1024:
                size_str = f"{file_size / 1024:.1f}KB"
            else:
                size_str = f"{file_size}B"
            
            print(f"{detail['symbol']:<10} {detail['timeframe']:<8} "
                  f"{last_update:<20} {detail['total_bars']:<8} {size_str}")
    
    def clean_old_data(self, days_old: int = 7):
        """清理旧数据"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_old)
            cleaned_count = 0
            
            raw_data_dir = self.data_dir / "raw_data"
            
            for csv_file in raw_data_dir.glob("*.csv"):
                meta_file = csv_file.with_suffix('.json')
                
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        last_update_str = metadata.get('last_update')
                        if last_update_str:
                            last_update = datetime.fromisoformat(last_update_str)
                            
                            if last_update < cutoff_time:
                                csv_file.unlink()
                                meta_file.unlink()
                                cleaned_count += 1
                                logger.info(f"删除旧数据: {csv_file.name}")
                                
                    except Exception as e:
                        logger.error(f"处理文件 {csv_file} 时出错: {e}")
            
            logger.info(f"清理完成，删除了 {cleaned_count} 个旧数据文件")
            
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
    
    def __del__(self):
        """析构函数"""
        self.disconnect_mt5()


def main():
    """主函数 - 数据管理工具"""
    print("📊 白银相关性分析 - 数据管理器")
    print("=" * 50)
    
    # 创建数据管理器
    data_manager = DataManager()
    
    # 配置要获取的数据 - 根据MT5经纪商支持的代码
    symbols_config = {
        'XAGUSD': ['H4'],  # 白银4小时 - 检测标的
        'XAUUSD': ['H1', 'H4'],  # 黄金
        'XTIUSD': ['H1', 'H4'],  # WTI原油
        'XBRUSD': ['H1', 'H4'],  # 布伦特原油
        'US500': ['H1', 'H4'],   # 标普500
        'US30': ['H1', 'H4'],    # 道琼斯
        'NAS100': ['H1', 'H4'],  # 纳斯达克100
        'EURUSD': ['H1', 'H4'],  # 欧元美元
        'GBPUSD': ['H1', 'H4'],  # 英镑美元
    }
    
    try:
        while True:
            print(f"\n请选择操作:")
            print("1. 批量更新所有数据")
            print("2. 更新单个品种数据")
            print("3. 查看数据摘要")
            print("4. 清理旧数据")
            print("5. 测试数据获取")
            print("6. 退出")
            
            choice = input("\n请输入选择 (1-6): ").strip()
            
            if choice == '1':
                print("\n🔄 开始批量更新数据...")
                results = data_manager.batch_update_data(symbols_config, count=5000)
                
                print(f"\n📊 更新结果:")
                for symbol, symbol_results in results.items():
                    for timeframe, success in symbol_results.items():
                        status = "✅" if success else "❌"
                        print(f"{status} {symbol} {timeframe}")
                
            elif choice == '2':
                symbol = input("请输入品种代码 (如 XAGUSD): ").strip().upper()
                timeframe = input("请输入时间框架 (如 H1): ").strip().upper()
                
                if symbol and timeframe:
                    print(f"\n🔄 更新 {symbol} {timeframe} 数据...")
                    data = data_manager.get_data(symbol, timeframe, force_refresh=True)
                    
                    if data is not None:
                        print(f"✅ 更新成功: {len(data)} 根K线")
                        print(f"时间范围: {data.index.min()} 到 {data.index.max()}")
                    else:
                        print("❌ 更新失败")
                
            elif choice == '3':
                data_manager.print_data_summary()
                
            elif choice == '4':
                days = input("请输入清理天数 (默认7天): ").strip()
                try:
                    days = int(days) if days else 7
                    print(f"\n🧹 清理 {days} 天前的数据...")
                    data_manager.clean_old_data(days)
                    print("✅ 清理完成")
                except ValueError:
                    print("❌ 无效的天数")
                
            elif choice == '5':
                print("\n🔧 测试数据获取...")
                test_data = data_manager.get_data('XAGUSD', 'H4', count=50)
                
                if test_data is not None:
                    print(f"✅ 测试成功")
                    print(f"数据量: {len(test_data)} 根K线")
                    print(f"最新价格: {test_data['close'].iloc[-1]:.4f}")
                    print(f"时间范围: {test_data.index.min()} 到 {test_data.index.max()}")
                else:
                    print("❌ 测试失败")
                
            elif choice == '6':
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
        data_manager.disconnect_mt5()


if __name__ == "__main__":
    main()