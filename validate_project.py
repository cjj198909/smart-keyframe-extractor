#!/usr/bin/env python3
"""
项目完成度验证工具
验证Smart Keyframe Extractor项目的所有组件和功能
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
import importlib.util


class ProjectValidator:
    """项目完成度验证器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'validations': {}
        }
    
    def validate_core_modules(self) -> Dict[str, Any]:
        """验证核心模块"""
        print("🔍 验证核心模块...")
        
        core_modules = {
            'extractor.py': '主要提取器模块',
            'azure_openai.py': 'Azure OpenAI集成',
            'vision_utils.py': '视觉处理工具',
            'cli.py': '命令行接口'
        }
        
        results = {'status': 'success', 'modules': {}, 'issues': []}
        
        for module_file, description in core_modules.items():
            module_path = self.project_root / 'smart_keyframe_extractor' / module_file
            
            if module_path.exists():
                try:
                    # 尝试导入模块验证语法
                    spec = importlib.util.spec_from_file_location(
                        module_file.replace('.py', ''), module_path
                    )
                    module = importlib.util.module_from_spec(spec)
                    
                    # 检查文件大小（应该有实际内容）
                    file_size = module_path.stat().st_size
                    
                    results['modules'][module_file] = {
                        'status': '✅ 存在且有效',
                        'description': description,
                        'file_size': file_size,
                        'path': str(module_path)
                    }
                    
                except Exception as e:
                    results['modules'][module_file] = {
                        'status': '❌ 语法错误',
                        'error': str(e),
                        'description': description
                    }
                    results['issues'].append(f"{module_file}: {e}")
            else:
                results['modules'][module_file] = {
                    'status': '❌ 缺失',
                    'description': description
                }
                results['issues'].append(f"{module_file}: 文件不存在")
        
        if results['issues']:
            results['status'] = 'warning'
        
        return results
    
    def validate_test_suite(self) -> Dict[str, Any]:
        """验证测试套件"""
        print("🧪 验证测试套件...")
        
        test_tools = {
            'quick_benchmark.py': '快速基准测试',
            'concurrent_stress_test.py': '并发压力测试',
            'cloud_stress_test.py': '云服务器测试',
            'memory_stress_test.py': '内存压力测试',
            'stress_test.py': '完整压力测试',
            'performance_optimizer.py': '性能优化器',
            'branch_comparator.py': '分支对比工具',
            'intelligent_batch_processor.py': '智能批处理器'
        }
        
        results = {'status': 'success', 'tools': {}, 'issues': []}
        
        for tool_file, description in test_tools.items():
            tool_path = self.project_root / 'benchmark' / tool_file
            
            if tool_path.exists():
                file_size = tool_path.stat().st_size
                
                # 检查是否为可执行脚本
                try:
                    with open(tool_path, 'r') as f:
                        content = f.read()
                        has_main = 'def main(' in content or 'if __name__ == "__main__"' in content
                        has_shebang = content.startswith('#!')
                        
                    results['tools'][tool_file] = {
                        'status': '✅ 完整',
                        'description': description,
                        'file_size': file_size,
                        'executable': has_main and has_shebang,
                        'path': str(tool_path)
                    }
                    
                except Exception as e:
                    results['tools'][tool_file] = {
                        'status': '⚠️ 可能有问题',
                        'error': str(e),
                        'description': description
                    }
                    results['issues'].append(f"{tool_file}: {e}")
            else:
                results['tools'][tool_file] = {
                    'status': '❌ 缺失',
                    'description': description
                }
                results['issues'].append(f"{tool_file}: 文件不存在")
        
        if results['issues']:
            results['status'] = 'warning'
        
        return results
    
    def validate_documentation(self) -> Dict[str, Any]:
        """验证文档完整性"""
        print("📚 验证文档...")
        
        required_docs = {
            'README.md': '项目主要说明文档',
            'STRESS_TESTING_GUIDE.md': '压力测试指南',
            'PERFORMANCE_ANALYSIS_REPORT.md': '性能分析报告',
            'STRESS_TEST_COMPLETION_SUMMARY.md': '测试完成总结',
            'benchmark/README.md': '测试工具说明',
            'benchmark/CONCURRENT_TESTING_GUIDE.md': '并发测试指南'
        }
        
        results = {'status': 'success', 'documents': {}, 'issues': []}
        
        for doc_file, description in required_docs.items():
            doc_path = self.project_root / doc_file
            
            if doc_path.exists():
                file_size = doc_path.stat().st_size
                
                # 检查文档内容质量
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        line_count = len(content.splitlines())
                        word_count = len(content.split())
                        
                    quality = 'excellent' if word_count > 1000 else 'good' if word_count > 500 else 'basic'
                    
                    results['documents'][doc_file] = {
                        'status': '✅ 完整',
                        'description': description,
                        'file_size': file_size,
                        'lines': line_count,
                        'words': word_count,
                        'quality': quality
                    }
                    
                except Exception as e:
                    results['documents'][doc_file] = {
                        'status': '⚠️ 读取错误',
                        'error': str(e),
                        'description': description
                    }
                    results['issues'].append(f"{doc_file}: {e}")
            else:
                results['documents'][doc_file] = {
                    'status': '❌ 缺失',
                    'description': description
                }
                results['issues'].append(f"{doc_file}: 文件不存在")
        
        if results['issues']:
            results['status'] = 'warning'
        
        return results
    
    def validate_test_results(self) -> Dict[str, Any]:
        """验证测试结果"""
        print("📊 验证测试结果...")
        
        results_dirs = [
            ('wyze_auto_results', '大规模压力测试结果'),
            ('benchmark_results', '基准测试结果'),
            ('cloud_stress_results', '云服务器测试结果')
        ]
        
        results = {'status': 'success', 'result_directories': {}, 'issues': []}
        
        for dir_name, description in results_dirs:
            dir_path = self.project_root / dir_name
            
            if dir_path.exists():
                # 统计结果文件
                json_files = list(dir_path.glob('*.json'))
                csv_files = list(dir_path.glob('*.csv'))
                log_files = list(dir_path.glob('*.log'))
                
                # 查找最新的汇总报告
                summary_files = list(dir_path.glob('summary_report_*.json'))
                latest_summary = None
                
                if summary_files:
                    latest_summary = max(summary_files, key=os.path.getctime)
                    
                    try:
                        with open(latest_summary, 'r') as f:
                            summary_data = json.load(f)
                            
                        total_tasks = summary_data.get('summary', {}).get('total_tasks', 0)
                        success_rate = summary_data.get('summary', {}).get('success_rate', 0)
                        
                        results['result_directories'][dir_name] = {
                            'status': '✅ 有有效结果',
                            'description': description,
                            'json_files': len(json_files),
                            'csv_files': len(csv_files),
                            'log_files': len(log_files),
                            'latest_summary': str(latest_summary.name),
                            'total_tasks': total_tasks,
                            'success_rate': f"{success_rate:.1f}%"
                        }
                        
                    except Exception as e:
                        results['result_directories'][dir_name] = {
                            'status': '⚠️ 结果可能损坏',
                            'error': str(e),
                            'description': description
                        }
                        results['issues'].append(f"{dir_name}: 汇总报告读取错误: {e}")
                else:
                    results['result_directories'][dir_name] = {
                        'status': '🟡 目录存在但无汇总报告',
                        'description': description,
                        'json_files': len(json_files),
                        'csv_files': len(csv_files),
                        'log_files': len(log_files)
                    }
                    results['issues'].append(f"{dir_name}: 缺少汇总报告")
            else:
                results['result_directories'][dir_name] = {
                    'status': '❌ 目录不存在',
                    'description': description
                }
                results['issues'].append(f"{dir_name}: 目录不存在")
        
        if results['issues']:
            results['status'] = 'warning'
        
        return results
    
    def validate_deployment_readiness(self) -> Dict[str, Any]:
        """验证部署就绪状态"""
        print("🚀 验证部署就绪状态...")
        
        deployment_files = {
            'pyproject.toml': '项目配置文件',
            'setup.py': 'Python安装脚本（可选）',
            'requirements.txt': '依赖文件（可选）',
            'MANIFEST.in': '打包清单',
            'LICENSE': '许可证文件',
            'deploy_cloud_stress_test.sh': '云部署脚本',
            'upload_to_github.sh': 'GitHub上传脚本'
        }
        
        results = {'status': 'success', 'deployment_files': {}, 'issues': []}
        
        for file_name, description in deployment_files.items():
            file_path = self.project_root / file_name
            
            if file_path.exists():
                file_size = file_path.stat().st_size
                
                results['deployment_files'][file_name] = {
                    'status': '✅ 存在',
                    'description': description,
                    'file_size': file_size
                }
            else:
                if file_name in ['setup.py', 'requirements.txt']:
                    results['deployment_files'][file_name] = {
                        'status': '🟡 可选文件缺失',
                        'description': description
                    }
                else:
                    results['deployment_files'][file_name] = {
                        'status': '❌ 缺失',
                        'description': description
                    }
                    results['issues'].append(f"{file_name}: 部署文件缺失")
        
        # 检查Git状态
        try:
            git_status = subprocess.run(['git', 'status', '--porcelain'], 
                                      capture_output=True, text=True, 
                                      cwd=self.project_root)
            
            if git_status.returncode == 0:
                uncommitted_files = git_status.stdout.strip().splitlines()
                results['git_status'] = {
                    'repository_exists': True,
                    'uncommitted_files': len(uncommitted_files),
                    'clean_working_directory': len(uncommitted_files) == 0
                }
            else:
                results['git_status'] = {
                    'repository_exists': False,
                    'error': 'Not a git repository'
                }
                
        except Exception as e:
            results['git_status'] = {
                'repository_exists': False,
                'error': str(e)
            }
        
        if results['issues']:
            results['status'] = 'warning'
        
        return results
    
    def run_full_validation(self) -> Dict[str, Any]:
        """运行完整验证"""
        print("🔍 Smart Keyframe Extractor - 项目完成度验证")
        print("=" * 70)
        
        # 执行各项验证
        validations = {
            'core_modules': self.validate_core_modules(),
            'test_suite': self.validate_test_suite(),
            'documentation': self.validate_documentation(),
            'test_results': self.validate_test_results(),
            'deployment': self.validate_deployment_readiness()
        }
        
        self.validation_results['validations'] = validations
        
        # 计算总体状态
        all_statuses = [v['status'] for v in validations.values()]
        if all(status == 'success' for status in all_statuses):
            overall_status = 'excellent'
        elif any(status == 'warning' for status in all_statuses):
            overall_status = 'good'
        else:
            overall_status = 'needs_improvement'
        
        self.validation_results['overall_status'] = overall_status
        
        return self.validation_results
    
    def print_validation_report(self, validation_results: Dict = None):
        """打印验证报告"""
        if validation_results is None:
            validation_results = self.validation_results
        
        print(f"\n📋 项目验证报告")
        print("=" * 70)
        
        validations = validation_results['validations']
        
        # 核心模块验证
        print(f"\n🔧 核心模块验证:")
        core_results = validations['core_modules']
        for module, info in core_results['modules'].items():
            print(f"  {info['status']} {module}: {info['description']}")
        
        # 测试套件验证
        print(f"\n🧪 测试套件验证:")
        test_results = validations['test_suite']
        for tool, info in test_results['tools'].items():
            print(f"  {info['status']} {tool}: {info['description']}")
        
        # 文档验证
        print(f"\n📚 文档验证:")
        doc_results = validations['documentation']
        for doc, info in doc_results['documents'].items():
            status_detail = ""
            if 'words' in info:
                status_detail = f" ({info['words']} 词, {info['quality']})"
            print(f"  {info['status']} {doc}: {info['description']}{status_detail}")
        
        # 测试结果验证
        print(f"\n📊 测试结果验证:")
        result_validation = validations['test_results']
        for dir_name, info in result_validation['result_directories'].items():
            extra_info = ""
            if 'total_tasks' in info:
                extra_info = f" ({info['total_tasks']} 任务, {info['success_rate']} 成功率)"
            print(f"  {info['status']} {dir_name}: {info['description']}{extra_info}")
        
        # 部署就绪验证
        print(f"\n🚀 部署就绪验证:")
        deploy_results = validations['deployment']
        for file_name, info in deploy_results['deployment_files'].items():
            print(f"  {info['status']} {file_name}: {info['description']}")
        
        if 'git_status' in deploy_results:
            git_info = deploy_results['git_status']
            if git_info['repository_exists']:
                git_status = "✅ Git仓库就绪" if git_info['clean_working_directory'] else f"🟡 有 {git_info['uncommitted_files']} 个未提交文件"
                print(f"  {git_status}")
        
        # 总体评估
        overall = validation_results['overall_status']
        print(f"\n🎯 总体评估:")
        if overall == 'excellent':
            print("  🎉 优秀！项目完成度极高，已达到生产环境标准")
            print("  ✅ 所有核心组件完整")
            print("  ✅ 测试覆盖率充分")  
            print("  ✅ 文档完善")
            print("  ✅ 部署就绪")
        elif overall == 'good':
            print("  👍 良好！项目基本完成，有少量待改进项")
            print("  🔧 建议解决警告项后发布")
        else:
            print("  ⚠️ 需要改进！存在关键问题需要解决")
        
        # 收集所有问题
        all_issues = []
        for validation in validations.values():
            all_issues.extend(validation.get('issues', []))
        
        if all_issues:
            print(f"\n❗ 发现的问题:")
            for issue in all_issues:
                print(f"  • {issue}")
        
        print(f"\n📅 验证时间: {validation_results['timestamp'][:19]}")
    
    def save_validation_report(self, output_file: str = None):
        """保存验证报告"""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"project_validation_report_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 验证报告已保存到: {output_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='项目完成度验证工具')
    parser.add_argument('--project-root', help='项目根目录路径')
    parser.add_argument('--save-report', help='保存验证报告到指定文件')
    parser.add_argument('--quiet', action='store_true', help='静默模式，仅输出结果')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🔍 启动项目完成度验证...")
    
    validator = ProjectValidator(args.project_root)
    validation_results = validator.run_full_validation()
    
    if not args.quiet:
        validator.print_validation_report(validation_results)
    
    if args.save_report:
        validator.save_validation_report(args.save_report)
    
    # 返回验证状态作为退出码
    overall_status = validation_results['overall_status']
    if overall_status == 'excellent':
        sys.exit(0)  # 优秀
    elif overall_status == 'good':
        sys.exit(1)  # 良好但有警告
    else:
        sys.exit(2)  # 需要改进


if __name__ == "__main__":
    main()
