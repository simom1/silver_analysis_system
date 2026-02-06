"""
改进版形态可视化工具

主要改进：
1. 使用Z-score标准化，让所有形态在同一尺度显示
2. 同时显示原始价格和标准化形态
3. 更清晰的对比效果
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import List
import sys
import os
import warnings

# 过滤numpy的警告
warnings.filterwarnings('ignore', category=RuntimeWarning, module='numpy')
warnings.filterwarnings('ignore', message='Degrees of freedom <= 0 for slice')
warnings.filterwarnings('ignore', message='divide by zero encountered')
warnings.filterwarnings('ignore', message='invalid value encountered')

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入改进版形态匹配器
try:
    from core.improved_pattern_matcher import ImprovedPatternMatcher, PatternMatch
except ImportError:
    from improved_pattern_matcher import ImprovedPatternMatcher, PatternMatch

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def normalize_for_display(prices: pd.Series, method='zscore') -> np.ndarray:
    """
    为显示标准化价格
    
    Args:
        prices: 价格序列
        method: 标准化方法 ('zscore' 或 'minmax')
        
    Returns:
        标准化后的数组
    """
    if len(prices) < 2:
        return np.array([0])
    
    if method == 'zscore':
        # Z-score标准化
        mean = prices.mean()
        std = prices.std()
        if std == 0:
            return np.zeros(len(prices))
        return ((prices - mean) / std).values
    
    elif method == 'minmax':
        # Min-Max标准化到0-100范围
        min_price = prices.min()
        max_price = prices.max()
        if max_price == min_price:
            return np.zeros(len(prices))
        return ((prices - min_price) / (max_price - min_price) * 100).values
    
    else:
        # 相对第一个价格的百分比变化
        first_price = prices.iloc[0]
        return ((prices - first_price) / first_price * 100).values


def visualize_pattern_matches_improved(matcher: ImprovedPatternMatcher, 
                                       matches: List[PatternMatch],
                                       silver_data: pd.DataFrame,
                                       n_matches: int = 10,
                                       save_path: str = None) -> str:
    """
    改进版形态匹配可视化
    
    Args:
        matcher: 形态匹配器
        matches: 匹配结果列表
        silver_data: 白银数据
        n_matches: 显示前N个匹配
        save_path: 保存路径
        
    Returns:
        保存的文件路径
    """
    if not matches:
        print("❌ 没有匹配结果可以可视化")
        return None
    
    n_matches = min(n_matches, len(matches))
    
    # 计算子图布局
    if n_matches <= 3:
        rows, cols = 1, n_matches + 1
    elif n_matches <= 8:
        rows, cols = 2, 4
    else:
        rows, cols = 3, 4
    
    fig, axes = plt.subplots(rows, cols, figsize=(cols*6, rows*5))
    if rows == 1:
        axes = axes.reshape(1, -1)
    elif cols == 1:
        axes = axes.reshape(-1, 1)
    
    fig.suptitle(f'改进版白银形态匹配可视化 (Z-score标准化)\n白银4H最新50根K线 vs 前{n_matches}名最相似形态', 
                fontsize=16, fontweight='bold')
    
    # 标准化白银数据
    silver_pattern = normalize_for_display(silver_data['close'], method='zscore')
    
    # 第一个图：白银基准形态
    ax = axes[0, 0]
    x_axis = range(len(silver_pattern))
    
    # 绘制标准化形态
    ax.plot(x_axis, silver_pattern, 'b-', linewidth=3, 
           label='白银 XAGUSD H4', marker='o', markersize=4)
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.set_title('白银基准形态\n(Z-score标准化)', fontsize=12, fontweight='bold')
    ax.set_xlabel('K线序号')
    ax.set_ylabel('Z-score')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 添加统计信息
    info_text = f"时间: {silver_data.index[0].strftime('%m-%d %H:%M')}\n"
    info_text += f"  到  {silver_data.index[-1].strftime('%m-%d %H:%M')}\n"
    info_text += f"价格: {silver_data['close'].iloc[0]:.2f} → {silver_data['close'].iloc[-1]:.2f}\n"
    total_change = (silver_data['close'].iloc[-1] / silver_data['close'].iloc[0] - 1) * 100
    info_text += f"涨跌: {total_change:+.2f}%\n"
    info_text += f"Z-score范围: [{silver_pattern.min():.2f}, {silver_pattern.max():.2f}]"
    
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # 绘制匹配的形态
    colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'magenta']
    
    for i, match in enumerate(matches[:n_matches]):
        row = (i + 1) // cols
        col = (i + 1) % cols
        
        if row >= rows or col >= cols:
            break
        
        ax = axes[row, col]
        
        # 获取匹配形态的数据
        match_data = matcher.data_manager.get_data(match.symbol, match.timeframe, count=5000)
        if match_data is None:
            continue
        
        # 提取匹配的50根K线
        match_window = match_data.iloc[match.start_index:match.end_index + 1]
        if len(match_window) != len(silver_data):
            continue
        
        # 标准化匹配形态
        match_pattern = normalize_for_display(match_window['close'], method='zscore')
        
        # 绘制对比
        ax.plot(x_axis, silver_pattern, 'b-', linewidth=2, alpha=0.5, 
               label='白银', marker='o', markersize=3)
        ax.plot(x_axis, match_pattern, color=colors[i % len(colors)], 
               linewidth=3, label=f'{match.symbol}', marker='s', markersize=3)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        # 标题
        title = f"#{i+1} {match.symbol} {match.timeframe}\n"
        title += f"综合相似度: {match.similarity_score:.3f}"
        ax.set_title(title, fontsize=11, fontweight='bold')
        
        ax.set_xlabel('K线序号')
        ax.set_ylabel('Z-score')
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3)
        
        # 添加详细信息
        match_change = (match_window['close'].iloc[-1] / match_window['close'].iloc[0] - 1) * 100
        
        detail_text = f"时间: {match.start_time.strftime('%m-%d %H:%M')}\n"
        detail_text += f"价格: {match_window['close'].iloc[0]:.2f} → {match_window['close'].iloc[-1]:.2f}\n"
        detail_text += f"涨跌: {match_change:+.2f}%\n"
        detail_text += f"形状: {match.shape_similarity:.3f}\n"
        detail_text += f"趋势: {match.trend_similarity:.3f}\n"
        detail_text += f"波动: {match.volatility_similarity:.3f}"
        
        # 根据相似度选择背景色
        if match.similarity_score >= 0.7:
            bg_color = 'lightgreen'
        elif match.similarity_score >= 0.6:
            bg_color = 'lightyellow'
        else:
            bg_color = 'lightcoral'
        
        ax.text(0.98, 0.02, detail_text, transform=ax.transAxes, fontsize=8,
               verticalalignment='bottom', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor=bg_color, alpha=0.8))
    
    # 隐藏多余的子图
    total_subplots = rows * cols
    for i in range(n_matches + 1, total_subplots):
        row = i // cols
        col = i % cols
        if row < rows and col < cols:
            axes[row, col].axis('off')
    
    plt.tight_layout()
    
    # 确保 outputs 目录存在
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存图表
    if not save_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = os.path.join(output_dir, f"improved_pattern_visualization_{timestamp}.png")
    elif not os.path.isabs(save_path):
        save_path = os.path.join(output_dir, save_path)
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"📊 改进版形态对比图已保存: {save_path}")
    
    # 显示图表
    plt.show()
    
    return save_path


def main():
    """主函数"""
    print("=" * 80)
    print("🎨 改进版白银形态可视化工具")
    print("=" * 80)
    print("特点:")
    print("1. 使用Z-score标准化，所有形态在同一尺度显示")
    print("2. 清晰展示形态相似度")
    print("3. 同时显示原始价格变化和标准化形态")
    print("=" * 80)
    
    # 创建形态匹配器
    matcher = ImprovedPatternMatcher()
    
    try:
        while True:
            print(f"\n请选择操作:")
            print("1. 运行形态匹配并可视化")
            print("2. 退出")
            
            choice = input("\n请输入选择 (1-2): ").strip()
            
            if choice == '1':
                print("\n🔍 开始形态匹配分析...")
                
                # 设置参数
                print("\n" + "=" * 60)
                print("📋 参数说明")
                print("=" * 60)
                print("显示数量: 在图表上显示多少个形态对比")
                print("  - 每个形态 = 50根K线")
                print("  - 建议不超过12个（否则图太小）")
                print()
                print("相似度阈值: 过滤掉相似度低的形态")
                print("  - 推荐: 0.3-0.5 (排除同期数据后建议降低)")
                print()
                print("⚠️  系统会自动排除与白银同期的数据")
                print("=" * 60)
                print()
                
                top_n = int(input("显示多少个相似形态 (默认9): ") or "9")
                min_similarity = float(input("最小相似度阈值 (默认0.3): ") or "0.3")
                
                # 运行分析
                matches = matcher.run_pattern_matching(top_n=top_n, min_similarity=min_similarity)
                
                if matches:
                    # 获取白银数据
                    silver_data_full = matcher.data_manager.get_data('XAGUSD', 'H4', count=50)
                    silver_data = silver_data_full.iloc[-50:]
                    
                    # 可视化
                    print(f"\n🎨 生成可视化图表...")
                    save_path = visualize_pattern_matches_improved(
                        matcher, matches, silver_data, n_matches=top_n
                    )
                    
                    if save_path:
                        print(f"✅ 可视化完成")
                else:
                    print("❌ 没有找到相似的形态")
                
            elif choice == '2':
                print("👋 再见!")
                break
                
            else:
                print("❌ 无效选择，请重新输入")
                
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        matcher.data_manager.disconnect_mt5()


if __name__ == "__main__":
    main()
