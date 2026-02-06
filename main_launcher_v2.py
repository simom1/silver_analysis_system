"""
白银分析系统主启动器 V2

使用改进版算法和可视化工具
"""

import os
import sys
import subprocess
from datetime import datetime

def print_banner():
    """打印系统横幅"""
    print("=" * 80)
    print("🥈 白银分析系统 V2 (Silver Analysis System)")
    print("=" * 80)
    print("版本: v4.1 (改进版)")
    print("功能: 形态匹配 | 相关性分析 | 可视化 | 走势预测")
    print("时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 80)

def check_dependencies():
    """检查依赖"""
    print("\n🔍 检查系统依赖...")
    
    required_modules = [
        'pandas', 'numpy', 'matplotlib', 'MetaTrader5'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - 未安装")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️ 缺少依赖: {', '.join(missing_modules)}")
        print("请运行: pip install pandas numpy matplotlib MetaTrader5")
        return False
    
    print("✅ 所有依赖已满足")
    return True

def run_script(script_name):
    """运行指定脚本"""
    try:
        print(f"\n🚀 启动 {script_name}...")
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 运行失败: {e}")
    except FileNotFoundError:
        print(f"❌ 文件不存在: {script_name}")
    except KeyboardInterrupt:
        print(f"\n⚠️ 用户中断")

def main_menu():
    """主菜单"""
    while True:
        print("\n" + "=" * 80)
        print("🎯 白银分析系统主菜单 V2")
        print("=" * 80)
        
        print("\n📊 核心分析功能:")
        print("1. 形态匹配分析 (Pattern Matching + Visualization) ⭐⭐")
        print("2. 统计相关性分析 (Correlation Analysis)")
        print("3. 未来走势预测 (Future Prediction)")
        
        print("\n🔧 数据和工具:")
        print("4. 更新市场数据 (Update Data)")
        print("5. 查看数据状态 (Data Status)")
        print("6. 系统诊断测试 (Diagnostic Test)")
        
        print("\n🗑️ 维护工具:")
        print("7. 清理重复文件 (Cleanup Duplicates)")
        
        print("\n📋 文档:")
        print("8. 查看算法说明")
        print("9. 查看文件功能说明")
        
        print("\n0. 退出系统")
        
        choice = input("\n请选择功能 (0-9): ").strip()
        
        if choice == '0':
            print("👋 感谢使用白银分析系统！")
            break
            
        elif choice == '1':
            print("\n" + "=" * 80)
            print("📊 形态匹配分析 + 可视化")
            print("=" * 80)
            print("功能:")
            print("  • 找到与白银当前形态相似的历史形态")
            print("  • 显示文字分析报告")
            print("  • 生成形态对比图表")
            print()
            print("特点:")
            print("  • Z-score标准化，更科学")
            print("  • 多维度特征提取")
            print("  • 三维相似度计算（形状、趋势、波动）")
            print("  • 清晰的图表对比")
            print("=" * 80)
            run_script('visualizers/improved_pattern_visualizer.py')
            
        elif choice == '2':
            print("\n" + "=" * 80)
            print("📊 统计相关性分析")
            print("=" * 80)
            print("功能: 计算白银与其他品种的统计相关性")
            print("=" * 80)
            run_script('core/silver_correlation_analyzer.py')
            
        elif choice == '3':
            print("\n" + "=" * 80)
            print("📊 未来走势预测")
            print("=" * 80)
            print("功能: 基于历史相似形态预测未来走势")
            print("=" * 80)
            run_script('core/pattern_future_predictor.py')
            
        elif choice == '4':
            print("\n" + "=" * 80)
            print("🔄 批量更新市场数据")
            print("=" * 80)
            print("功能: 更新所有品种的历史数据")
            print("建议: 每个品种至少获取1000根K线")
            print("=" * 80)
            
            try:
                from core.improved_pattern_matcher import ImprovedPatternMatcher
                matcher = ImprovedPatternMatcher()
                
                print(f"\n检测到 {len(matcher.target_symbols)} 个品种需要更新")
                
                confirm = input("\n确认更新所有品种数据? (y/N): ").strip().lower()
                if confirm in ['y', 'yes', '是']:
                    print("\n开始更新数据...")
                    
                    # 添加白银
                    all_symbols = dict(matcher.target_symbols)
                    all_symbols[matcher.silver_symbol] = [matcher.silver_timeframe]
                    
                    results = matcher.data_manager.batch_update_data(all_symbols, count=5000)
                    
                    print(f"\n📊 更新结果:")
                    success_count = 0
                    fail_count = 0
                    
                    for symbol, symbol_results in results.items():
                        for timeframe, success in symbol_results.items():
                            if success:
                                status = "✅"
                                success_count += 1
                            else:
                                status = "❌"
                                fail_count += 1
                            print(f"{status} {symbol} {timeframe}")
                    
                    print(f"\n总计: 成功 {success_count} 个, 失败 {fail_count} 个")
                else:
                    print("❌ 已取消更新")
                    
            except Exception as e:
                print(f"❌ 更新失败: {e}")
            
        elif choice == '5':
            print("\n" + "=" * 80)
            print("📊 查看数据状态")
            print("=" * 80)
            
            try:
                from core.improved_pattern_matcher import ImprovedPatternMatcher
                matcher = ImprovedPatternMatcher()
                
                print("\n本地数据状态:")
                print("-" * 80)
                print(f"{'品种':<12} {'时间框架':<10} {'数据量':<10} {'状态'}")
                print("-" * 80)
                
                # 检查白银
                silver_data = matcher.data_manager.get_data(matcher.silver_symbol, matcher.silver_timeframe, count=50)
                if silver_data is not None:
                    status = "✅ 充足" if len(silver_data) >= 1000 else f"⚠️  不足"
                    print(f"{matcher.silver_symbol:<12} {matcher.silver_timeframe:<10} {len(silver_data):<10} {status}")
                
                # 检查其他品种
                for symbol, timeframes in matcher.target_symbols.items():
                    for timeframe in timeframes:
                        data = matcher.data_manager.get_data(symbol, timeframe, count=1000)
                        if data is not None:
                            status = "✅ 充足" if len(data) >= 1000 else f"⚠️  不足"
                            print(f"{symbol:<12} {timeframe:<10} {len(data):<10} {status}")
                        else:
                            print(f"{symbol:<12} {timeframe:<10} {'0':<10} ❌ 无数据")
                
                print("-" * 80)
                print("\n💡 提示: 建议每个品种至少有1000根K线数据")
                print("   如果数据不足，请选择功能4更新数据")
                
            except Exception as e:
                print(f"❌ 查看失败: {e}")
            
        elif choice == '6':
            print("\n" + "=" * 80)
            print("🔍 系统诊断测试")
            print("=" * 80)
            print("功能: 测试算法性能，诊断问题")
            print("=" * 80)
            run_script('test_pattern_matching.py')
            
        elif choice == '7':
            print("\n" + "=" * 80)
            print("🗑️ 清理重复文件")
            print("=" * 80)
            print("功能: 将旧版本文件移动到备份目录")
            print("=" * 80)
            run_script('cleanup_duplicates.py')
            
        elif choice == '8':
            print("\n📖 查看算法说明...")
            doc_file = '形态匹配算法说明.md'
            if os.path.exists(doc_file):
                print(f"✅ 文档位置: {doc_file}")
                print("请使用文本编辑器或Markdown查看器打开")
            else:
                print(f"❌ 文档不存在: {doc_file}")
                
        elif choice == '9':
            print("\n📖 查看文件功能说明...")
            doc_file = '文件功能说明.md'
            if os.path.exists(doc_file):
                print(f"✅ 文档位置: {doc_file}")
                print("请使用文本编辑器或Markdown查看器打开")
            else:
                print(f"❌ 文档不存在: {doc_file}")
                
        else:
            print("❌ 无效选择，请重新输入")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("\n⚠️ 请先安装必要的依赖包")
        input("\n按回车键退出...")
        return
    
    # 显示主菜单
    main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
