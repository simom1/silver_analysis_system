"""
改进的白银相关性分析工具

自动检测可用品种，避免品种代码错误
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import sys
import os

# 添加父目录到路径，以便导入 metatrader_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入MT5客户端
from metatrader_tools.mt5_client.client import MT5Client, MT5Credentials
from metatrader_tools.mt5_client.periods import timeframe_from_str

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_symbol_availability(client, symbol):
    """检查品种是否可用"""
    try:
        # 尝试获取1根K线来测试品种是否存在
        data = client.get_rates(symbol, timeframe_from_str('H1'), count=1)
        return not data.empty
    except:
        return False


def get_available_symbols(client):
    """获取可用的品种列表"""
    # 常见的品种代码变体
    symbol_variants = {
        '黄金': ['XAUUSD', 'GOLD', 'GOLDUSD'],
        'WTI原油': ['USOIL', 'XTIUSD', 'WTI', 'CRUDE', 'CRUDEOIL'],
        '布伦特原油': ['UKOUSD', 'XBRUSD', 'BRENT', 'BRENTOIL'],
        '标普500': ['SPX500', 'SP500', 'US500', 'SPY'],
        '道琼斯': ['US30', 'DJ30', 'DJIA', 'DOW'],
        '纳斯达克': ['NAS100', 'NASDAQ', 'NDX', 'QQQ'],
        '欧元美元': ['EURUSD', 'EUR_USD'],
        '英镑美元': ['GBPUSD', 'GBP_USD'],
        '美元日元': ['USDJPY', 'USD_JPY'],
        '澳元美元': ['AUDUSD', 'AUD_USD'],
        '美元加元': ['USDCAD', 'USD_CAD'],
        '美元瑞郎': ['USDCHF', 'USD_CHF'],
        '纽元美元': ['NZDUSD', 'NZD_USD'],
    }
    
    available_symbols = {}
    
    print("🔍 检测可用品种...")
    for category, variants in symbol_variants.items():
        for symbol in variants:
            if check_symbol_availability(client, symbol):
                available_symbols[category] = symbol
                print(f"✅ {category}: {symbol}")
                break
        else:
            print(f"❌ {category}: 未找到可用代码")
    
    return available_symbols


def improved_correlation_analysis():
    """改进的相关性分析"""
    
    print("🔍 改进的白银相关性分析")
    print("=" * 50)
    
    # 配置参数
    silver_symbol = 'XAGUSD'  # 白银
    silver_timeframe = 'H4'   # 4小时图
    silver_bars = 50          # 最后50根K线
    
    try:
        with MT5Client() as client:
            # 检查白银是否可用
            if not check_symbol_availability(client, silver_symbol):
                print(f"❌ 白银品种 {silver_symbol} 不可用")
                return
            
            # 获取可用品种
            available_symbols = get_available_symbols(client)
            
            if not available_symbols:
                print("❌ 没有找到可用的对比品种")
                return
            
            print(f"\n📊 获取白银数据: {silver_symbol} {silver_timeframe}")
            
            # 获取白银数据
            silver_tf = timeframe_from_str(silver_timeframe)
            silver_data = client.get_rates(silver_symbol, silver_tf, count=silver_bars)
            
            if silver_data.empty:
                print("❌ 无法获取白银数据")
                return
            
            print(f"✅ 白银数据: {len(silver_data)} 根K线")
            print(f"   时间范围: {silver_data.index.min()} 到 {silver_data.index.max()}")
            
            # 计算白银收益率
            silver_returns = np.log(silver_data['close'] / silver_data['close'].shift(1)).dropna()
            
            print(f"\n🔍 开始分析相关性...")
            print("-" * 50)
            
            results = []
            timeframes = ['H1', 'H4']  # 分析1小时和4小时
            
            # 分析每个可用品种
            for category, symbol in available_symbols.items():
                for timeframe in timeframes:
                    try:
                        print(f"分析 {symbol} ({category}) {timeframe}...", end=" ")
                        
                        # 获取数据
                        tf_const = timeframe_from_str(timeframe)
                        data = client.get_rates(symbol, tf_const, count=5000)
                        
                        if data.empty:
                            print("❌ 无数据")
                            continue
                        
                        # 计算收益率
                        returns = np.log(data['close'] / data['close'].shift(1)).dropna()
                        
                        # 对齐时间
                        common_times = silver_returns.index.intersection(returns.index)
                        
                        if len(common_times) < 10:
                            print(f"❌ 共同时间点太少 ({len(common_times)})")
                            continue
                        
                        # 计算相关性
                        aligned_silver = silver_returns.loc[common_times]
                        aligned_other = returns.loc[common_times]
                        
                        correlation = aligned_silver.corr(aligned_other)
                        
                        results.append({
                            'category': category,
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'correlation': correlation,
                            'data_points': len(common_times)
                        })
                        
                        print(f"✅ 相关性: {correlation:.4f} ({len(common_times)}点)")
                        
                    except Exception as e:
                        print(f"❌ 错误: {e}")
                        continue
            
            # 显示结果
            if results:
                print(f"\n📈 相关性分析结果 (检测标的: {silver_symbol} {silver_timeframe})")
                print("=" * 80)
                print(f"{'排名':<4} {'品种类别':<12} {'代码':<10} {'时间框架':<8} {'相关系数':<12} {'数据点':<8} {'关系'}")
                print("-" * 80)
                
                # 按相关性绝对值排序
                results.sort(key=lambda x: abs(x['correlation']), reverse=True)
                
                for i, result in enumerate(results, 1):
                    corr = result['correlation']
                    abs_corr = abs(corr)
                    
                    # 判断相关性强度和方向
                    if abs_corr >= 0.7:
                        strength = "强"
                    elif abs_corr >= 0.5:
                        strength = "中"
                    elif abs_corr >= 0.3:
                        strength = "弱"
                    else:
                        strength = "微"
                    
                    direction = "正" if corr > 0 else "负"
                    relationship = f"{direction}相关-{strength}"
                    
                    print(f"{i:<4} {result['category']:<12} {result['symbol']:<10} {result['timeframe']:<8} "
                          f"{corr:<12.4f} {result['data_points']:<8} {relationship}")
                
                # 显示最佳相关品种
                best = results[0]
                print(f"\n🎯 最强相关品种: {best['symbol']} ({best['category']}) - {best['timeframe']}")
                print(f"   相关系数: {best['correlation']:.4f}")
                print(f"   数据点数: {best['data_points']}")
                
                if abs(best['correlation']) >= 0.5:
                    print(f"   💡 建议: 可作为白银交易的重要参考指标")
                    if best['correlation'] > 0:
                        print(f"   📈 正相关: {best['category']}上涨 → 白银可能上涨")
                        print(f"   📉 正相关: {best['category']}下跌 → 白银可能下跌")
                    else:
                        print(f"   📈 负相关: {best['category']}上涨 → 白银可能下跌")
                        print(f"   📉 负相关: {best['category']}下跌 → 白银可能上涨")
                else:
                    print(f"   ⚠️  相关性较弱，建议结合其他分析方法")
                
                # 显示前3名的详细建议
                print(f"\n💡 交易建议 (基于前3名相关品种):")
                print("-" * 50)
                for i, result in enumerate(results[:3], 1):
                    corr = result['correlation']
                    category = result['category']
                    symbol = result['symbol']
                    tf = result['timeframe']
                    
                    if abs(corr) >= 0.3:
                        direction = "同向" if corr > 0 else "反向"
                        print(f"{i}. 关注 {category} ({symbol}) {tf} 走势")
                        print(f"   相关性: {corr:.4f} - {direction}关系")
                        if corr > 0:
                            print(f"   策略: {category}突破上涨时考虑做多白银")
                        else:
                            print(f"   策略: {category}突破上涨时考虑做空白银")
                        print()
                
            else:
                print("❌ 没有获得有效的相关性结果")
                
    except Exception as e:
        logger.error(f"分析失败: {e}")
        print(f"❌ 分析失败: {e}")


def test_mt5_connection():
    """测试MT5连接"""
    print("🔧 测试MT5连接...")
    
    try:
        with MT5Client() as client:
            # 测试获取账户信息
            account_info = client.get_account_info()
            print(f"✅ MT5连接成功")
            print(f"   账户: {account_info.get('login', 'N/A')}")
            print(f"   服务器: {account_info.get('server', 'N/A')}")
            print(f"   余额: {account_info.get('balance', 'N/A')}")
            
            # 测试获取白银价格
            try:
                tick = client.get_tick('XAGUSD')
                print(f"   白银价格: {tick['bid']:.4f} / {tick['ask']:.4f}")
            except:
                print("   ⚠️  无法获取白银价格")
            
            return True
            
    except Exception as e:
        print(f"❌ MT5连接失败: {e}")
        return False


if __name__ == "__main__":
    print("改进的白银相关性分析工具")
    print("=" * 50)
    
    # 先测试连接
    if test_mt5_connection():
        print()
        # 运行分析
        improved_correlation_analysis()
    else:
        print("\n请确保:")
        print("1. MT5终端已启动并登录")
        print("2. Python环境已安装MetaTrader5包")
        print("3. 账户有相关品种的访问权限")