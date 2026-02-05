"""
安装可视化依赖包
"""

import subprocess
import sys


def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    """主函数"""
    print("📦 安装可视化依赖包")
    print("=" * 40)
    
    packages = [
        "matplotlib",
        "numpy", 
        "pandas"
    ]
    
    for package in packages:
        print(f"安装 {package}...", end=" ")
        
        if install_package(package):
            print("✅ 成功")
        else:
            print("❌ 失败")
    
    print(f"\n🎉 依赖包安装完成！")
    print("现在可以使用可视化功能了")


if __name__ == "__main__":
    main()