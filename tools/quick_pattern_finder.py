"""
快速K线形态匹配工具

快速找到与白银4H最后50根K线形态最相似的其他品种K线段
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
from metatrader_tools.mt5_client.client import MT5Client
from metatrader_tools.mt5_client.periods import timeframe_from_str

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def normalize_pattern(prices):
    """标准化价格形态为百分比变化"""
    if len(prices) < 2:
        return prices
    
    first_price = prices[0]
    return [(p - first_price) / first_price * 100 for p in prices]


def calculate_pattern_similarity(pattern1, pattern2):
    """计算两个形态的相似性"""
    if len(pattern1) != len(pattern2):
        return 0.0
    
    # 欧几里得距离相似性
    distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(pattern1, pattern2)))
    max_distance = np.sqrt(len(pattern1) * (100 ** 2))  # 假设最大变化100%
    euclidean_sim = 1 - (distance / max_distance)
    
    # 相关性相似性
    correlation = np.corrcoef(pattern1, pattern2)[0, 1]
    if np.isnan(correlation):
        correlation = 0
    correlation_sim = abs(correlation)
    
    # 综合相似性 (加权平均)
    combined_sim = 0.6 * euclidean_sim + 0.4 * correlation_sim
    
    return max(0, combined_sim)


def find_most_similar_patterns():
    """找到最相似的K线形态"""
    
    print("🔍 快速K线形态匹配")
    print("=" * 50)
    print("目标: 找到与白银4H最后50根K线最相似的形态")
    print("=" * 50)
    
    # 配置参数
    silver_symbol = 'XAGUSD'
    silver_timeframe = 'H4'
    silver_bars = 50
    
    # 要搜索的品种 - 根据你的MT5经纪商支持的代码
    search_symbols = [
        # 黄金
        ('XAUUSD', 'H1'),
        ('XAUUSD', 'H4'),
        
        # 原油
        ('XTIUSD', 'H1'),    # WTI原油
        ('XTIUSD', 'H4'),
        ('XBRUSD', 'H1'),    # 布伦特原油
        ('XBRUSD', 'H4'),
        
        # 标普500
        ('US500', 'H1'),
        ('US500', 'H4'),
        
        # 道琼斯
        ('US30', 'H1'),
        ('US30', 'H4'),
        
        # 纳斯达克100
        ('NAS100', 'H1'),
        ('NAS100', 'H4'),
        
        # 外汇 (额外参考)
        ('EURUSD', 'H1'),
        ('EURUSD', 'H4'),
        ('GBPUSD', 'H1'),
        ('GBPUSD', 'H4'),
    ]
    
    try:
        with MT5Client() as client:
            # 获取白银基准形态
            print(f"📊 获取白银基准形态: {silver_symbol} {silver_timeframe}")
            
            silver_tf = timeframe_from_str(silver_timeframe)
            silver_data = client.get_rates(silver_symbol, silver_tf, count=silver_bars)
            
            if silver_data.empty:
                print("❌ 无法获取白银数据")
                return
            
            # 提取白银价格形态
            silver_prices = silver_data['close'].tolist()
            silver_pattern = normalize_pattern(silver_prices)
            
            print(f"✅ 白银基准形态获取成功")
            print(f"   时间范围: {silver_data.index[0]} 到 {silver_data.index[-1]}")
            print(f"   价格范围: {min(silver_prices):.2f} - {max(silver_prices):.2f}")
            
            print(f"\n🔍 开始搜索相似形态...")
            print("-" * 60)
            
            all_matches = []
            
            # 搜索每个品种
            for symbol, timeframe in search_symbols:
                try:
                    print(f"搜索 {symbol} {timeframe}...", end=" ")
                    
                    # 先检查品种是否存在
                    try:
                        client.ensure_symbol(symbol)
                    except Exception as symbol_error:
                        print(f"❌ 品种不存在: {symbol}")
                        continue
                    
                    # 获取目标品种数据
                    tf_const = timeframe_from_str(timeframe)
                    target_data = client.get_rates(symbol, tf_const, count=2000)
                    
                    if target_data.empty:
                        print("❌ 无数据")
                        continue
                    
                    target_prices = target_data['close'].tolist()
                    
                    # 滑动窗口搜索最相似的形态
                    best_similarity = 0
                    best_start_idx = 0
                    
                    for i in range(len(target_prices) - silver_bars + 1):
                        window_prices = target_prices[i:i + silver_bars]
                        window_pattern = normalize_pattern(window_prices)
                        
                        similarity = calculate_pattern_similarity(silver_pattern, window_pattern)
                        
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_start_idx = i
                    
                    if best_similarity > 0.3:  # 只保留相似度较高的结果
                        best_end_idx = best_start_idx + silver_bars - 1
                        start_time = target_data.index[best_start_idx]
                        end_time = target_data.index[best_end_idx]
                        
                        all_matches.append({
                            'symbol': symbol,
                            'timeframe': timeframe,
                            'similarity': best_similarity,
                            'start_time': start_time,
                            'end_time': end_time,
                            'start_idx': best_start_idx,
                            'end_idx': best_end_idx
                        })
                        
                        print(f"✅ 相似度: {best_similarity:.3f}")
                    else:
                        print(f"⚪ 相似度过低: {best_similarity:.3f}")
                        
                except Exception as e:
                    print(f"❌ 错误: {str(e)[:50]}")
                    continue
            
            # 显示结果
            if all_matches:
                # 按相似度排序
                all_matches.sort(key=lambda x: x['similarity'], reverse=True)
                
                print(f"\n📈 找到 {len(all_matches)} 个相似形态 (按相似度排序)")
                print("=" * 80)
                print(f"{'排名':<4} {'品种':<8} {'时间框架':<8} {'相似度':<8} {'最相似时间段'}")
                print("-" * 80)
                
                for i, match in enumerate(all_matches, 1):
                    similarity = match['similarity']
                    
                    # 相似度等级
                    if similarity >= 0.8:
                        level = "🔴"
                    elif similarity >= 0.6:
                        level = "🟡"
                    elif similarity >= 0.4:
                        level = "🟢"
                    else:
                        level = "⚪"
                    
                    time_range = f"{match['start_time'].strftime('%m-%d %H:%M')} ~ {match['end_time'].strftime('%m-%d %H:%M')}"
                    
                    print(f"{i:<4} {match['symbol']:<8} {match['timeframe']:<8} "
                          f"{similarity:<8.3f} {time_range} {level}")
                
                # 显示最佳匹配
                best = all_matches[0]
                print(f"\n🎯 最相似的K线形态:")
                print(f"   品种: {best['symbol']} ({best['timeframe']})")
                print(f"   相似度: {best['similarity']:.4f}")
                print(f"   时间段: {best['start_time']} 到 {best['end_time']}")
                
                if best['similarity'] >= 0.6:
                    print(f"\n💡 形态分析建议:")
                    print(f"   • 该时间段的 {best['symbol']} 走势与当前白银形态高度相似")
                    print(f"   • 可以研究该时间段后续几根K线的走势")
                    print(f"   • 参考该时间段的市场环境和价格变化")
                    print(f"   • 注意: 历史形态不保证未来走势，仅供参考")
                else:
                    print(f"\n⚠️  注意: 最高相似度为 {best['similarity']:.3f}，相对较低")
                    print(f"   建议结合其他分析方法，谨慎参考")
                
            else:
                print("\n❌ 没有找到相似度足够高的K线形态")
                print("   建议:")
                print("   • 降低相似度阈值")
                print("   • 增加搜索的品种和时间框架")
                print("   • 检查数据质量")
                
    except Exception as e:
        logger.error(f"分析失败: {e}")
        print(f"❌ 分析失败: {e}")


def test_mt5_connection():
    """测试MT5连接"""
    print("🔧 测试MT5连接...")
    
    try:
        with MT5Client() as client:
            # 测试获取白银数据
            silver_data = client.get_rates('XAGUSD', timeframe_from_str('H4'), count=10)
            
            if not silver_data.empty:
                print("✅ MT5连接正常")
                print(f"   白银最新价格: {silver_data['close'].iloc[-1]:.2f}")
                return True
            else:
                print("❌ 无法获取白银数据")
                return False
                
    except Exception as e:
        print(f"❌ MT5连接失败: {e}")
        return False


if __name__ == "__main__":
    print("🔍 快速K线形态匹配工具")
    print("=" * 50)
    
    while True:
        print("\n选择操作:")
        print("1. 运行形态匹配分析")
        print("2. 检测可用的品种代码")
        print("3. 退出")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == '1':
            # 测试连接
            if test_mt5_connection():
                print()
                # 运行形态匹配
                find_most_similar_patterns()
            else:
                print("\n请确保:")
                print("1. MT5终端已启动并登录")
                print("2. 账户有白银等品种的访问权限")
                print("3. 网络连接正常")
                
        elif choice == '2':
            print("\n🔍 检测可用品种代码...")
            try:
                import subprocess
                subprocess.run(["python", "check_symbol_codes.py"])
            except Exception as e:
                print(f"❌ 无法启动品种检测工具: {e}")
                print("请手动运行: python check_symbol_codes.py")
                
        elif choice == '3':
            print("👋 再见!")
            break
            
        else:
            print("❌ 无效选择")