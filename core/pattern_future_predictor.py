"""
基于形态匹配的未来走势预测工具

分析历史相似形态的后续走势，预测白银未来可能的价格变化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import json
import sys
import os

# 添加父目录到路径，以便导入 metatrader_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据管理器和形态匹配器
from silver_data_manager import DataManager
try:
    from real_pattern_visualizer import RealPatternMatcher, PatternMatch
except ImportError:
    # 如果导入失败，创建简单的替代类
    class PatternMatch:
        def __init__(self, symbol, timeframe, similarity_score, match_method):
            self.symbol = symbol
            self.timeframe = timeframe
            self.similarity_score = similarity_score
            self.match_method = match_method

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FuturePrediction:
    """未来走势预测结果"""
    match: PatternMatch
    future_data: pd.DataFrame
    future_pattern: np.ndarray
    prediction_bars: int
    price_change: float
    max_gain: float
    max_loss: float
    volatility: float
    trend_direction: str


class PatternFuturePredictor:
    """基于形态匹配的未来走势预测器"""
    
    def __init__(self, data_dir: str = "market_data"):
        self.data_manager = DataManager(data_dir)
        self.pattern_matcher = RealPatternMatcher(data_dir)
        
        # 预测参数
        self.prediction_bars = 20  # 预测未来20根K线
        
    def get_future_data_after_match(self, match: PatternMatch, future_bars: int = 20) -> Optional[pd.DataFrame]:
        """
        获取匹配形态之后的未来数据
        
        Args:
            match: 形态匹配结果
            future_bars: 需要的未来K线数量
            
        Returns:
            未来数据DataFrame，如果没有足够数据则返回None
        """
        try:
            # 获取该品种的完整历史数据
            full_data = self.data_manager.get_data(match.symbol, match.timeframe, count=5000)
            
            if full_data is None:
                return None
            
            # 找到匹配结束时间在完整数据中的位置
            match_end_time = match.end_time
            
            # 找到匹配结束后的数据
            future_mask = full_data.index > match_end_time
            future_data = full_data[future_mask]
            
            if len(future_data) < future_bars:
                print(f"⚠️ {match.symbol} {match.timeframe} 匹配后只有 {len(future_data)} 根K线，少于需要的 {future_bars} 根")
                if len(future_data) > 0:
                    return future_data  # 返回现有的数据
                else:
                    return None
            
            # 返回指定数量的未来数据
            return future_data.head(future_bars)
            
        except Exception as e:
            print(f"❌ 获取 {match.symbol} {match.timeframe} 未来数据失败: {e}")
            return None
    
    def analyze_future_pattern(self, future_data: pd.DataFrame, match: PatternMatch) -> FuturePrediction:
        """
        分析未来形态的特征
        
        Args:
            future_data: 未来数据
            match: 原始匹配结果
            
        Returns:
            未来走势预测结果
        """
        if future_data is None or len(future_data) == 0:
            return None
        
        # 标准化未来价格（相对于匹配结束时的价格）
        start_price = match.pattern_data['close'].iloc[-1]  # 匹配形态的最后一个价格
        future_prices = future_data['close']
        future_pattern = ((future_prices - start_price) / start_price * 100).values
        
        # 计算关键指标
        total_change = future_pattern[-1] if len(future_pattern) > 0 else 0
        max_gain = np.max(future_pattern) if len(future_pattern) > 0 else 0
        max_loss = np.min(future_pattern) if len(future_pattern) > 0 else 0
        volatility = np.std(future_pattern) if len(future_pattern) > 1 else 0
        
        # 判断趋势方向
        if total_change > 2:
            trend_direction = "上涨"
        elif total_change < -2:
            trend_direction = "下跌"
        else:
            trend_direction = "震荡"
        
        return FuturePrediction(
            match=match,
            future_data=future_data,
            future_pattern=future_pattern,
            prediction_bars=len(future_pattern),
            price_change=total_change,
            max_gain=max_gain,
            max_loss=max_loss,
            volatility=volatility,
            trend_direction=trend_direction
        )
    
    def predict_future_trends(self, matches: List[PatternMatch], future_bars: int = 20) -> List[FuturePrediction]:
        """
        基于匹配结果预测未来走势
        
        Args:
            matches: 形态匹配结果列表
            future_bars: 预测的未来K线数量
            
        Returns:
            未来走势预测结果列表
        """
        predictions = []
        
        print(f"🔮 开始分析历史相似形态的后续走势...")
        print(f"预测范围: 未来 {future_bars} 根K线")
        print("-" * 60)
        
        for i, match in enumerate(matches, 1):
            print(f"📊 分析第{i}名匹配: {match.symbol} {match.timeframe} (相似度: {match.similarity_score:.3f})")
            
            # 获取未来数据
            future_data = self.get_future_data_after_match(match, future_bars)
            
            if future_data is None:
                print(f"   ❌ 无法获取未来数据")
                continue
            
            # 分析未来走势
            prediction = self.analyze_future_pattern(future_data, match)
            
            if prediction:
                predictions.append(prediction)
                print(f"   ✅ 后续{len(prediction.future_pattern)}根K线: {prediction.trend_direction} {prediction.price_change:+.2f}%")
                print(f"      最大涨幅: +{prediction.max_gain:.2f}%, 最大跌幅: {prediction.max_loss:.2f}%")
            else:
                print(f"   ❌ 分析失败")
        
        print(f"\n📊 成功分析了 {len(predictions)} 个历史形态的后续走势")
        return predictions
    
    def create_prediction_chart(self, predictions: List[FuturePrediction], save_path: Optional[str] = None):
        """
        创建未来走势预测图表
        
        Args:
            predictions: 预测结果列表
            save_path: 保存路径
        """
        if not predictions:
            print("❌ 没有预测结果可以可视化")
            return None
        
        # 获取白银当前形态
        silver_data_full = self.data_manager.get_data('XAGUSD', 'H4', count=5000)
        silver_current = silver_data_full.tail(50)
        silver_pattern = self.pattern_matcher.normalize_price_series(silver_current['close'])
        
        # 创建图表
        n_predictions = min(6, len(predictions))  # 最多显示6个预测
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('基于历史相似形态的白银未来走势预测\n(分析历史形态后续走势，预测白银可能的价格变化)', 
                    fontsize=16, fontweight='bold')
        
        # 第一个图：白银当前形态 + 综合预测
        ax = axes[0, 0]
        
        # 绘制白银当前形态
        current_x = range(len(silver_pattern))
        ax.plot(current_x, silver_pattern, 'b-', linewidth=3, label='白银当前形态', marker='o', markersize=4)
        
        # 计算综合预测
        if predictions:
            # 加权平均预测（相似度越高权重越大）
            weights = np.array([p.match.similarity_score for p in predictions])
            weights = weights / np.sum(weights)
            
            # 找到最长的预测长度
            max_pred_len = max(len(p.future_pattern) for p in predictions)
            
            # 计算加权平均预测
            weighted_prediction = np.zeros(max_pred_len)
            total_weight = 0
            
            for pred, weight in zip(predictions, weights):
                pred_len = len(pred.future_pattern)
                weighted_prediction[:pred_len] += pred.future_pattern * weight
                total_weight += weight
            
            # 绘制预测走势
            future_x = range(len(silver_pattern), len(silver_pattern) + len(weighted_prediction))
            ax.plot(future_x, weighted_prediction, 'r--', linewidth=3, label='综合预测走势', marker='s', markersize=3)
            
            # 连接当前和预测
            ax.plot([len(silver_pattern)-1, len(silver_pattern)], [silver_pattern[-1], weighted_prediction[0]], 'g-', linewidth=2, alpha=0.7)
        
        ax.set_title('白银当前形态 + 综合预测', fontsize=12, fontweight='bold')
        ax.set_xlabel('K线序号')
        ax.set_ylabel('相对变化 (%)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.axvline(x=len(silver_pattern)-1, color='gray', linestyle=':', alpha=0.7, label='预测起点')
        
        # 添加预测统计信息
        if predictions:
            avg_change = np.mean([p.price_change for p in predictions])
            avg_max_gain = np.mean([p.max_gain for p in predictions])
            avg_max_loss = np.mean([p.max_loss for p in predictions])
            
            stats_text = f"基于{len(predictions)}个历史形态:\n"
            stats_text += f"平均变化: {avg_change:+.2f}%\n"
            stats_text += f"平均最大涨幅: +{avg_max_gain:.2f}%\n"
            stats_text += f"平均最大跌幅: {avg_max_loss:.2f}%"
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        # 绘制各个历史预测
        colors = ['red', 'green', 'orange', 'purple', 'brown', 'pink']
        
        for i, prediction in enumerate(predictions[:n_predictions-1]):
            row = (i + 1) // 3
            col = (i + 1) % 3
            
            ax = axes[row, col]
            
            # 绘制匹配的历史形态
            match_pattern = self.pattern_matcher.normalize_price_series(prediction.match.pattern_data['close'])
            match_x = range(len(match_pattern))
            ax.plot(match_x, match_pattern, 'b-', linewidth=2, alpha=0.7, label='历史匹配形态', marker='o', markersize=3)
            
            # 绘制后续走势
            future_x = range(len(match_pattern), len(match_pattern) + len(prediction.future_pattern))
            ax.plot(future_x, prediction.future_pattern, colors[i], linewidth=3, 
                   label=f'后续走势 ({prediction.trend_direction})', marker='s', markersize=3)
            
            # 连接历史和未来
            ax.plot([len(match_pattern)-1, len(match_pattern)], [match_pattern[-1], prediction.future_pattern[0]], 
                   'g-', linewidth=2, alpha=0.7)
            
            # 标题
            title = f"{prediction.match.symbol} {prediction.match.timeframe}\n"
            title += f"相似度: {prediction.match.similarity_score:.3f} | {prediction.trend_direction} {prediction.price_change:+.2f}%"
            ax.set_title(title, fontsize=10, fontweight='bold')
            
            ax.set_xlabel('K线序号')
            ax.set_ylabel('相对变化 (%)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.axvline(x=len(match_pattern)-1, color='gray', linestyle=':', alpha=0.7)
            
            # 添加详细信息
            detail_text = f"时间: {prediction.match.start_time.strftime('%Y-%m-%d')}\n"
            detail_text += f"最大涨幅: +{prediction.max_gain:.2f}%\n"
            detail_text += f"最大跌幅: {prediction.max_loss:.2f}%\n"
            detail_text += f"波动率: {prediction.volatility:.2f}%"
            
            ax.text(0.02, 0.02, detail_text, transform=ax.transAxes, fontsize=8,
                   verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 隐藏多余的子图
        total_subplots = 6
        for i in range(n_predictions, total_subplots):
            row = i // 3
            col = i % 3
            axes[row, col].axis('off')
        
        plt.tight_layout()
        
        # 保存图表
        if not save_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = f"silver_future_prediction_{timestamp}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 未来走势预测图已保存: {save_path}")
        
        # 显示图表
        plt.show()
        
        return save_path
    
    def generate_prediction_report(self, predictions: List[FuturePrediction]) -> str:
        """
        生成预测报告
        
        Args:
            predictions: 预测结果列表
            
        Returns:
            预测报告文本
        """
        if not predictions:
            return "❌ 没有预测结果"
        
        report = []
        report.append("🔮 白银未来走势预测报告")
        report.append("=" * 60)
        report.append(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"基于历史形态数量: {len(predictions)}")
        report.append(f"预测K线数量: {self.prediction_bars}")
        report.append("=" * 60)
        
        # 综合预测
        weights = np.array([p.match.similarity_score for p in predictions])
        weights = weights / np.sum(weights)
        
        weighted_change = np.sum([p.price_change * w for p, w in zip(predictions, weights)])
        weighted_max_gain = np.sum([p.max_gain * w for p, w in zip(predictions, weights)])
        weighted_max_loss = np.sum([p.max_loss * w for p, w in zip(predictions, weights)])
        weighted_volatility = np.sum([p.volatility * w for p, w in zip(predictions, weights)])
        
        # 趋势统计 - 基于相似度加权
        trend_weights = {}
        total_weight = 0
        
        for pred in predictions:
            trend = pred.trend_direction
            weight = pred.match.similarity_score
            
            if trend not in trend_weights:
                trend_weights[trend] = 0
            trend_weights[trend] += weight
            total_weight += weight
        
        # 计算加权概率
        trend_probabilities = {}
        for trend, weight in trend_weights.items():
            trend_probabilities[trend] = (weight / total_weight) * 100
        
        most_likely_trend = max(trend_probabilities, key=trend_probabilities.get)
        trend_probability = trend_probabilities[most_likely_trend]
        
        report.append("\n📊 综合预测结果:")
        report.append("-" * 40)
        report.append(f"最可能趋势: {most_likely_trend} (加权概率: {trend_probability:.1f}%)")
        
        # 显示所有趋势的概率分布
        report.append(f"\n📈 趋势概率分布 (基于相似度加权):")
        for trend, prob in sorted(trend_probabilities.items(), key=lambda x: x[1], reverse=True):
            report.append(f"   • {trend}: {prob:.1f}%")
        
        report.append(f"\n💰 价格变化预测:")
        report.append(f"预期价格变化: {weighted_change:+.2f}%")
        report.append(f"预期最大涨幅: +{weighted_max_gain:.2f}%")
        report.append(f"预期最大跌幅: {weighted_max_loss:.2f}%")
        report.append(f"预期波动率: {weighted_volatility:.2f}%")
        
        # 风险评估
        report.append(f"\n⚠️ 风险评估:")
        if weighted_volatility > 5:
            report.append("• 高波动风险 - 价格可能出现大幅波动")
        elif weighted_volatility > 3:
            report.append("• 中等波动风险 - 价格波动适中")
        else:
            report.append("• 低波动风险 - 价格相对稳定")
        
        if abs(weighted_max_loss) > 5:
            report.append("• 高下跌风险 - 可能出现较大回撤")
        elif abs(weighted_max_loss) > 3:
            report.append("• 中等下跌风险 - 可能出现适度回撤")
        else:
            report.append("• 低下跌风险 - 回撤风险较小")
        
        # 详细历史案例
        report.append(f"\n📋 历史案例详情 (按相似度排序):")
        report.append("-" * 80)
        report.append(f"{'排名':<4} {'品种':<8} {'时间框架':<6} {'相似度':<8} {'权重':<6} {'后续走势':<8} {'最大涨幅':<10} {'最大跌幅':<10}")
        report.append("-" * 80)
        
        total_similarity = sum(p.match.similarity_score for p in predictions)
        for i, pred in enumerate(predictions, 1):
            weight_pct = (pred.match.similarity_score / total_similarity) * 100
            report.append(f"{i:<4} {pred.match.symbol:<8} {pred.match.timeframe:<6} "
                         f"{pred.match.similarity_score:<8.3f} {weight_pct:<6.1f}% {pred.price_change:+8.2f}% "
                         f"+{pred.max_gain:<9.2f}% {pred.max_loss:<10.2f}%")
        
        # 投资建议
        report.append(f"\n💡 投资建议:")
        report.append("-" * 20)
        
        if most_likely_trend == "上涨" and weighted_change > 3:
            report.append("• 建议: 考虑做多白银")
            report.append("• 目标: 关注上涨空间")
            report.append(f"• 止损: 如跌破 {abs(weighted_max_loss):.1f}% 考虑止损")
        elif most_likely_trend == "下跌" and weighted_change < -3:
            report.append("• 建议: 考虑做空白银或观望")
            report.append("• 目标: 关注下跌空间")
            report.append(f"• 止损: 如涨超 {weighted_max_gain:.1f}% 考虑止损")
        else:
            report.append("• 建议: 震荡行情，建议区间操作或观望")
            report.append("• 策略: 高抛低吸，控制仓位")
            report.append("• 风险: 注意突破信号")
        
        report.append(f"\n⚠️ 免责声明:")
        report.append("• 本预测基于历史数据分析，不构成投资建议")
        report.append("• 市场有风险，投资需谨慎")
        report.append("• 请结合其他分析方法和风险管理策略")
        
        return "\n".join(report)
    
    def save_prediction_report(self, predictions: List[FuturePrediction], filename: Optional[str] = None):
        """保存预测报告"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"silver_prediction_report_{timestamp}.txt"
        
        report = self.generate_prediction_report(predictions)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 预测报告已保存: {filename}")
            return filename
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
            return None


def main():
    """主函数"""
    print("🔮 基于形态匹配的白银未来走势预测工具")
    print("=" * 60)
    print("功能: 分析历史相似形态的后续走势，预测白银未来价格变化")
    print("=" * 60)
    
    predictor = PatternFuturePredictor()
    
    try:
        while True:
            print(f"\n选择功能:")
            print("1. 运行完整预测分析 (形态匹配 + 走势预测)")
            print("2. 基于已有匹配结果进行预测")
            print("3. 生成预测可视化图表")
            print("4. 生成预测报告")
            print("5. 退出")
            
            choice = input("\n请选择 (1-5): ").strip()
            
            if choice == '1':
                print("\n🔍 第一步: 运行形态匹配分析...")
                
                # 运行形态匹配
                matches = predictor.pattern_matcher.run_pattern_matching(top_n=10)
                
                if not matches:
                    print("❌ 没有找到相似形态，无法进行预测")
                    continue
                
                print("\n🔮 第二步: 分析历史形态的后续走势...")
                
                # 预测未来走势
                future_bars = int(input("预测未来多少根K线? (默认20): ") or "20")
                predictions = predictor.predict_future_trends(matches, future_bars)
                
                if predictions:
                    # 显示预测报告
                    report = predictor.generate_prediction_report(predictions)
                    print(f"\n{report}")
                    
                    # 保存结果
                    globals()['latest_predictions'] = predictions
                    
                    # 询问是否保存报告
                    save_report = input("\n是否保存预测报告? (y/N): ").strip().lower()
                    if save_report in ['y', 'yes', '是']:
                        predictor.save_prediction_report(predictions)
                else:
                    print("❌ 无法生成预测结果")
                
            elif choice == '2':
                print("❌ 此功能需要先运行选项1")
                
            elif choice == '3':
                if 'latest_predictions' not in globals():
                    print("❌ 请先运行预测分析 (选项1)")
                    continue
                
                print("\n📊 生成预测可视化图表...")
                chart_path = predictor.create_prediction_chart(globals()['latest_predictions'])
                
                if chart_path:
                    print(f"🎉 预测图表已生成: {chart_path}")
                
            elif choice == '4':
                if 'latest_predictions' not in globals():
                    print("❌ 请先运行预测分析 (选项1)")
                    continue
                
                print("\n📄 生成预测报告...")
                report_path = predictor.save_prediction_report(globals()['latest_predictions'])
                
                if report_path:
                    print(f"🎉 预测报告已生成: {report_path}")
                
            elif choice == '5':
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