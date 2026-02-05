"""
🥈 白银分析系统主启动器

集成所有白银分析功能的统一入口
"""

import os
import sys
import subprocess
from datetime import datetime

def print_banner():
    """打印系统横幅"""
    print("=" * 80)
    print("🥈 白银分析系统 (Silver Analysis System)")
    print("=" * 80)
    print("版本: v4.0")
    print("功能: 统计分析 | 形态匹配 | 可视化 | 走势预测")
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
        print("请运行: pip install -r requirements_silver.txt")
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

def main_menu():
    """主菜单"""
    while True:
        print("\n" + "=" * 60)
        print("🎯 白银分析系统主菜单")
        print("=" * 60)
        
        print("\n📊 核心分析功能:")
        print("1. 统计相关性分析 (Correlation Analysis)")
        print("2. K线形态匹配 (Pattern Matching)")
        print("3. 快速形态匹配 (Quick Pattern Finder)")
        print("4. 未来走势预测 (Future Prediction)")
        
        print("\n📈 可视化功能:")
        print("5. 真实形态可视化 (Real Pattern Visualizer)")
        print("6. 快速图表生成 (Quick Chart Generator)")
        print("7. 形态对比可视化 (Pattern Comparison)")
        
        print("\n🔧 工具和设置:")
        print("8. 数据管理器 (Data Manager)")
        print("9. 安装可视化依赖 (Install Visualization)")
        print("10. 系统状态检查 (System Check)")
        
        print("\n📋 文档和帮助:")
        print("11. 查看使用说明")
        print("12. 查看分析方法对比")
        print("13. 查看可视化功能说明")
        
        print("\n0. 退出系统")
        
        choice = input("\n请选择功能 (0-13): ").strip()
        
        if choice == '0':
            print("👋 感谢使用白银分析系统！")
            break
            
        elif choice == '1':
            run_script('core/silver_correlation_analyzer.py')
            
        elif choice == '2':
            run_script('core/silver_pattern_matcher.py')
            
        elif choice == '3':
            run_script('tools/quick_pattern_finder.py')
            
        elif choice == '4':
            run_script('core/pattern_future_predictor.py')
            
        elif choice == '5':
            run_script('visualizers/real_pattern_visualizer.py')
            
        elif choice == '6':
            run_script('visualizers/quick_chart_generator.py')
            
        elif choice == '7':
            run_script('visualizers/pattern_visualizer.py')
            
        elif choice == '8':
            print("\n📊 数据管理功能:")
            print("数据管理器集成在各个分析工具中")
            print("可以通过各个分析工具的菜单访问数据管理功能")
            
        elif choice == '9':
            run_script('tools/install_visualization.py')
            
        elif choice == '10':
            check_dependencies()
            print("\n📁 检查文件完整性...")
            
            core_files = [
                'core/silver_correlation_analyzer.py',
                'core/silver_pattern_matcher.py', 
                'core/silver_data_manager.py',
                'core/pattern_future_predictor.py',
                'visualizers/real_pattern_visualizer.py'
            ]
            
            for file in core_files:
                if os.path.exists(file):
                    print(f"✅ {file}")
                else:
                    print(f"❌ {file} - 文件缺失")
            
        elif choice == '11':
            print("\n📖 使用说明文档:")
            docs = [
                'README.md',
                'docs/白银相关性分析使用说明.md',
                'docs/白银相关性分析使用说明_v2.md',
                'docs/白银相关性分析说明_最终版.md'
            ]
            
            for doc in docs:
                if os.path.exists(doc):
                    print(f"📄 {doc}")
                    
        elif choice == '12':
            if os.path.exists('分析方法对比说明.md'):
                print("\n📊 分析方法对比说明:")
                print("请查看文件: 分析方法对比说明.md")
            else:
                print("❌ 分析方法对比说明文件不存在")
                
        elif choice == '13':
            if os.path.exists('可视化功能使用说明.md'):
                print("\n📈 可视化功能说明:")
                print("请查看文件: 可视化功能使用说明.md")
            else:
                print("❌ 可视化功能说明文件不存在")
                
        else:
            print("❌ 无效选择，请重新输入")

def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("\n⚠️ 请先安装必要的依赖包")
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