"""
快速图表生成器

基于形态匹配结果快速生成可视化对比图
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import json
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


def generate_top_matches_chart():
    """生成前几名最相似形态的对比图"""
    
    print("📊 快速生成形态对比图")
    print("=" * 40)
    
    # 基于你的分析结果
    silver_config = {
        'symbol': 'XAGUSD',
        'timeframe': 'H4',
        'bars': 50
    }
    
    # 前5名最相似的形态
    top_matches = [
        {'symbol': 'XBRUSD', 'timeframe': 'H4', 'similarity': 0.931, 'name': '布伦特原油4H'},
        {'symbol': 'XTIUSD', 'timeframe': 'H4', 'similarity': 0.931, 'name': 'WTI原油4H'},
        {'symbol': 'XBRUSD', 'timeframe': 'H1', 'similarity': 0.905, 'name': '布伦特原油1H'},
        {'symbol': 'US500', 'timeframe': 'H4', 'similarity': 0.903, 'name': '标普500 4H'},
        {'symbol': 'XAUUSD', 'timeframe': 'H1', 'similarity': 0.897, 'name': '黄金1H'},
    ]
    
    try:
        with MT5Client() as client:
            print("✅ MT5连接成功")
            
            # 获取白银数据
            print("📊 获取白银基准数据...")
            silver_tf = timeframe_from_str(silver_config['timeframe'])
            silver_data = client.get_rates(silver_config['symbol'], silver_tf, count=silver_config['bars'])
            
            if silver_data.empty:
                print("❌ 无法获取白银数据")
                return
            
            silver_prices = silver_data['close'].tolist()
            silver_norm = [(p - silver_prices[0]) / silver_prices[0] * 100 for p in silver_prices]
            
            # 创建图表
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle('白银4H形态 vs 最相似品种对比图\n(标准化显示 - 相对变化百分比)', 
                        fontsize=16, fontweight='bold')
            
            # 第一个图：白银基准
            ax = axes[0, 0]
            ax.plot(range(len(silver_norm)), silver_norm, 'b-', linewidth=3, 
                   label='白银 XAGUSD H4', marker='o', markersize=4)
            ax.set_title('白银基准形态\n(最新50根4H K线)', fontsize=12, fontweight='bold')
            ax.set_xlabel('K线序号')
            ax.set_ylabel('相对变化 (%)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # 添加价格范围信息
            price_info = f"价格范围: {min(silver_prices):.2f} - {max(silver_prices):.2f}"
            ax.text(0.02, 0.98, price_info, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            
            # 获取并绘制匹配品种
            colors = ['red', 'green', 'orange', 'purple', 'brown']
            
            for i, match in enumerate(top_matches):
                row = (i + 1) // 3
                col = (i + 1) % 3
                
                print(f"📊 获取 {match['name']} 数据...")
                
                try:
                    # 获取匹配品种数据
                    match_tf = timeframe_from_str(match['timeframe'])
                    match_data = client.get_rates(match['symbol'], match_tf, count=200)
                    
                    if match_data.empty:
                        print(f"❌ 无法获取 {match['symbol']} 数据")
                        continue
                    
                    # 使用最新的50根K线
                    match_segment = match_data.tail(silver_config['bars'])
                    match_prices = match_segment['close'].tolist()
                    match_norm = [(p - match_prices[0]) / match_prices[0] * 100 for p in match_prices]
                    
                    # 绘制对比图
                    ax = axes[row, col]
                    
                    # 白银（半透明）
                    ax.plot(range(len(silver_norm)), silver_norm, 'b-', linewidth=2, 
                           alpha=0.6, label='白银', marker='o', markersize=3)
                    
                    # 匹配品种（突出显示）
                    ax.plot(range(len(match_norm)), match_norm, color=colors[i], 
                           linewidth=3, label=match['name'], marker='s', markersize=3)
                    
                    ax.set_title(f"{match['name']}\n相似度: {match['similarity']:.3f}", 
                               fontsize=11, fontweight='bold')
                    ax.set_xlabel('K线序号')
                    ax.set_ylabel('相对变化 (%)')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    
                    # 添加统计信息
                    total_change_silver = silver_norm[-1]
                    total_change_match = match_norm[-1]
                    
                    stats_text = f"白银总变化: {total_change_silver:.2f}%\n{match['name']}: {total_change_match:.2f}%"
                    ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=8,
                           verticalalignment='bottom', 
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                    
                    print(f"✅ {match['name']} - 相似度: {match['similarity']:.3f}")
                    
                except Exception as e:
                    print(f"❌ {match['symbol']}: {e}")
                    # 隐藏失败的子图
                    axes[row, col].axis('off')
                    continue
            
            # 隐藏多余的子图
            for i in range(len(top_matches) + 1, 6):
                row = i // 3
                col = i % 3
                axes[row, col].axis('off')
            
            plt.tight_layout()
            
            # 确保 outputs 目录存在
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存图表
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(output_dir, f"silver_pattern_comparison_{timestamp}.png")
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            
            print(f"\n📊 对比图已生成并保存:")
            print(f"文件名: {filename}")
            print(f"分辨率: 300 DPI")
            print(f"格式: PNG")
            
            # 显示图表
            plt.show()
            
            return filename
            
    except Exception as e:
        print(f"❌ 生成图表失败: {e}")
        return None


def generate_single_comparison(symbol, timeframe, similarity=None):
    """生成单个品种的详细对比图"""
    
    print(f"📊 生成 {symbol} {timeframe} 详细对比图")
    print("=" * 40)
    
    try:
        with MT5Client() as client:
            # 获取白银数据
            silver_data = client.get_rates('XAGUSD', timeframe_from_str('H4'), count=50)
            match_data = client.get_rates(symbol, timeframe_from_str(timeframe), count=50)
            
            if silver_data.empty or match_data.empty:
                print("❌ 数据获取失败")
                return None
            
            # 创建详细对比图
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f'白银 vs {symbol} 详细形态对比', fontsize=16, fontweight='bold')
            
            silver_prices = silver_data['close'].tolist()
            match_prices = match_data['close'].tolist()
            
            # 标准化
            silver_norm = [(p - silver_prices[0]) / silver_prices[0] * 100 for p in silver_prices]
            match_norm = [(p - match_prices[0]) / match_prices[0] * 100 for p in match_prices]
            
            # 1. 标准化对比
            axes[0, 0].plot(silver_norm, 'b-', linewidth=3, label='白银', marker='o')
            axes[0, 0].plot(match_norm, 'r--', linewidth=3, label=symbol, marker='s')
            axes[0, 0].set_title('标准化形态对比')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # 2. 原始价格
            axes[0, 1].plot(silver_prices, 'b-', linewidth=2, label='白银价格')
            ax2 = axes[0, 1].twinx()
            ax2.plot(match_prices, 'r-', linewidth=2, label=f'{symbol}价格')
            axes[0, 1].set_title('原始价格对比')
            axes[0, 1].legend(loc='upper left')
            ax2.legend(loc='upper right')
            
            # 3. 收益率对比
            silver_returns = [0] + [silver_norm[i] - silver_norm[i-1] for i in range(1, len(silver_norm))]
            match_returns = [0] + [match_norm[i] - match_norm[i-1] for i in range(1, len(match_norm))]
            
            axes[1, 0].bar(range(len(silver_returns)), silver_returns, alpha=0.7, label='白银', width=0.4)
            axes[1, 0].bar([x+0.4 for x in range(len(match_returns))], match_returns, 
                          alpha=0.7, label=symbol, width=0.4)
            axes[1, 0].set_title('单期变化对比')
            axes[1, 0].legend()
            axes[1, 0].axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            # 4. 散点图相关性
            axes[1, 1].scatter(silver_norm, match_norm, alpha=0.7)
            axes[1, 1].plot([min(silver_norm), max(silver_norm)], 
                           [min(silver_norm), max(silver_norm)], 'r--', alpha=0.5)
            axes[1, 1].set_xlabel('白银变化 (%)')
            axes[1, 1].set_ylabel(f'{symbol}变化 (%)')
            axes[1, 1].set_title('相关性散点图')
            
            if similarity:
                axes[1, 1].text(0.05, 0.95, f'相似度: {similarity:.3f}', 
                               transform=axes[1, 1].transAxes, fontsize=12,
                               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
            
            plt.tight_layout()
            
            # 确保 outputs 目录存在
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(output_dir, f"detailed_comparison_{symbol}_{timeframe}_{timestamp}.png")
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            
            print(f"✅ 详细对比图已保存: {filename}")
            plt.show()
            
            return filename
            
    except Exception as e:
        print(f"❌ 生成详细对比图失败: {e}")
        return None


def main():
    """主函数"""
    print("📊 K线形态可视化工具")
    print("=" * 40)
    
    while True:
        print("\n选择功能:")
        print("1. 生成前5名最相似形态对比图")
        print("2. 生成单个品种详细对比图")
        print("3. 退出")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == '1':
            filename = generate_top_matches_chart()
            if filename:
                print(f"\n🎉 成功生成对比图: {filename}")
            
        elif choice == '2':
            symbol = input("请输入品种代码 (如 XBRUSD): ").strip().upper()
            timeframe = input("请输入时间框架 (如 H4): ").strip().upper()
            similarity = input("请输入相似度 (可选): ").strip()
            
            if symbol and timeframe:
                sim_value = float(similarity) if similarity else None
                filename = generate_single_comparison(symbol, timeframe, sim_value)
                if filename:
                    print(f"\n🎉 成功生成详细对比图: {filename}")
            
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