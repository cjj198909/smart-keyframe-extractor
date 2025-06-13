#!/usr/bin/env python3
"""
依赖包更新脚本
Update Dependencies Script

自动检查和更新项目依赖包到最新稳定版本
"""

import subprocess
import sys
import pkg_resources
from typing import Dict, List, Tuple

class DependencyUpdater:
    """依赖包更新器"""
    
    def __init__(self):
        self.critical_packages = [
            'opencv-python',
            'numpy', 
            'Pillow',
            'requests'
        ]
        
        self.security_packages = [
            'azure-identity',
            'azure-core',
            'azure-storage-blob',
            'boto3',
            'botocore',
            'openai',
            'cryptography',
            'urllib3',
            'certifi'
        ]
        
        self.optional_packages = [
            'google-cloud-storage',
            'google-api-core'
        ]
    
    def get_installed_version(self, package: str) -> str:
        """获取已安装包的版本"""
        try:
            return pkg_resources.get_distribution(package).version
        except pkg_resources.DistributionNotFound:
            return "未安装"
    
    def get_latest_version(self, package: str) -> str:
        """获取包的最新版本"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'index', 'versions', package],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Available versions:' in line:
                        versions = line.split(':')[1].strip().split(',')
                        return versions[0].strip() if versions else 'Unknown'
            return 'Unknown'
        except Exception:
            return 'Unknown'
    
    def check_package_status(self, packages: List[str]) -> List[Tuple[str, str, str, str]]:
        """检查包状态"""
        results = []
        for package in packages:
            installed = self.get_installed_version(package)
            latest = self.get_latest_version(package)
            
            if installed == "未安装":
                status = "❌ 未安装"
            elif installed == latest:
                status = "✅ 最新"
            elif latest == "Unknown":
                status = "⚠️ 无法检查"
            else:
                status = "🔄 可更新"
            
            results.append((package, installed, latest, status))
        
        return results
    
    def update_packages(self, packages: List[str], force: bool = False) -> bool:
        """更新包"""
        if not packages:
            return True
            
        try:
            cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade']
            if force:
                cmd.append('--force-reinstall')
            cmd.extend(packages)
            
            print(f"🔄 正在更新包: {', '.join(packages)}")
            result = subprocess.run(cmd, check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False
    
    def run_update_check(self):
        """运行更新检查"""
        print("🔍 Smart Keyframe Extractor - 依赖包更新检查")
        print("=" * 60)
        
        # 检查核心包
        print("\n📦 核心依赖包:")
        critical_results = self.check_package_status(self.critical_packages)
        for pkg, installed, latest, status in critical_results:
            print(f"  {pkg:<20} {installed:<15} → {latest:<15} {status}")
        
        # 检查安全包
        print("\n🛡️ 安全相关包:")
        security_results = self.check_package_status(self.security_packages)
        for pkg, installed, latest, status in security_results:
            print(f"  {pkg:<20} {installed:<15} → {latest:<15} {status}")
        
        # 检查可选包
        print("\n🌐 可选依赖包:")
        optional_results = self.check_package_status(self.optional_packages)
        for pkg, installed, latest, status in optional_results:
            print(f"  {pkg:<20} {installed:<15} → {latest:<15} {status}")
        
        # 统计需要更新的包
        all_results = critical_results + security_results + optional_results
        needs_update = [pkg for pkg, _, _, status in all_results if "可更新" in status]
        critical_updates = [pkg for pkg, _, _, status in critical_results if "可更新" in status]
        security_updates = [pkg for pkg, _, _, status in security_results if "可更新" in status]
        
        print(f"\n📊 更新统计:")
        print(f"  总共需要更新: {len(needs_update)} 个包")
        print(f"  核心包更新: {len(critical_updates)} 个")
        print(f"  安全包更新: {len(security_updates)} 个")
        
        return needs_update, critical_updates, security_updates
    
    def interactive_update(self):
        """交互式更新"""
        needs_update, critical_updates, security_updates = self.run_update_check()
        
        if not needs_update:
            print("\n✅ 所有包都是最新版本！")
            return
        
        print(f"\n🤔 发现 {len(needs_update)} 个包可以更新")
        
        # 推荐更新安全相关包
        if security_updates:
            print(f"\n⚠️ 强烈建议更新安全相关包: {', '.join(security_updates)}")
            choice = input("是否立即更新安全包? (y/n): ").lower()
            if choice in ['y', 'yes']:
                success = self.update_packages(security_updates)
                if success:
                    print("✅ 安全包更新完成")
                else:
                    print("❌ 安全包更新失败")
        
        # 询问是否更新所有包
        if needs_update:
            print(f"\n📦 所有可更新的包: {', '.join(needs_update)}")
            choice = input("是否更新所有包? (y/n): ").lower()
            if choice in ['y', 'yes']:
                success = self.update_packages(needs_update)
                if success:
                    print("✅ 所有包更新完成")
                    print("\n🔄 建议重启应用以使用新版本")
                else:
                    print("❌ 包更新失败")

def main():
    """主函数"""
    updater = DependencyUpdater()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        # 自动更新模式（仅安全包）
        needs_update, critical_updates, security_updates = updater.run_update_check()
        if security_updates:
            print(f"\n🔄 自动更新安全包: {', '.join(security_updates)}")
            success = updater.update_packages(security_updates)
            if success:
                print("✅ 安全包自动更新完成")
            else:
                print("❌ 安全包自动更新失败")
        else:
            print("\n✅ 安全包都是最新版本")
    else:
        # 交互式更新模式
        updater.interactive_update()

if __name__ == "__main__":
    main()
