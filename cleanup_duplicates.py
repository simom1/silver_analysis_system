"""
清理重复文件脚本

将旧版本文件移动到 _backup 目录
"""

import os
import shutil
from pathlib import Path

def cleanup_duplicates():
    """清理重复文件"""
    
    base_dir = Path(__file__).parent
    
    # 创建备份目录
    backup_dirs = {
        'core': base_dir / 'core' / '_backup',
        'visualizers': base_dir / 'visualizers' / '_backup'
    }
    
    for dir_path in backup_dirs.values():
        dir_path.mkdir(exist_ok=True)
        print(f"✅ 创建备份目录: {dir_path}")
    
    # 需要移动到备份的文件
    files_to_backup = {
        'core': [
            'silver_pattern_matcher.py',  # 旧版形态匹配
        ],
        'visualizers': [
            'real_pattern_visualizer.py',  # 旧版可视化
            'accurate_pattern_visualizer.py',  # 功能重复
            'pattern_visualizer.py',  # 功能重复
            'quick_chart_generator.py',  # 功能重复
        ]
    }
    
    print("\n" + "=" * 80)
    print("开始清理重复文件...")
    print("=" * 80)
    
    for module, files in files_to_backup.items():
        print(f"\n📁 处理 {module} 目录:")
        
        for filename in files:
            src = base_dir / module / filename
            dst = backup_dirs[module] / filename
            
            if src.exists():
                if dst.exists():
                    print(f"   ⚠️  备份已存在，跳过: {filename}")
                else:
                    try:
                        shutil.move(str(src), str(dst))
                        print(f"   ✅ 已移动: {filename} → _backup/")
                    except Exception as e:
                        print(f"   ❌ 移动失败: {filename} - {e}")
            else:
                print(f"   ℹ️  文件不存在: {filename}")
    
    print("\n" + "=" * 80)
    print("清理完成！")
    print("=" * 80)
    
    print("\n📋 当前推荐使用的文件:")
    print("\n核心模块 (core/):")
    print("  ✅ silver_data_manager.py          - 数据管理")
    print("  ✅ improved_pattern_matcher.py     - 形态匹配（推荐）")
    print("  ✅ silver_correlation_analyzer.py  - 相关性分析")
    print("  ✅ pattern_future_predictor.py     - 未来走势预测")
    print("  ⚠️  enhanced_silver_analyzer.py     - 增强版相关性（可选）")
    
    print("\n可视化模块 (visualizers/):")
    print("  ✅ improved_pattern_visualizer.py  - 形态可视化（推荐）")
    
    print("\n备份文件位置:")
    print("  📦 core/_backup/")
    print("  📦 visualizers/_backup/")
    
    print("\n💡 提示:")
    print("  - 备份文件不会被删除，可以随时恢复")
    print("  - 如需恢复，手动将文件从 _backup 移回原目录")
    print("  - 建议更新 main_launcher.py 使用新版本文件")


if __name__ == "__main__":
    try:
        response = input("确认要清理重复文件吗？(y/N): ").strip().lower()
        if response in ['y', 'yes', '是']:
            cleanup_duplicates()
        else:
            print("❌ 已取消清理")
    except KeyboardInterrupt:
        print("\n❌ 已取消清理")
