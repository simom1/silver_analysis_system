"""
测试形态匹配算法，诊断为什么找不到相似形态
"""

import sys
import os
import warnings

# 过滤numpy的警告
warnings.filterwarnings('ignore', category=RuntimeWarning, module='numpy')
warnings.filterwarnings('ignore', message='Degrees of freedom <= 0 for slice')
warnings.filterwarnings('ignore', message='divide by zero encountered')
warnings.filterwarnings('ignore', message='invalid value encountered')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.improved_pattern_matcher import ImprovedPatternMatcher
import numpy as np

def test_pattern_matching():
    """测试形态匹配"""
    print("=" * 80)
    print("🔍 形态匹配算法诊断测试")
    print("=" * 80)
    
    matcher = ImprovedPatternMatcher()
    
    # 1. 获取白银数据
    print("\n📊 步骤1: 获取白银基准数据")
    silver_data_full = matcher.data_manager.get_data('XAGUSD', 'H4', count=50)
    
    if silver_data_full is None or len(silver_data_full) < 50:
        print("❌ 无法获取白银数据")
        return
    
    # 只取最后50根K线
    silver_data = silver_data_full.iloc[-50:]
    
    print(f"✅ 白银数据: {len(silver_data)} 根K线（最新50根）")
    print(f"   时间范围: {silver_data.index[0]} 到 {silver_data.index[-1]}")
    print(f"   价格范围: {silver_data['close'].min():.2f} - {silver_data['close'].max():.2f}")
    print(f"   起始价格: {silver_data['close'].iloc[0]:.2f}")
    print(f"   结束价格: {silver_data['close'].iloc[-1]:.2f}")
    
    total_return = (silver_data['close'].iloc[-1] - silver_data['close'].iloc[0]) / silver_data['close'].iloc[0]
    print(f"   总涨跌幅: {total_return:.2%}")
    
    # 2. 标准化和提取特征
    print("\n📊 步骤2: 标准化和特征提取")
    silver_pattern = matcher.normalize_pattern_zscore(silver_data['close'])
    silver_features = matcher.extract_pattern_features(silver_data)
    
    print(f"✅ 标准化完成")
    print(f"   Z-score范围: {silver_pattern.min():.3f} 到 {silver_pattern.max():.3f}")
    print(f"   Z-score均值: {silver_pattern.mean():.6f} (应该接近0)")
    print(f"   Z-score标准差: {silver_pattern.std():.6f} (应该接近1)")
    
    print(f"\n✅ 特征提取完成")
    for key, value in silver_features.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.6f}")
        else:
            print(f"   {key}: {value}")
    
    # 3. 测试一个品种
    print("\n📊 步骤3: 测试黄金(XAUUSD) H4 匹配")
    gold_data = matcher.data_manager.get_data('XAUUSD', 'H4', count=1000)
    
    if gold_data is None:
        print("❌ 无法获取黄金数据")
        return
    
    print(f"✅ 黄金数据: {len(gold_data)} 根K线")
    print(f"   时间范围: {gold_data.index[0]} 到 {gold_data.index[-1]}")
    
    # 4. 手动测试几个窗口
    print("\n📊 步骤4: 手动测试前5个窗口的相似度")
    print("-" * 80)
    print(f"{'窗口':<6} {'时间范围':<35} {'形状':<8} {'趋势':<8} {'波动':<8} {'综合':<8}")
    print("-" * 80)
    
    for i in range(0, min(5, len(gold_data) - 50), 10):
        window_data = gold_data.iloc[i:i + 50]
        window_pattern = matcher.normalize_pattern_zscore(window_data['close'])
        window_features = matcher.extract_pattern_features(window_data)
        
        shape_sim = matcher.calculate_shape_similarity(silver_pattern, window_pattern)
        trend_sim = matcher.calculate_trend_similarity(silver_features, window_features)
        vol_sim = matcher.calculate_volatility_similarity(silver_features, window_features)
        
        combined = shape_sim * 0.5 + trend_sim * 0.3 + vol_sim * 0.2
        
        time_range = f"{window_data.index[0].strftime('%m-%d %H:%M')} ~ {window_data.index[-1].strftime('%m-%d %H:%M')}"
        print(f"{i:<6} {time_range:<35} {shape_sim:<8.3f} {trend_sim:<8.3f} {vol_sim:<8.3f} {combined:<8.3f}")
    
    # 5. 搜索最高相似度
    print("\n📊 步骤5: 搜索黄金数据中的最高相似度")
    max_similarity = 0
    max_index = -1
    max_details = {}
    
    step = 10  # 每10根K线测试一次，加快速度
    for i in range(0, len(gold_data) - 50, step):
        window_data = gold_data.iloc[i:i + 50]
        window_pattern = matcher.normalize_pattern_zscore(window_data['close'])
        window_features = matcher.extract_pattern_features(window_data)
        
        shape_sim = matcher.calculate_shape_similarity(silver_pattern, window_pattern)
        trend_sim = matcher.calculate_trend_similarity(silver_features, window_features)
        vol_sim = matcher.calculate_volatility_similarity(silver_features, window_features)
        
        combined = shape_sim * 0.5 + trend_sim * 0.3 + vol_sim * 0.2
        
        if combined > max_similarity:
            max_similarity = combined
            max_index = i
            max_details = {
                'shape': shape_sim,
                'trend': trend_sim,
                'volatility': vol_sim,
                'time_range': f"{window_data.index[0]} ~ {window_data.index[-1]}"
            }
    
    print(f"\n✅ 最高相似度: {max_similarity:.3f}")
    print(f"   位置: 第 {max_index} 根K线")
    print(f"   时间: {max_details['time_range']}")
    print(f"   形状相似度: {max_details['shape']:.3f}")
    print(f"   趋势相似度: {max_details['trend']:.3f}")
    print(f"   波动相似度: {max_details['volatility']:.3f}")
    
    # 6. 诊断结论
    print("\n" + "=" * 80)
    print("📋 诊断结论")
    print("=" * 80)
    
    if max_similarity < 0.3:
        print("❌ 问题严重: 最高相似度 < 0.3")
        print("   可能原因:")
        print("   1. 算法权重设置不合理")
        print("   2. 标准化方法有问题")
        print("   3. 白银形态非常独特")
        print("\n   建议:")
        print("   - 降低最小相似度阈值到 0.2")
        print("   - 调整权重分配")
        print("   - 检查标准化逻辑")
    elif max_similarity < 0.5:
        print("⚠️  相似度偏低: 0.3 <= 最高相似度 < 0.5")
        print("   可能原因:")
        print("   1. 白银当前形态比较独特")
        print("   2. 阈值设置偏高")
        print("\n   建议:")
        print("   - 降低最小相似度阈值到 0.3-0.4")
        print("   - 增加搜索的历史数据量")
    elif max_similarity < 0.7:
        print("✅ 相似度正常: 0.5 <= 最高相似度 < 0.7")
        print("   建议:")
        print("   - 使用默认阈值 0.5")
        print("   - 应该能找到一些相似形态")
    else:
        print("✅ 相似度很高: 最高相似度 >= 0.7")
        print("   建议:")
        print("   - 使用默认阈值 0.5")
        print("   - 应该能找到多个相似形态")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_pattern_matching()
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
