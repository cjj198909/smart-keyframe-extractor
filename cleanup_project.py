#!/usr/bin/env python3
"""
项目文件清理脚本
Project File Cleanup Script

清理不需要的文件，优化项目结构
"""

import os
import shutil
import glob
from pathlib import Path
from typing import List, Dict, Tuple

class ProjectCleaner:
    """项目清理器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.removed_files = []
        self.removed_dirs = []
        self.kept_files = []
        
    def get_cleanup_targets(self) -> Dict[str, List[str]]:
        """获取清理目标"""
        return {
            # 临时文件和缓存
            "temp_files": [
                "**/__pycache__",
                "**/*.pyc", 
                "**/*.pyo",
                "**/*.pyd",
                "**/.pytest_cache",
                "**/cache",
                "**/*.tmp",
                "**/*.temp",
                "**/.DS_Store",
                "**/Thumbs.db"
            ],
            
            # 构建产物
            "build_artifacts": [
                "build/",
                "dist/", 
                "*.egg-info/",
                ".eggs/"
            ],
            
            # 测试结果文件（但保留重要报告）
            "test_results": [
                "stress_test_*.log",
                "benchmark_results/*.json",
                "benchmark_results/*.csv", 
                "test_auto_results/*.json",
                "test_auto_results/*.csv"
            ],
            
            # 测试输出目录（保留最新的示例）
            "test_outputs": [
                "output_*/"
            ],
            
            # 重复的文档文件
            "duplicate_docs": [
                "*_TEST_REPORT.md",
                "*_COMPLETION_*.md",
                "ITERATION_*.md"
            ],
            
            # 空目录
            "empty_dirs": []
        }
    
    def scan_files(self) -> Dict[str, List[Path]]:
        """扫描需要清理的文件"""
        targets = self.get_cleanup_targets()
        found_files = {}
        
        for category, patterns in targets.items():
            found_files[category] = []
            
            for pattern in patterns:
                if pattern.endswith('/'):
                    # 目录模式
                    for path in self.project_root.rglob(pattern.rstrip('/')):
                        if path.is_dir():
                            found_files[category].append(path)
                else:
                    # 文件模式
                    for path in self.project_root.rglob(pattern):
                        if path.is_file():
                            found_files[category].append(path)
        
        # 查找空目录
        for path in self.project_root.rglob('*'):
            if path.is_dir() and not any(path.iterdir()):
                found_files["empty_dirs"].append(path)
        
        return found_files
    
    def analyze_cleanup(self) -> Dict[str, Dict]:
        """分析清理情况"""
        found_files = self.scan_files()
        analysis = {}
        
        for category, files in found_files.items():
            total_size = 0
            file_count = len(files)
            
            for file_path in files:
                if file_path.exists():
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                    elif file_path.is_dir():
                        total_size += sum(f.stat().st_size for f in file_path.rglob('*') if f.is_file())
            
            analysis[category] = {
                'files': files,
                'count': file_count,
                'size_mb': total_size / (1024 * 1024),
                'size_bytes': total_size
            }
        
        return analysis
    
    def should_keep_file(self, file_path: Path) -> bool:
        """判断是否应该保留文件"""
        # 保留重要的文档
        important_docs = [
            'README.md',
            'LICENSE', 
            'AZURE_AUTHENTICATION_GUIDE.md',
            'DEPENDENCY_UPDATE_SUMMARY.md',
            'STRESS_TESTING_GUIDE.md'
        ]
        
        if file_path.name in important_docs:
            return True
        
        # 保留最新的测试输出示例
        if 'output_s3_test' in str(file_path) or 'output_azure_blob_test' in str(file_path):
            # 保留一个示例输出目录
            return True
        
        # 保留关键配置文件
        if file_path.name in ['pyproject.toml', 'requirements.txt', 'requirements-remote.txt', '.gitignore']:
            return True
            
        return False
    
    def perform_cleanup(self, dry_run: bool = True) -> Tuple[int, float]:
        """执行清理"""
        analysis = self.analyze_cleanup()
        total_removed = 0
        total_size_mb = 0
        
        print(f"🧹 项目清理分析 {'(预览模式)' if dry_run else '(执行模式)'}")
        print("=" * 60)
        
        for category, data in analysis.items():
            if data['count'] > 0:
                print(f"\n📂 {category.upper().replace('_', ' ')}:")
                print(f"   文件/目录数: {data['count']}")
                print(f"   占用空间: {data['size_mb']:.2f} MB")
                
                for file_path in data['files']:
                    if self.should_keep_file(file_path):
                        print(f"   ⚠️  保留: {file_path.relative_to(self.project_root)}")
                        self.kept_files.append(str(file_path))
                        continue
                    
                    print(f"   🗑️  {'将删除' if dry_run else '删除'}: {file_path.relative_to(self.project_root)}")
                    
                    if not dry_run:
                        try:
                            if file_path.is_file():
                                file_path.unlink()
                                self.removed_files.append(str(file_path))
                            elif file_path.is_dir():
                                shutil.rmtree(file_path)
                                self.removed_dirs.append(str(file_path))
                        except Exception as e:
                            print(f"   ❌ 删除失败: {e}")
                            continue
                    
                    total_removed += 1
                    total_size_mb += data['size_mb'] / data['count'] if data['count'] > 0 else 0
        
        return total_removed, total_size_mb
    
    def create_cleanup_summary(self, removed_count: int, size_mb: float, dry_run: bool = True):
        """创建清理摘要"""
        print(f"\n📊 清理摘要:")
        print("=" * 40)
        print(f"{'预计' if dry_run else '实际'}删除文件/目录: {removed_count}")
        print(f"{'预计' if dry_run else '实际'}释放空间: {size_mb:.2f} MB")
        print(f"保留的重要文件: {len(self.kept_files)}")
        
        if not dry_run and removed_count > 0:
            print(f"\n✅ 清理完成！项目结构已优化")
        elif dry_run:
            print(f"\n💡 这是预览模式，如需执行清理，请使用 --execute 参数")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Keyframe Extractor 项目清理工具")
    parser.add_argument("--execute", action="store_true", help="执行清理（默认为预览模式）")
    parser.add_argument("--project-root", default=".", help="项目根目录路径")
    
    args = parser.parse_args()
    
    cleaner = ProjectCleaner(args.project_root)
    
    print("🚀 Smart Keyframe Extractor - 项目文件清理工具")
    print(f"📁 项目路径: {os.path.abspath(args.project_root)}")
    print(f"🔍 模式: {'执行清理' if args.execute else '预览分析'}")
    
    removed_count, size_mb = cleaner.perform_cleanup(dry_run=not args.execute)
    cleaner.create_cleanup_summary(removed_count, size_mb, dry_run=not args.execute)
    
    if not args.execute and removed_count > 0:
        print(f"\n🔧 执行清理命令:")
        print(f"python cleanup_project.py --execute")

if __name__ == "__main__":
    main()
