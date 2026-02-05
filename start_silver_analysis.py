"""
白银相关性分析 - 快速启动脚本

一键启动白银相关性分析，自动处理数据获取和分析
"""

import sys
import os
from datetime import datetime
import logging

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from silver_data_manager import DataManager
    from silver_correlation_analyzer import SilverCorrelationAnalyzer
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保所有必要的文件都在同一目录下")
    sys.exit(1)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def quick_analysis():
    """快速分析"""
    print("🚀 白银相关性快速分析")
    print("=" * 50)
    print("检测标的: XAGUSD 4小时图 最后50根K线")
    print("对比品种: 多品种大数据量分析")
    print("=" * 50)
    
    try:
        # 创建分析器
        analyzer = SilverCorrelationAnalyzer()
        
        print("📊 检查本地数据状态...")
        data_summary = analyzer.data_manager.get_data_summary()
        
        if data_summary['total_files'] == 0:
            print("📥 首次运行，需要下载数据...")
            force_refresh = True
        else:
            print(f"✅ 发现 {data_summary['total_files']} 个本地数据文件")
            
            # 检查数据是否需要更新
            user_input = input("是否强制刷新数据? (y/N): ").strip().lower()
            force_refresh = user_input in ['y', 'yes', '是']
        
        # 运行分析
        print(f"\n🔍 开始分析...")
        results = analyzer.run_full_analysis(force_refresh=force_refresh)
        
        if not results:
            print("❌ 没有获得有效的分析结果")
            return
        
        # 显示结果
        analyzer.print_results(results, top_n=8)
        
        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"silver_analysis_{timestamp}.json"
        analyzer.save_results_to_json(results, filename)
        
        # 显示交易建议
        suggestions = analyzer.get_trading_suggestions(results)
        print(f"\n{'='*80}")
        print("💡 交易建议:")
        print("=" * 80)
        for suggestion in suggestions:
            print(suggestion)
        
        print(f"\n✅ 分析完成！结果已保存到: {filename}")
        
    except Exception as e:
        logger.error(f"分析失败: {e}")
        print(f"❌ 分析失败: {e}")
        
        # 提供故障排除建议
        print(f"\n🔧 故障排除建议:")
        print("1. 确保MT5终端已启动并登录")
        print("2. 检查网络连接")
        print("3. 确认账户有相关品种的访问权限")
        print("4. 查看日志文件获取详细错误信息")


def data_management():
    """数据管理"""
    print("📊 数据管理工具")
    print("=" * 30)
    
    try:
        data_manager = DataManager()
        
        while True:
            print(f"\n数据管理选项:")
            print("1. 查看数据状态")
            print("2. 更新所有数据")
            print("3. 清理旧数据")
            print("4. 返回主菜单")
            
            choice = input("\n请选择 (1-4): ").strip()
            
            if choice == '1':
                data_manager.print_data_summary()
                
            elif choice == '2':
                symbols_config = {
                    'XAGUSD': ['H4'],  # 白银4小时 - 检测标的
                    'XAUUSD': ['H1', 'H4'],  # 黄金
                    'XTIUSD': ['H1', 'H4'],  # WTI原油
                    'XBRUSD': ['H1', 'H4'],  # 布伦特原油
                    'US500': ['H1', 'H4'],   # 标普500
                    'US30': ['H1', 'H4'],    # 道琼斯
                    'NAS100': ['H1', 'H4'],  # 纳斯达克100
                    'EURUSD': ['H1', 'H4'],  # 欧元美元
                    'GBPUSD': ['H1', 'H4'],  # 英镑美元
                }
                
                print("🔄 更新所有数据...")
                results = data_manager.batch_update_data(symbols_config, count=5000)
                
                print(f"\n📊 更新结果:")
                for symbol, symbol_results in results.items():
                    for timeframe, success in symbol_results.items():
                        status = "✅" if success else "❌"
                        print(f"{status} {symbol} {timeframe}")
                
            elif choice == '3':
                days = input("清理几天前的数据 (默认7天): ").strip()
                try:
                    days = int(days) if days else 7
                    data_manager.clean_old_data(days)
                    print("✅ 清理完成")
                except ValueError:
                    print("❌ 无效的天数")
                
            elif choice == '4':
                break
                
            else:
                print("❌ 无效选择")
                
    except Exception as e:
        logger.error(f"数据管理失败: {e}")
        print(f"❌ 数据管理失败: {e}")


def main():
    """主函数"""
    print("🥈 白银相关性分析系统")
    print("=" * 50)
    print("版本: 2.0 (支持本地数据缓存)")
    print("检测标的: XAGUSD 4小时图 最后50根K线")
    print("对比品种: 多品种多时间框架大数据分析")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        while True:
            print(f"\n主菜单:")
            print("1. 🚀 快速分析 (推荐)")
            print("2. 📊 数据管理")
            print("3. 🔍 K线形态匹配 (新功能)")
            print("4. 📖 查看帮助")
            print("5. 🚪 退出")
            
            choice = input("\n请选择 (1-5): ").strip()
            
            if choice == '1':
                quick_analysis()
                
            elif choice == '2':
                data_management()
                
            elif choice == '3':
                pattern_matching_menu()
                
            elif choice == '4':
                show_help()
                
            elif choice == '5':
                print("👋 感谢使用白银相关性分析系统！")
                break
                
            else:
                print("❌ 无效选择，请重新输入")
                
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        logger.error(f"程序运行错误: {e}")
        print(f"❌ 程序错误: {e}")


def pattern_matching_menu():
    """K线形态匹配菜单"""
    print("\n🔍 K线形态匹配")
    print("=" * 30)
    print("功能: 找到与白银4H最后50根K线形态最相似的其他品种K线段")
    
    while True:
        print(f"\n形态匹配选项:")
        print("1. 快速形态匹配")
        print("2. 详细形态分析")
        print("3. 📊 生成可视化对比图")
        print("4. 返回主菜单")
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == '1':
            try:
                print("\n🔍 启动快速形态匹配...")
                import subprocess
                subprocess.run(["python", "quick_pattern_finder.py"])
            except Exception as e:
                print(f"❌ 启动失败: {e}")
                
        elif choice == '2':
            try:
                print("\n🔍 启动详细形态分析...")
                import subprocess
                subprocess.run(["python", "silver_pattern_matcher.py"])
            except Exception as e:
                print(f"❌ 启动失败: {e}")
                
        elif choice == '3':
            visualization_menu()
                
        elif choice == '4':
            break
            
        else:
            print("❌ 无效选择")


def visualization_menu():
    """可视化菜单"""
    print("\n📊 形态可视化工具")
    print("=" * 30)
    
    while True:
        print(f"\n可视化选项:")
        print("1. 快速生成前5名对比图")
        print("2. 生成单个品种详细对比图")
        print("3. 启动完整可视化工具")
        print("4. 返回上级菜单")
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == '1':
            try:
                print("\n📊 生成前5名最相似形态对比图...")
                import subprocess
                result = subprocess.run(["python", "-c", 
                    "from quick_chart_generator import generate_top_matches_chart; generate_top_matches_chart()"],
                    capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ 对比图生成成功！")
                else:
                    print(f"❌ 生成失败: {result.stderr}")
            except Exception as e:
                print(f"❌ 启动失败: {e}")
                print("请确保已安装matplotlib: pip install matplotlib")
                
        elif choice == '2':
            symbol = input("请输入品种代码 (如 XBRUSD): ").strip().upper()
            timeframe = input("请输入时间框架 (如 H4): ").strip().upper()
            
            if symbol and timeframe:
                try:
                    print(f"\n📊 生成 {symbol} {timeframe} 详细对比图...")
                    import subprocess
                    result = subprocess.run(["python", "-c", 
                        f"from quick_chart_generator import generate_single_comparison; generate_single_comparison('{symbol}', '{timeframe}')"],
                        capture_output=True, text=True)
                    if result.returncode == 0:
                        print("✅ 详细对比图生成成功！")
                    else:
                        print(f"❌ 生成失败: {result.stderr}")
                except Exception as e:
                    print(f"❌ 生成失败: {e}")
            else:
                print("❌ 请输入有效的品种代码和时间框架")
                
        elif choice == '3':
            try:
                print("\n📊 启动完整可视化工具...")
                import subprocess
                subprocess.run(["python", "pattern_visualizer.py"])
            except Exception as e:
                print(f"❌ 启动失败: {e}")
                
        elif choice == '4':
            break
            
        else:
            print("❌ 无效选择")


def show_help():
    """显示帮助信息"""
    print(f"\n📖 白银相关性分析系统帮助")
    print("=" * 50)
    
    print(f"\n🎯 功能说明:")
    print("• 统计相关性分析: 分析白银4H与其他金融产品的相关性")
    print("• K线形态匹配: 找到与白银4H最后50根K线形态最相似的K线段")
    print("• 检测标的: XAGUSD 4小时图 最后50根K线")
    print("• 对比品种: 黄金、原油、股指等多个品种")
    print("• 支持1小时、4小时、日线等多个时间框架")
    print("• 自动缓存数据，提高分析效率")
    
    print(f"\n📊 分析品种:")
    print("• XAGUSD - 白银 4小时图 (检测标的)")
    print("• XAUUSD - 黄金 1小时图")
    print("• USOIL - WTI原油 1小时、4小时图")
    print("• UKOUSD - 布伦特原油 1小时、4小时图")
    print("• SPX500 - 标普500指数 1小时、4小时、日线")
    print("• US30 - 道琼斯指数 1小时、4小时、日线")
    print("• NAS100 - 纳斯达克100指数 1小时、4小时、日线")
    
    print(f"\n⏰ 时间框架:")
    print("• H1 - 1小时")
    print("• H4 - 4小时")
    print("• D1 - 日线")
    
    print(f"\n📈 相关性解读:")
    print("• 强相关 (|r| ≥ 0.7): 两品种高度同步")
    print("• 中等相关 (0.5 ≤ |r| < 0.7): 有一定关联")
    print("• 弱相关 (0.3 ≤ |r| < 0.5): 关联较弱")
    print("• 几乎无关 (|r| < 0.3): 基本无关联")
    
    print(f"\n💡 使用建议:")
    print("• 首次使用选择'快速分析'")
    print("• 定期更新数据以获得最新结果")
    print("• 结合技术分析和基本面分析")
    print("• 严格执行风险管理")
    
    print(f"\n⚠️ 注意事项:")
    print("• 需要MT5终端运行并登录")
    print("• 确保有相关品种的访问权限")
    print("• 相关性会随市场环境变化")
    print("• 相关性不等于因果关系")


if __name__ == "__main__":
    main()