"""
真正的K线形态匹配可视化工具

基于算法计算的形态相似度，使用本地数据
实现欧氏距离、DTW、皮尔逊相关、余弦相似度等算法
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import json

# 导入数据管理器
from silver_data_manager import DataManager

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """形态匹配结果"""
    symbol: str
    timeframe: str
    similarity_score: float
    start_index: int
    end_index: int
    start_time: datetime
    end_time: datetime
    pattern_data: pd.DataFrame
    similarity_details: Dict[str, float]


class RealPatternMatcher:
    """真正的形态匹配器"""
    
    def __init__(self, data_dir: str = "market_data"):
        self.data_manager = DataManager(data_dir)
        
        # 监测的品种和时间框架
        self.target_symbols = {
            'XAUUSD': ['H1', 'H4'],  # 黄金
            'XTIUSD': ['H1', 'H4'],  # WTI原油
            'XBRUSD': ['H1', 'H4'],  # 布伦特原油
            'US500': ['H1', 'H4'],   # 标普500
            'US30': ['H1', 'H4'],    # 道琼斯
            'NAS100': ['H1', 'H4'],  # 纳斯达克100
            'EURUSD': ['H1', 'H4'],  # 欧美
            'GBPUSD': ['H1', 'H4'],  # 英美
        }
        
        # 白银基准参数
        self.silver_symbol = 'XAGUSD'
        self.silver_timeframe = 'H4'
        self.silver_bars = 50
    
    def normalize_price_series(self, prices: pd.Series) -> np.ndarray:
        """
        价格序列标准化
        转换为相对于第一个价格的百分比变化
        """
        if len(prices) < 2:
            return np.array([0])
        
        first_price = prices.iloc[0]
        normalized = ((prices - first_price) / first_price * 100).values
        return normalized
    
    def calculate_euclidean_similarity(self, pattern1: np.ndarray, pattern2: np.ndarray) -> float:
        """
        欧氏距离相似度
        距离越小，相似度越高
        """
        if len(pattern1) != len(pattern2):
            return 0.0
        
        # 计算欧氏距离
        distance = np.sqrt(np.sum((pattern1 - pattern2) ** 2))
        
        # 转换为相似度 (0-1)
        # 假设最大可能距离为每个点都相差100%
        max_distance = np.sqrt(len(pattern1) * (100 ** 2))
        similarity = 1 - (distance / max_distance)
        
        return max(0, min(1, similarity))
    
    def calculate_dtw_distance(self, pattern1: np.ndarray, pattern2: np.ndarray) -> float:
        """
        动态时间规整(DTW)距离
        允许时间拉伸/压缩的形态匹配
        """
        if len(pattern1) != len(pattern2):
            return float('inf')
        
        n, m = len(pattern1), len(pattern2)
        
        # 创建DTW矩阵
        dtw_matrix = np.full((n + 1, m + 1), float('inf'))
        dtw_matrix[0, 0] = 0
        
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = abs(pattern1[i-1] - pattern2[j-1])
                dtw_matrix[i, j] = cost + min(
                    dtw_matrix[i-1, j],      # 插入
                    dtw_matrix[i, j-1],      # 删除
                    dtw_matrix[i-1, j-1]     # 匹配
                )
        
        return dtw_matrix[n, m]
    
    def calculate_dtw_similarity(self, pattern1: np.ndarray, pattern2: np.ndarray) -> float:
        """DTW相似度 (0-1)"""
        dtw_distance = self.calculate_dtw_distance(pattern1, pattern2)
        if dtw_distance == float('inf'):
            return 0.0
        
        # 转换为相似度
        max_possible_distance = len(pattern1) * 100  # 假设最大差异100%
        similarity = 1 - (dtw_distance / max_possible_distance)
        
        return max(0, min(1, similarity))
    
    def calculate_pearson_correlation(self, pattern1: np.ndarray, pattern2: np.ndarray) -> float:
        """
        皮尔逊相关系数
        衡量线性相关性，关注趋势方向一致性
        """
        if len(pattern1) != len(pattern2) or len(pattern1) < 2:
            return 0.0
        
        correlation = np.corrcoef(pattern1, pattern2)[0, 1]
        
        if np.isnan(correlation):
            return 0.0
        
        # 返回绝对值，因为我们关心形态相似性，不区分正负相关
        return abs(correlation)
    
    def calculate_cosine_similarity(self, pattern1: np.ndarray, pattern2: np.ndarray) -> float:
        """
        余弦相似度
        衡量向量方向的相似性
        """
        if len(pattern1) != len(pattern2):
            return 0.0
        
        # 计算余弦相似度
        dot_product = np.dot(pattern1, pattern2)
        norm1 = np.linalg.norm(pattern1)
        norm2 = np.linalg.norm(pattern2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_sim = dot_product / (norm1 * norm2)
        
        # 转换到0-1范围，取绝对值
        return abs(cosine_sim)
    
    def calculate_combined_similarity(self, pattern1: np.ndarray, pattern2: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """
        综合相似度计算
        结合多种算法的加权平均
        """
        # 计算各种相似度
        euclidean_sim = self.calculate_euclidean_similarity(pattern1, pattern2)
        dtw_sim = self.calculate_dtw_similarity(pattern1, pattern2)
        pearson_sim = self.calculate_pearson_correlation(pattern1, pattern2)
        cosine_sim = self.calculate_cosine_similarity(pattern1, pattern2)
        
        # 权重设置（可调整）
        weights = {
            'euclidean': 0.3,   # 形状相似性
            'dtw': 0.3,         # 允许时间拉伸的形状相似性
            'pearson': 0.2,     # 趋势方向一致性
            'cosine': 0.2       # 向量方向相似性
        }
        
        # 加权平均
        combined_score = (
            euclidean_sim * weights['euclidean'] +
            dtw_sim * weights['dtw'] +
            pearson_sim * weights['pearson'] +
            cosine_sim * weights['cosine']
        )
        
        details = {
            'euclidean': euclidean_sim,
            'dtw': dtw_sim,
            'pearson': pearson_sim,
            'cosine': cosine_sim,
            'combined': combined_score
        }
        
        return combined_score, details
    
    def find_best_matches(self, silver_pattern: np.ndarray, target_data: pd.DataFrame, 
                         symbol: str, timeframe: str, window_size: int = 50) -> List[PatternMatch]:
        """
        在目标数据中寻找最佳匹配
        使用滑动窗口算法
        """
        matches = []
        
        if len(target_data) < window_size:
            return matches
        
        print(f"  搜索 {symbol} {timeframe}... (数据长度: {len(target_data)})")
        
        best_similarity = -1  # 改为-1，确保能找到匹配
        best_match = None
        
        # 滑动窗口搜索
        step = max(1, window_size // 10)  # 步长优化，减少计算量
        
        for i in range(0, len(target_data) - window_size + 1, step):
            window_data = target_data.iloc[i:i + window_size]
            window_pattern = self.normalize_price_series(window_data['close'])
            
            # 计算综合相似度
            similarity, details = self.calculate_combined_similarity(silver_pattern, window_pattern)
            
            # 保留最佳匹配
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = PatternMatch(
                    symbol=symbol,
                    timeframe=timeframe,
                    similarity_score=similarity,
                    start_index=i,
                    end_index=i + window_size - 1,
                    start_time=window_data.index[0],
                    end_time=window_data.index[-1],
                    pattern_data=window_data.copy(),
                    similarity_details=details
                )
        
        if best_match:
            matches.append(best_match)
            print(f"    ✅ 最佳相似度: {best_similarity:.3f}")
        else:
            print(f"    ❌ 未找到匹配")
        
        return matches
    
    def run_pattern_matching(self, top_n: int = 10) -> List[PatternMatch]:
        """
        运行真正的形态匹配分析
        """
        print("🔍 开始真正的K线形态匹配分析...")
        print("=" * 60)
        
        # 获取白银基准形态
        print(f"📊 获取白银基准形态: {self.silver_symbol} {self.silver_timeframe} 最后{self.silver_bars}根K线")
        silver_data_full = self.data_manager.get_data(self.silver_symbol, self.silver_timeframe, count=5000)
        
        if silver_data_full is None or len(silver_data_full) < self.silver_bars:
            print("❌ 无法获取白银基准数据")
            return []
        
        # 取最新的50根K线作为基准形态
        silver_data = silver_data_full.tail(self.silver_bars)
        
        # 标准化白银形态
        silver_pattern = self.normalize_price_series(silver_data['close'])
        
        print(f"✅ 白银基准形态获取成功")
        print(f"   时间范围: {silver_data.index[0]} 到 {silver_data.index[-1]}")
        print(f"   价格范围: {silver_data['close'].min():.2f} - {silver_data['close'].max():.2f}")
        print(f"   形态特征: {len(silver_pattern)} 个数据点")
        
        all_matches = []
        
        # 搜索所有目标品种
        print(f"\n🔍 开始搜索相似形态...")
        print("-" * 60)
        
        for symbol, timeframes in self.target_symbols.items():
            for timeframe in timeframes:
                try:
                    # 获取目标数据
                    target_data = self.data_manager.get_data(symbol, timeframe, count=2000)
                    
                    if target_data is None or len(target_data) < self.silver_bars:
                        print(f"  ❌ {symbol} {timeframe}: 数据不足")
                        continue
                    
                    # 寻找最佳匹配
                    matches = self.find_best_matches(
                        silver_pattern, target_data, symbol, timeframe, self.silver_bars
                    )
                    
                    all_matches.extend(matches)
                    
                except Exception as e:
                    print(f"  ❌ {symbol} {timeframe}: 错误 - {e}")
                    continue
        
        # 按相似度排序
        all_matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        print(f"\n📊 形态匹配完成!")
        print(f"   共找到 {len(all_matches)} 个匹配结果")
        print(f"   返回前 {min(top_n, len(all_matches))} 个最相似的形态")
        
        return all_matches[:top_n]
    
    def create_comparison_chart(self, matches: List[PatternMatch], 
                              save_path: Optional[str] = None):
        """
        创建真正的形态对比图
        只比较白银4H最新50根K线
        """
        if not matches:
            print("❌ 没有匹配结果可以可视化")
            return None
        
        # 获取白银最新50根K线
        silver_data_full = self.data_manager.get_data(self.silver_symbol, self.silver_timeframe, count=5000)
        if silver_data_full is None:
            print("❌ 无法获取白银数据")
            return None
        
        silver_data = silver_data_full.tail(self.silver_bars)  # 只取最新50根
        silver_pattern = self.normalize_price_series(silver_data['close'])
        
        # 创建图表 - 可以显示更多匹配结果
        n_matches = min(8, len(matches))  # 最多显示8个匹配结果
        
        # 动态计算布局
        if n_matches <= 2:
            rows, cols = 2, 2
        elif n_matches <= 5:
            rows, cols = 2, 3
        elif n_matches <= 8:
            rows, cols = 3, 3
        else:
            rows, cols = 3, 4
            
        fig, axes = plt.subplots(rows, cols, figsize=(cols*6, rows*4))
        if rows == 1:
            axes = axes.reshape(1, -1)
        elif cols == 1:
            axes = axes.reshape(-1, 1)
            
        fig.suptitle(f'白银4H最新50根K线 vs 前{n_matches}名最相似形态\n(基于欧氏距离+DTW+相关性+余弦相似度)', 
                    fontsize=16, fontweight='bold')
        
        # 第一个图：白银基准形态（最新50根）
        ax = axes[0, 0]
        ax.plot(range(len(silver_pattern)), silver_pattern, 'b-', linewidth=3, 
               label='白银 XAGUSD H4', marker='o', markersize=4)
        ax.set_title('白银基准形态\n(最新50根4H K线)', fontsize=12, fontweight='bold')
        ax.set_xlabel('K线序号 (1-50)')
        ax.set_ylabel('相对变化 (%)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 添加白银统计信息
        info_text = f"时间: {silver_data.index[0].strftime('%m-%d %H:%M')} 到\n"
        info_text += f"      {silver_data.index[-1].strftime('%m-%d %H:%M')}\n"
        info_text += f"价格: {silver_data['close'].min():.2f} - {silver_data['close'].max():.2f}\n"
        info_text += f"总变化: {silver_pattern[-1]:.2f}%\n"
        info_text += f"波动: {np.std(silver_pattern):.2f}%"
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # 绘制匹配的形态
        colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'magenta', 'yellow', 'lime', 'navy', 'maroon', 'teal']
        
        for i, match in enumerate(matches[:n_matches]):
            row = (i + 1) // cols
            col = (i + 1) % cols
            
            ax = axes[row, col]
            
            # 匹配形态的标准化数据（确保也是50根）
            match_pattern = self.normalize_price_series(match.pattern_data['close'])
            
            # 确保长度一致
            if len(match_pattern) != len(silver_pattern):
                print(f"⚠️ 长度不匹配: 白银{len(silver_pattern)}, {match.symbol}{len(match_pattern)}")
                continue
            
            # 绘制对比
            ax.plot(range(len(silver_pattern)), silver_pattern, 'b-', linewidth=2, 
                   alpha=0.6, label='白银', marker='o', markersize=3)
            ax.plot(range(len(match_pattern)), match_pattern, color=colors[i], 
                   linewidth=3, label=f'{match.symbol}', marker='s', markersize=3)
            
            # 标题包含详细相似度信息
            title = f"{match.symbol} {match.timeframe}\n"
            title += f"综合相似度: {match.similarity_score:.3f}"
            ax.set_title(title, fontsize=11, fontweight='bold')
            
            ax.set_xlabel('K线序号 (1-50)')
            ax.set_ylabel('相对变化 (%)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # 添加详细相似度信息
            details = match.similarity_details
            detail_text = f"欧氏: {details['euclidean']:.3f}\n"
            detail_text += f"DTW: {details['dtw']:.3f}\n"
            detail_text += f"相关: {details['pearson']:.3f}\n"
            detail_text += f"余弦: {details['cosine']:.3f}"
            
            ax.text(0.02, 0.02, detail_text, transform=ax.transAxes, fontsize=8,
                   verticalalignment='bottom', 
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # 添加匹配时间信息
            time_text = f"匹配时间:\n{match.start_time.strftime('%m-%d %H:%M')}\n到\n{match.end_time.strftime('%m-%d %H:%M')}"
            ax.text(0.98, 0.98, time_text, transform=ax.transAxes, fontsize=8,
                   verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        # 隐藏多余的子图
        total_subplots = rows * cols
        for i in range(n_matches + 1, total_subplots):
            row = i // cols
            col = i % cols
            if row < rows and col < cols:
                axes[row, col].axis('off')
        
        plt.tight_layout()
        
        # 保存图表
        if not save_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = f"real_pattern_comparison_{timestamp}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 真实形态对比图已保存: {save_path}")
        
        # 显示图表
        plt.show()
        
        return save_path
    
    def print_detailed_results(self, matches: List[PatternMatch]):
        """打印详细的匹配结果"""
        if not matches:
            print("❌ 没有找到相似的形态")
            return
        
        print(f"\n{'='*80}")
        print(f"🎯 真正的K线形态匹配结果 (基于算法计算)")
        print(f"{'='*80}")
        print(f"基准: {self.silver_symbol} {self.silver_timeframe} 最后{self.silver_bars}根K线")
        print(f"算法: 欧氏距离 + DTW + 皮尔逊相关 + 余弦相似度")
        print(f"结果: 找到 {len(matches)} 个最相似形态")
        print(f"{'='*80}")
        
        print(f"\n📊 详细匹配结果:")
        print("-" * 80)
        print(f"{'排名':<4} {'品种':<8} {'时间框架':<6} {'综合':<6} {'欧氏':<6} {'DTW':<6} {'相关':<6} {'余弦':<6} {'时间段'}")
        print("-" * 80)
        
        for i, match in enumerate(matches, 1):
            details = match.similarity_details
            time_range = f"{match.start_time.strftime('%m-%d %H:%M')} ~ {match.end_time.strftime('%m-%d %H:%M')}"
            
            print(f"{i:<4} {match.symbol:<8} {match.timeframe:<6} "
                  f"{details['combined']:<6.3f} {details['euclidean']:<6.3f} "
                  f"{details['dtw']:<6.3f} {details['pearson']:<6.3f} "
                  f"{details['cosine']:<6.3f} {time_range}")
        
        # 最佳匹配详情
        if matches:
            best = matches[0]
            print(f"\n🏆 最佳匹配详情:")
            print(f"   品种: {best.symbol} {best.timeframe}")
            print(f"   综合相似度: {best.similarity_details['combined']:.4f}")
            print(f"   时间段: {best.start_time} 到 {best.end_time}")
            print(f"   算法分解:")
            print(f"     • 欧氏距离相似度: {best.similarity_details['euclidean']:.4f} (形状相似性)")
            print(f"     • DTW相似度: {best.similarity_details['dtw']:.4f} (允许时间拉伸)")
            print(f"     • 皮尔逊相关: {best.similarity_details['pearson']:.4f} (趋势一致性)")
            print(f"     • 余弦相似度: {best.similarity_details['cosine']:.4f} (方向相似性)")


def main():
    """主函数"""
    print("🔍 真正的K线形态匹配可视化工具")
    print("=" * 60)
    print("基于算法: 欧氏距离 + DTW + 皮尔逊相关 + 余弦相似度")
    print("数据来源: 本地缓存数据")
    print("=" * 60)
    
    matcher = RealPatternMatcher()
    
    try:
        while True:
            print(f"\n选择功能:")
            print("1. 运行真正的形态匹配分析")
            print("2. 生成形态对比可视化图")
            print("3. 查看本地数据状态")
            print("4. 退出")
            
            choice = input("\n请选择 (1-4): ").strip()
            
            if choice == '1':
                print("\n🔍 开始真正的形态匹配分析...")
                
                # 运行匹配
                matches = matcher.run_pattern_matching(top_n=10)
                
                # 显示结果
                matcher.print_detailed_results(matches)
                
                # 保存到全局变量供可视化使用
                globals()['latest_matches'] = matches
                
            elif choice == '2':
                if 'latest_matches' not in globals():
                    print("❌ 请先运行形态匹配分析 (选项1)")
                    continue
                
                print("\n📊 生成形态对比可视化图...")
                
                # 让用户选择显示多少个匹配结果
                total_matches = len(globals()['latest_matches'])
                print(f"共找到 {total_matches} 个匹配结果")
                
                while True:
                    try:
                        num_display = input(f"显示前几个匹配结果? (1-{min(total_matches, 15)}, 默认8): ").strip()
                        if not num_display:
                            num_display = 8
                        else:
                            num_display = int(num_display)
                        
                        if 1 <= num_display <= min(total_matches, 15):
                            break
                        else:
                            print(f"❌ 请输入1到{min(total_matches, 15)}之间的数字")
                    except ValueError:
                        print("❌ 请输入有效数字")
                
                # 生成图表
                selected_matches = globals()['latest_matches'][:num_display]
                chart_path = matcher.create_comparison_chart(selected_matches)
                
                if chart_path:
                    print(f"🎉 可视化图表已生成: {chart_path}")
                    print(f"📊 显示了前 {len(selected_matches)} 个最相似的形态")
                
            elif choice == '3':
                print("\n📊 本地数据状态:")
                matcher.data_manager.print_data_summary()
                
            elif choice == '4':
                print("👋 再见!")
                break
                
            else:
                print("❌ 无效选择")
                
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 程序错误: {e}")
        logger.error(f"程序运行错误: {e}")


if __name__ == "__main__":
    main()