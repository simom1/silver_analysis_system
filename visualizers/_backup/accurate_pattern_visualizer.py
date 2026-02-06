"""
精确K线形态可视化工具

基于真实的形态匹配结果生成准确的对比图
使用具体的时间段数据，而不是简单的最新数据
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Optional
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入MT5客户端
from metatrader_tools.mt5_client.client import MT5Client
from metatrader_tools.mt5_client.periods import timeframe_from_str

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def get_silver_reference_pattern():
    """获取白银基准形态（最新50根4H K线）"""
    try:
        with MT5Client() as client:
            silver_data = client.get_rates('XAGUSD', timeframe_from_str('H4'), count=50)
            if silver_data.empty:
                return None
            return silver_data
    except Exception as e:
        print(f"❌ 获取白银数据失败: {e}")
        return None


def get_historical_pattern(symbol, timeframe, start_time, end_time):
    """获取指定时间段的历史形态数据"""
    try:
        with MT5Client() as client:
            # 转换时间字符串为datetime对象
            if isinstance(start_time, str):
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                start_dt = start_time
                
            if isinstance(end_time, str):
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            else:
                end_dt = end_time
            
            # 获取该时间段的数据
            tf = timeframe_from_str(timeframe)
            
            # 使用from_time_utc和to_time_utc参数获取指定时间段的数据
            data = client.get_rates(
                symbol, 
                tf, 
                from_time_utc=start_dt, 
                to_time_utc=end_dt
            )
            
            if data.empty:
                print(f"⚠️ 指定时间段无数据，尝试获取附近时间段...")
                # 如果指定时间段没有数据，尝试获取更大范围
                extended_start = start_dt - timedelta(days=7)
                extended_end = end_dt + timedelta(days=7)
                data = client.get_rates(
                    symbol, 
                    tf, 
                    from_time_utc=extended_start, 
                    to_time_utc=extended_end
                )
                
                if data.empty:
                    return None
                
                # 如果还是没有足够数据，使用最新的50根K线
                if len(data) < 30:
                    print(f"⚠️ 历史数据不足，使用最新数据代替...")
                    data = client.get_rates(symbol, tf, count=50)
            
            # 如果数据太多，取中间部分或调整到50根左右
            if len(data) > 80:
                # 取中间50根
                start_idx = max(0, (len(data) - 50) // 2)
                data = data.iloc[start_idx:start_idx + 50]
            elif len(data) > 50:
                # 取前50根
                data = data.head(50)
            
            return data
            
    except Exception as e:
        print(f"❌ 获取 {symbol} {timeframe} 历史数据失败: {e}")
        return None


def normalize_for_comparison(prices1, prices2):
    """标准化两个价格序列用于形态对比"""
    if len(prices1) == 0 or len(prices2) == 0:
        return [], []
    
    # 转换为相对变化百分比
    norm1 = [(p - prices1[0]) / prices1[0] * 100 for p in prices1]
    norm2 = [(p - prices2[0]) / prices2[0] * 100 for p in prices2]
    
    return norm1, norm2


def calculate_pattern_similarity(prices1, prices2):
    """计算两个价格序列的形态相似度"""
    if len(prices1) != len(prices2):
        # 调整长度
        min_len = min(len(prices1), len(prices2))
        prices1 = prices1[:min_len]
        prices2 = prices2[:min_len]
    
    if len(prices1) < 10:
        return 0.0
    
    # 标准化
    norm1, norm2 = normalize_for_comparison(prices1, prices2)
    
    # 计算多种相似度指标
    try:
        # 1. 皮尔逊相关系数
        corr = np.corrcoef(norm1, norm2)[0, 1]
        if np.isnan(corr):
            corr = 0
        
        # 2. 欧几里得距离（转换为相似度）
        euclidean_dist = np.sqrt(np.sum((np.array(norm1) - np.array(norm2)) ** 2))
        max_possible_dist = np.sqrt(2 * len(norm1) * (max(max(norm1), max(norm2)) ** 2))
        euclidean_sim = 1 - (euclidean_dist / max_possible_dist) if max_possible_dist > 0 else 0
        
        # 3. 余弦相似度
        dot_product = np.dot(norm1, norm2)
        norm_a = np.linalg.norm(norm1)
        norm_b = np.linalg.norm(norm2)
        cosine_sim = dot_product / (norm_a * norm_b) if (norm_a * norm_b) > 0 else 0
        
        # 综合相似度（加权平均）
        similarity = (abs(corr) * 0.4 + euclidean_sim * 0.3 + cosine_sim * 0.3)
        
        return max(0, min(1, similarity))
        
    except Exception as e:
        print(f"计算相似度时出错: {e}")
        return 0.0


def create_accurate_comparison_chart():
    """创建基于真实匹配结果的精确对比图"""
    
    print("📊 生成精确K线形态对比图")
    print("=" * 50)
    
    # 获取白银基准数据
    print("📊 获取白银基准形态...")
    silver_data = get_silver_reference_pattern()
    if silver_data is None:
        print("❌ 无法获取白银基准数据")
        return None
    
    silver_prices = silver_data['close'].tolist()
    print(f"✅ 白银基准数据: {len(silver_prices)} 根K线")
    print(f"   时间范围: {silver_data.index[0]} 到 {silver_data.index[-1]}")
    print(f"   价格范围: {min(silver_prices):.2f} - {max(silver_prices):.2f}")
    
    # 基于形态匹配结果的真实时间段
    top_matches = [
        {
            'symbol': 'XBRUSD', 
            'timeframe': 'H4', 
            'similarity': 0.931,
            'start_time': '2025-06-17T12:00:00+00:00',
            'end_time': '2025-06-27T16:00:00+00:00',
            'name': '布伦特原油4H'
        },
        {
            'symbol': 'XTIUSD', 
            'timeframe': 'H4', 
            'similarity': 0.931,
            'start_time': '2025-06-17T12:00:00+00:00',
            'end_time': '2025-06-27T16:00:00+00:00',
            'name': 'WTI原油4H'
        },
        {
            'symbol': 'XBRUSD', 
            'timeframe': 'H1', 
            'similarity': 0.905,
            'start_time': '2025-01-29T19:00:00+00:00',
            'end_time': '2025-02-03T05:00:00+00:00',
            'name': '布伦特原油1H'
        },
        {
            'symbol': 'US500', 
            'timeframe': 'H4', 
            'similarity': 0.903,
            'start_time': '2025-03-28T12:00:00+00:00',
            'end_time': '2025-04-09T16:00:00+00:00',
            'name': '标普500 4H'
        },
        {
            'symbol': 'XAUUSD', 
            'timeframe': 'H1', 
            'similarity': 0.897,
            'start_time': '2025-10-20T11:00:00+00:00',
            'end_time': '2025-10-22T14:00:00+00:00',
            'name': '黄金1H'
        }
    ]
    
    # 创建图表
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('白银4H形态 vs 历史最相似形态精确对比\n(基于真实时间段的形态匹配)', 
                fontsize=16, fontweight='bold')
    
    # 第一个图：白银基准
    ax = axes[0, 0]
    silver_norm = [(p - silver_prices[0]) / silver_prices[0] * 100 for p in silver_prices]
    ax.plot(range(len(silver_norm)), silver_norm, 'b-', linewidth=3, 
           label='白银 XAGUSD H4', marker='o', markersize=4)
    ax.set_title('白银基准形态\n(最新50根4H K线)', fontsize=12, fontweight='bold')
    ax.set_xlabel('K线序号')
    ax.set_ylabel('相对变化 (%)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 添加价格和时间信息
    info_text = f"价格: {min(silver_prices):.2f} - {max(silver_prices):.2f}\n"
    info_text += f"时间: {silver_data.index[0].strftime('%m-%d %H:%M')}\n"
    info_text += f"至: {silver_data.index[-1].strftime('%m-%d %H:%M')}"
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # 获取并绘制匹配的历史形态
    colors = ['red', 'green', 'orange', 'purple', 'brown']
    successful_matches = 0
    
    for i, match in enumerate(top_matches):
        if successful_matches >= 5:  # 最多显示5个
            break
            
        row = (successful_matches + 1) // 3
        col = (successful_matches + 1) % 3
        
        print(f"\n🔍 获取 {match['name']} 历史形态数据...")
        print(f"   时间段: {match['start_time']} 到 {match['end_time']}")
        
        # 获取历史时间段的数据
        historical_data = get_historical_pattern(
            match['symbol'], 
            match['timeframe'], 
            match['start_time'], 
            match['end_time']
        )
        
        if historical_data is None or len(historical_data) < 10:
            print(f"❌ {match['name']} 历史数据获取失败")
            continue
        
        historical_prices = historical_data['close'].tolist()
        
        # 调整长度匹配
        if len(historical_prices) > len(silver_prices):
            historical_prices = historical_prices[:len(silver_prices)]
        elif len(historical_prices) < len(silver_prices):
            # 如果历史数据不够，尝试获取更多
            print(f"⚠️ {match['name']} 数据点不足，使用现有 {len(historical_prices)} 个点")
        
        # 重新计算实际相似度
        actual_similarity = calculate_pattern_similarity(silver_prices, historical_prices)
        
        # 标准化用于显示
        historical_norm = [(p - historical_prices[0]) / historical_prices[0] * 100 for p in historical_prices]
        
        # 绘制对比图
        ax = axes[row, col]
        
        # 白银（半透明）
        ax.plot(range(len(silver_norm)), silver_norm, 'b-', linewidth=2, 
               alpha=0.6, label='白银', marker='o', markersize=3)
        
        # 历史匹配形态（突出显示）
        ax.plot(range(len(historical_norm)), historical_norm, color=colors[i], 
               linewidth=3, label=match['name'], marker='s', markersize=3)
        
        ax.set_title(f"{match['name']}\n预期相似度: {match['similarity']:.3f} | 实际: {actual_similarity:.3f}", 
                   fontsize=11, fontweight='bold')
        ax.set_xlabel('K线序号')
        ax.set_ylabel('相对变化 (%)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 添加详细信息
        detail_text = f"历史时间: {historical_data.index[0].strftime('%Y-%m-%d')}\n"
        detail_text += f"数据点: {len(historical_prices)}\n"
        detail_text += f"价格范围: {min(historical_prices):.2f}-{max(historical_prices):.2f}"
        
        ax.text(0.02, 0.02, detail_text, transform=ax.transAxes, fontsize=8,
               verticalalignment='bottom', 
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        print(f"✅ {match['name']} - 预期相似度: {match['similarity']:.3f}, 实际: {actual_similarity:.3f}")
        successful_matches += 1
    
    # 隐藏多余的子图
    for i in range(successful_matches + 1, 6):
        row = i // 3
        col = i % 3
        axes[row, col].axis('off')
    
    plt.tight_layout()
    
    # 确保 outputs 目录存在
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存图表
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(output_dir, f"accurate_pattern_comparison_{timestamp}.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    print(f"\n📊 精确形态对比图已生成:")
    print(f"文件名: {filename}")
    print(f"成功匹配: {successful_matches} 个形态")
    print(f"分辨率: 300 DPI")
    
    # 显示图表
    plt.show()
    
    return filename


def create_single_accurate_comparison(symbol, timeframe, start_time, end_time, expected_similarity):
    """创建单个品种的精确历史对比"""
    
    print(f"📊 生成 {symbol} {timeframe} 精确历史对比图")
    print(f"时间段: {start_time} 到 {end_time}")
    print("=" * 50)
    
    # 获取白银基准数据
    silver_data = get_silver_reference_pattern()
    if silver_data is None:
        return None
    
    # 获取历史匹配数据
    historical_data = get_historical_pattern(symbol, timeframe, start_time, end_time)
    if historical_data is None:
        return None
    
    silver_prices = silver_data['close'].tolist()
    historical_prices = historical_data['close'].tolist()
    
    # 调整长度
    min_len = min(len(silver_prices), len(historical_prices))
    silver_prices = silver_prices[:min_len]
    historical_prices = historical_prices[:min_len]
    
    # 计算实际相似度
    actual_similarity = calculate_pattern_similarity(silver_prices, historical_prices)
    
    # 创建详细对比图
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'白银 vs {symbol} 精确历史形态对比\n预期相似度: {expected_similarity:.3f} | 实际相似度: {actual_similarity:.3f}', 
                fontsize=16, fontweight='bold')
    
    # 标准化
    silver_norm, historical_norm = normalize_for_comparison(silver_prices, historical_prices)
    
    # 1. 标准化形态对比
    axes[0, 0].plot(silver_norm, 'b-', linewidth=3, label='白银 (当前)', marker='o', markersize=4)
    axes[0, 0].plot(historical_norm, 'r--', linewidth=3, label=f'{symbol} (历史)', marker='s', markersize=4)
    axes[0, 0].set_title(f'标准化形态对比 (相似度: {actual_similarity:.3f})')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].set_xlabel('K线序号')
    axes[0, 0].set_ylabel('相对变化 (%)')
    
    # 2. 原始价格对比
    axes[0, 1].plot(silver_prices, 'b-', linewidth=2, label='白银价格')
    ax2 = axes[0, 1].twinx()
    ax2.plot(historical_prices, 'r-', linewidth=2, label=f'{symbol}价格')
    axes[0, 1].set_title('原始价格对比')
    axes[0, 1].legend(loc='upper left')
    ax2.legend(loc='upper right')
    axes[0, 1].set_xlabel('K线序号')
    
    # 3. 差异分析
    diff = np.array(silver_norm) - np.array(historical_norm)
    axes[1, 0].bar(range(len(diff)), diff, alpha=0.7, color='purple')
    axes[1, 0].set_title('形态差异分析')
    axes[1, 0].set_xlabel('K线序号')
    axes[1, 0].set_ylabel('差异 (%)')
    axes[1, 0].axhline(y=0, color='black', linestyle='-', alpha=0.3)
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 统计信息
    axes[1, 1].axis('off')
    
    stats_text = f"精确形态对比分析\n{'='*30}\n\n"
    stats_text += f"白银基准信息:\n"
    stats_text += f"  时间: {silver_data.index[0].strftime('%Y-%m-%d %H:%M')} 到\n"
    stats_text += f"        {silver_data.index[-1].strftime('%Y-%m-%d %H:%M')}\n"
    stats_text += f"  价格: {min(silver_prices):.2f} - {max(silver_prices):.2f}\n"
    stats_text += f"  总变化: {silver_norm[-1]:.2f}%\n\n"
    
    stats_text += f"历史匹配信息:\n"
    stats_text += f"  品种: {symbol} {timeframe}\n"
    stats_text += f"  时间: {historical_data.index[0].strftime('%Y-%m-%d %H:%M')} 到\n"
    stats_text += f"        {historical_data.index[-1].strftime('%Y-%m-%d %H:%M')}\n"
    stats_text += f"  价格: {min(historical_prices):.2f} - {max(historical_prices):.2f}\n"
    stats_text += f"  总变化: {historical_norm[-1]:.2f}%\n\n"
    
    stats_text += f"相似度分析:\n"
    stats_text += f"  预期相似度: {expected_similarity:.3f}\n"
    stats_text += f"  实际相似度: {actual_similarity:.3f}\n"
    stats_text += f"  差异: {abs(expected_similarity - actual_similarity):.3f}\n"
    stats_text += f"  数据点数: {len(silver_prices)}\n"
    
    axes[1, 1].text(0.05, 0.95, stats_text, transform=axes[1, 1].transAxes, fontsize=10,
                   verticalalignment='top', fontfamily='monospace',
                   bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    plt.tight_layout()
    
    # 确保 outputs 目录存在
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(output_dir, f"accurate_single_comparison_{symbol}_{timeframe}_{timestamp}.png")
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    print(f"✅ 精确对比图已保存: {filename}")
    print(f"实际相似度: {actual_similarity:.3f} (预期: {expected_similarity:.3f})")
    
    plt.show()
    
    return filename


def main():
    """主函数"""
    print("📊 精确K线形态可视化工具")
    print("=" * 50)
    
    while True:
        print("\n选择功能:")
        print("1. 生成精确的前5名形态对比图")
        print("2. 生成单个品种精确历史对比图")
        print("3. 退出")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == '1':
            filename = create_accurate_comparison_chart()
            if filename:
                print(f"\n🎉 成功生成精确对比图: {filename}")
            
        elif choice == '2':
            print("\n可选的历史匹配:")
            print("1. XBRUSD H4 (2025-06-17 到 2025-06-27, 相似度: 0.931)")
            print("2. XTIUSD H4 (2025-06-17 到 2025-06-27, 相似度: 0.931)")
            print("3. XAUUSD H1 (2025-10-20 到 2025-10-22, 相似度: 0.897)")
            
            sub_choice = input("选择 (1-3) 或输入自定义参数: ").strip()
            
            if sub_choice == '1':
                filename = create_single_accurate_comparison(
                    'XBRUSD', 'H4', 
                    '2025-06-17T12:00:00+00:00', 
                    '2025-06-27T16:00:00+00:00', 
                    0.931
                )
            elif sub_choice == '2':
                filename = create_single_accurate_comparison(
                    'XTIUSD', 'H4', 
                    '2025-06-17T12:00:00+00:00', 
                    '2025-06-27T16:00:00+00:00', 
                    0.931
                )
            elif sub_choice == '3':
                filename = create_single_accurate_comparison(
                    'XAUUSD', 'H1', 
                    '2025-10-20T11:00:00+00:00', 
                    '2025-10-22T14:00:00+00:00', 
                    0.897
                )
            else:
                print("❌ 无效选择")
                continue
                
            if filename:
                print(f"\n🎉 成功生成精确历史对比图: {filename}")
            
        elif choice == '3':
            print("👋 再见!")
            break
            
        else:
            print("❌ 无效选择")


if __name__ == "__main__":
    try:
        import matplotlib.pyplot as plt
        main()
    except ImportError:
        print("❌ 需要安装matplotlib库")
        print("请运行: pip install matplotlib")