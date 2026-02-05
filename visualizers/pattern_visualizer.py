"""
K线形态可视化对比工具

生成白银与最相似品种的形态对比图
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# 导入MT5客户端
from metatrader_tools.mt5_client.client import MT5Client
from metatrader_tools.mt5_client.periods import timeframe_from_str

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_prices_for_comparison(prices1, prices2):
    """标准化两个价格序列用于对比"""
    # 都转换为从0开始的百分比变化
    norm1 = [(p - prices1[0]) / prices1[0] * 100 for p in prices1]
    norm2 = [(p - prices2[0]) / prices2[0] * 100 for p in prices2]
    return norm1, norm2


def create_pattern_comparison_chart(silver_data, match_data, match_info, save_path=None):
    """
    创建形态对比图
    
    Args:
        silver_data: 白银数据
        match_data: 匹配品种数据
        match_info: 匹配信息字典
        save_path: 保存路径
    """
    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'白银 vs {match_info["symbol"]} 形态对比分析\n相似度: {match_info["similarity"]:.4f}', 
                 fontsize=16, fontweight='bold')
    
    # 提取价格数据
    silver_prices = silver_data['close'].tolist()
    match_prices = match_data['close'].tolist()
    
    # 标准化价格用于对比
    silver_norm, match_norm = normalize_prices_for_comparison(silver_prices, match_prices)
    
    # 1. 原始价格对比图
    ax1 = axes[0, 0]
    ax1.plot(range(len(silver_prices)), silver_prices, 'b-', linewidth=2, label=f'白银 (XAGUSD)', marker='o', markersize=3)
    ax1.plot(range(len(match_prices)), match_prices, 'r-', linewidth=2, label=f'{match_info["symbol"]}', marker='s', markersize=3)
    ax1.set_title('原始价格对比', fontsize=12, fontweight='bold')
    ax1.set_xlabel('K线序号')
    ax1.set_ylabel('价格')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 标准化价格对比图（重点）
    ax2 = axes[0, 1]
    ax2.plot(range(len(silver_norm)), silver_norm, 'b-', linewidth=3, label=f'白银 (标准化)', marker='o', markersize=4)
    ax2.plot(range(len(match_norm)), match_norm, 'r--', linewidth=3, label=f'{match_info["symbol"]} (标准化)', marker='s', markersize=4)
    ax2.set_title(f'标准化形态对比 (相似度: {match_info["similarity"]:.4f})', fontsize=12, fontweight='bold')
    ax2.set_xlabel('K线序号')
    ax2.set_ylabel('相对变化 (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 添加相似度文本
    ax2.text(0.02, 0.98, f'相似度: {match_info["similarity"]:.4f}\n时间段: {match_info["time_period"]}', 
             transform=ax2.transAxes, fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # 3. 收益率对比图
    ax3 = axes[1, 0]
    silver_returns = [0] + [(silver_prices[i] - silver_prices[i-1]) / silver_prices[i-1] * 100 
                           for i in range(1, len(silver_prices))]
    match_returns = [0] + [(match_prices[i] - match_prices[i-1]) / match_prices[i-1] * 100 
                          for i in range(1, len(match_prices))]
    
    ax3.bar(range(len(silver_returns)), silver_returns, alpha=0.7, label='白银收益率', color='blue', width=0.4)
    ax3.bar([x+0.4 for x in range(len(match_returns))], match_returns, alpha=0.7, 
            label=f'{match_info["symbol"]}收益率', color='red', width=0.4)
    ax3.set_title('单期收益率对比', fontsize=12, fontweight='bold')
    ax3.set_xlabel('K线序号')
    ax3.set_ylabel('收益率 (%)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    # 4. 统计信息图
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # 计算统计信息
    silver_stats = {
        '最高价': max(silver_prices),
        '最低价': min(silver_prices),
        '总涨幅': (silver_prices[-1] - silver_prices[0]) / silver_prices[0] * 100,
        '波动率': np.std(silver_returns) if len(silver_returns) > 1 else 0,
        '平均收益': np.mean(silver_returns) if len(silver_returns) > 1 else 0
    }
    
    match_stats = {
        '最高价': max(match_prices),
        '最低价': min(match_prices),
        '总涨幅': (match_prices[-1] - match_prices[0]) / match_prices[0] * 100,
        '波动率': np.std(match_returns) if len(match_returns) > 1 else 0,
        '平均收益': np.mean(match_returns) if len(match_returns) > 1 else 0
    }
    
    # 创建统计表格
    stats_text = "统计对比信息\n" + "="*30 + "\n"
    stats_text += f"{'指标':<12} {'白银':<15} {match_info['symbol']:<15}\n"
    stats_text += "-"*45 + "\n"
    
    for key in silver_stats:
        if '价' in key:
            stats_text += f"{key:<12} {silver_stats[key]:<15.2f} {match_stats[key]:<15.2f}\n"
        else:
            stats_text += f"{key:<12} {silver_stats[key]:<15.2f}% {match_stats[key]:<15.2f}%\n"
    
    stats_text += "\n形态匹配信息\n" + "="*30 + "\n"
    stats_text += f"品种: {match_info['symbol']}\n"
    stats_text += f"时间框架: {match_info['timeframe']}\n"
    stats_text += f"相似度: {match_info['similarity']:.4f}\n"
    stats_text += f"匹配时间段: {match_info['time_period']}\n"
    stats_text += f"数据点数: {len(silver_prices)} 根K线\n"
    
    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 对比图已保存到: {save_path}")
    
    plt.show()
    
    return fig


def create_multi_pattern_comparison(silver_data, matches_data, save_path=None):
    """
    创建多个形态对比图
    
    Args:
        silver_data: 白银数据
        matches_data: 多个匹配结果的数据列表
        save_path: 保存路径
    """
    n_matches = len(matches_data)
    if n_matches == 0:
        return None
    
    # 创建子图
    rows = (n_matches + 1) // 2 + 1  # +1 for silver baseline
    fig, axes = plt.subplots(rows, 2, figsize=(16, 4*rows))
    if rows == 1:
        axes = axes.reshape(1, -1)
    
    fig.suptitle('白银形态 vs 多个最相似形态对比', fontsize=16, fontweight='bold')
    
    # 白银基准数据
    silver_prices = silver_data['close'].tolist()
    silver_norm = [(p - silver_prices[0]) / silver_prices[0] * 100 for p in silver_prices]
    
    # 第一个图：白银基准
    ax = axes[0, 0]
    ax.plot(range(len(silver_norm)), silver_norm, 'b-', linewidth=3, 
            label='白银 (XAGUSD H4)', marker='o', markersize=4)
    ax.set_title('白银基准形态 (最新50根K线)', fontsize=12, fontweight='bold')
    ax.set_xlabel('K线序号')
    ax.set_ylabel('相对变化 (%)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 添加时间信息
    time_info = f"时间: {silver_data.index[0].strftime('%Y-%m-%d')} 到 {silver_data.index[-1].strftime('%Y-%m-%d')}"
    ax.text(0.02, 0.98, time_info, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # 其他匹配形态
    colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive']
    
    for i, match_data in enumerate(matches_data):
        row = (i + 1) // 2
        col = (i + 1) % 2
        
        if row >= rows:
            break
            
        ax = axes[row, col]
        
        # 匹配品种数据
        match_prices = match_data['data']['close'].tolist()
        match_norm = [(p - match_prices[0]) / match_prices[0] * 100 for p in match_prices]
        
        # 绘制对比
        ax.plot(range(len(silver_norm)), silver_norm, 'b-', linewidth=2, 
                label='白银', alpha=0.7, marker='o', markersize=3)
        ax.plot(range(len(match_norm)), match_norm, color=colors[i % len(colors)], 
                linestyle='--', linewidth=3, label=f"{match_data['symbol']}", 
                marker='s', markersize=3)
        
        ax.set_title(f"{match_data['symbol']} {match_data['timeframe']} (相似度: {match_data['similarity']:.3f})", 
                    fontsize=11, fontweight='bold')
        ax.set_xlabel('K线序号')
        ax.set_ylabel('相对变化 (%)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 添加时间信息
        time_period = f"{match_data['time_period']}"
        ax.text(0.02, 0.98, time_period, transform=ax.transAxes, fontsize=8,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # 隐藏多余的子图
    for i in range(len(matches_data) + 1, rows * 2):
        row = i // 2
        col = i % 2
        if row < rows:
            axes[row, col].axis('off')
    
    plt.tight_layout()
    
    # 保存图表
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 多重对比图已保存到: {save_path}")
    
    plt.show()
    
    return fig


def visualize_pattern_matches():
    """可视化形态匹配结果"""
    
    print("📊 K线形态可视化对比工具")
    print("=" * 50)
    
    # 配置参数
    silver_symbol = 'XAGUSD'
    silver_timeframe = 'H4'
    silver_bars = 50
    
    # 最相似的几个形态（基于之前的分析结果）
    top_matches = [
        {'symbol': 'XBRUSD', 'timeframe': 'H4', 'similarity': 0.931, 'period': '2025-06-17 12:00 ~ 2025-06-27 16:00'},
        {'symbol': 'XTIUSD', 'timeframe': 'H4', 'similarity': 0.931, 'period': '2025-06-17 12:00 ~ 2025-06-27 16:00'},
        {'symbol': 'XBRUSD', 'timeframe': 'H1', 'similarity': 0.905, 'period': '2025-01-29 19:00 ~ 2025-02-03 05:00'},
        {'symbol': 'US500', 'timeframe': 'H4', 'similarity': 0.903, 'period': '2025-03-28 12:00 ~ 2025-04-09 16:00'},
    ]
    
    try:
        with MT5Client() as client:
            print("✅ MT5连接成功")
            
            # 获取白银基准数据
            print(f"\n📊 获取白银基准数据...")
            silver_tf = timeframe_from_str(silver_timeframe)
            silver_data = client.get_rates(silver_symbol, silver_tf, count=silver_bars)
            
            if silver_data.empty:
                print("❌ 无法获取白银数据")
                return
            
            print(f"✅ 白银数据获取成功: {len(silver_data)} 根K线")
            
            # 选择要可视化的匹配
            print(f"\n请选择要可视化的形态:")
            print("1. 布伦特原油 H4 (相似度: 0.931)")
            print("2. WTI原油 H4 (相似度: 0.931)")
            print("3. 标普500 H4 (相似度: 0.903)")
            print("4. 生成多重对比图")
            print("5. 自定义品种")
            
            choice = input("\n请选择 (1-5): ").strip()
            
            if choice in ['1', '2', '3']:
                # 单个对比
                match_idx = int(choice) - 1
                match = top_matches[match_idx]
                
                print(f"\n🔍 获取 {match['symbol']} {match['timeframe']} 数据...")
                
                # 获取匹配品种数据
                match_tf = timeframe_from_str(match['timeframe'])
                match_data = client.get_rates(match['symbol'], match_tf, count=2000)
                
                if match_data.empty:
                    print(f"❌ 无法获取 {match['symbol']} 数据")
                    return
                
                # 找到最相似的50根K线段（简化处理，使用最新的50根）
                match_segment = match_data.tail(silver_bars)
                
                # 创建匹配信息
                match_info = {
                    'symbol': match['symbol'],
                    'timeframe': match['timeframe'],
                    'similarity': match['similarity'],
                    'time_period': match['period']
                }
                
                # 生成对比图
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                save_path = f"pattern_comparison_{match['symbol']}_{timestamp}.png"
                
                print(f"\n📊 生成对比图...")
                create_pattern_comparison_chart(silver_data, match_segment, match_info, save_path)
                
            elif choice == '4':
                # 多重对比图
                print(f"\n🔍 获取多个品种数据...")
                
                matches_data = []
                for match in top_matches[:4]:  # 前4个
                    try:
                        match_tf = timeframe_from_str(match['timeframe'])
                        match_data = client.get_rates(match['symbol'], match_tf, count=100)
                        
                        if not match_data.empty:
                            match_segment = match_data.tail(silver_bars)
                            matches_data.append({
                                'symbol': match['symbol'],
                                'timeframe': match['timeframe'],
                                'similarity': match['similarity'],
                                'time_period': match['period'],
                                'data': match_segment
                            })
                            print(f"✅ {match['symbol']} {match['timeframe']}")
                        else:
                            print(f"❌ {match['symbol']} {match['timeframe']}")
                            
                    except Exception as e:
                        print(f"❌ {match['symbol']} {match['timeframe']}: {e}")
                
                if matches_data:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_path = f"multi_pattern_comparison_{timestamp}.png"
                    
                    print(f"\n📊 生成多重对比图...")
                    create_multi_pattern_comparison(silver_data, matches_data, save_path)
                else:
                    print("❌ 没有获取到有效的对比数据")
                    
            elif choice == '5':
                # 自定义品种
                symbol = input("请输入品种代码 (如 XAUUSD): ").strip().upper()
                timeframe = input("请输入时间框架 (如 H1, H4): ").strip().upper()
                
                if symbol and timeframe:
                    print(f"\n🔍 获取 {symbol} {timeframe} 数据...")
                    
                    try:
                        match_tf = timeframe_from_str(timeframe)
                        match_data = client.get_rates(symbol, match_tf, count=100)
                        
                        if not match_data.empty:
                            match_segment = match_data.tail(silver_bars)
                            
                            match_info = {
                                'symbol': symbol,
                                'timeframe': timeframe,
                                'similarity': 0.000,  # 未计算
                                'time_period': f"{match_segment.index[0]} ~ {match_segment.index[-1]}"
                            }
                            
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            save_path = f"pattern_comparison_{symbol}_{timestamp}.png"
                            
                            print(f"\n📊 生成对比图...")
                            create_pattern_comparison_chart(silver_data, match_segment, match_info, save_path)
                        else:
                            print(f"❌ 无法获取 {symbol} 数据")
                            
                    except Exception as e:
                        print(f"❌ 错误: {e}")
            
            else:
                print("❌ 无效选择")
                
    except Exception as e:
        logger.error(f"可视化失败: {e}")
        print(f"❌ 可视化失败: {e}")


if __name__ == "__main__":
    # 检查matplotlib是否安装
    try:
        import matplotlib.pyplot as plt
        visualize_pattern_matches()
    except ImportError:
        print("❌ 需要安装matplotlib库")
        print("请运行: pip install matplotlib")