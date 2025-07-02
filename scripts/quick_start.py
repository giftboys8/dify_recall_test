#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动脚本
帮助用户快速配置和开始使用Dify知识库召回测试工具
"""

import os
import json
import sys
from pathlib import Path

def create_config_interactive():
    """交互式创建配置文件"""
    print("🔧 Dify知识库召回测试工具 - 快速配置")
    print("=" * 50)
    
    # 获取API配置
    print("\n📡 API配置:")
    api_url = input("请输入Dify API基础URL [https://api.dify.ai]: ").strip()
    if not api_url:
        api_url = "https://api.dify.ai"
    
    api_key = input("请输入您的API密钥: ").strip()
    if not api_key:
        print("❌ API密钥不能为空")
        return None
    
    dataset_id = input("请输入知识库ID: ").strip()
    if not dataset_id:
        print("❌ 知识库ID不能为空")
        return None
    
    # 获取测试配置
    print("\n⚙️ 测试配置:")
    
    try:
        top_k = int(input("返回文档数量 [10]: ") or "10")
    except ValueError:
        top_k = 10
    
    try:
        delay = float(input("请求间隔时间(秒) [1.0]: ") or "1.0")
    except ValueError:
        delay = 1.0
    
    reranking = input("启用重排序? (y/n) [y]: ").strip().lower()
    reranking_enabled = reranking != 'n'
    
    score_threshold = input("启用分数阈值? (y/n) [n]: ").strip().lower()
    score_threshold_enabled = score_threshold == 'y'
    
    threshold_value = 0.0
    if score_threshold_enabled:
        try:
            threshold_value = float(input("分数阈值 [0.7]: ") or "0.7")
        except ValueError:
            threshold_value = 0.7
    
    # 创建配置
    config = {
        "api_base_url": api_url,
        "api_key": api_key,
        "dataset_id": dataset_id,
        "test_settings": {
            "top_k": top_k,
            "delay_between_requests": delay,
            "score_threshold_enabled": score_threshold_enabled,
            "score_threshold": threshold_value,
            "reranking_enabled": reranking_enabled,
            "reranking_model": {
                "provider": "cohere",
                "model": "rerank-multilingual-v3.0"
            }
        },
        "output_settings": {
            "save_csv": True,
            "save_detailed_json": True,
            "output_prefix": "recall_test",
            "include_document_content": True
        }
    }
    
    return config

def save_config(config, filename="user_config.json"):
    """保存配置到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"✅ 配置已保存到: {filename}")

def create_sample_test_cases():
    """创建示例测试用例"""
    sample_cases = [
        {
            "id": "quick_001",
            "query": "什么是人工智能？",
            "category": "基础概念",
            "description": "AI基础概念测试"
        },
        {
            "id": "quick_002",
            "query": "机器学习和深度学习的区别",
            "category": "技术对比",
            "description": "技术概念对比测试"
        },
        {
            "id": "quick_003",
            "query": "如何选择合适的算法？",
            "category": "实践指导",
            "description": "实践应用指导测试"
        }
    ]
    
    # 保存为CSV
    import csv
    filename = "quick_test_cases.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'query', 'category', 'description']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for case in sample_cases:
            writer.writerow(case)
    
    print(f"✅ 示例测试用例已创建: {filename}")
    return filename

def run_quick_test(config_file, test_file):
    """运行快速测试"""
    print("\n🚀 开始快速测试...")
    
    # 创建结果目录
    results_dir = "quick_results"
    Path(results_dir).mkdir(exist_ok=True)
    
    # 构建命令
    cmd = [
        sys.executable,
        "enhanced_recall_tester.py",
        "--config", config_file,
        "--test-file", test_file,
        "--output-dir", results_dir,
        "--generate-viz"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    # 检查文件是否存在
    if not os.path.exists("enhanced_recall_tester.py"):
        print("❌ 找不到enhanced_recall_tester.py文件")
        print("请确保在正确的目录中运行此脚本")
        return False
    
    # 运行测试
    import subprocess
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 测试完成！")
            print(f"📁 结果保存在: {results_dir}/")
            print("\n📊 输出文件:")
            
            # 列出结果文件
            for file in Path(results_dir).glob("*"):
                print(f"  - {file.name}")
            
            return True
        else:
            print("❌ 测试失败:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 运行测试时出错: {str(e)}")
        return False

def start_web_interface():
    """启动Web界面"""
    print("\n🌐 启动Web界面...")
    
    if not os.path.exists("web_interface.py"):
        print("❌ 找不到web_interface.py文件")
        return False
    
    try:
        import subprocess
        cmd = [sys.executable, "-m", "streamlit", "run", "web_interface.py"]
        print(f"执行命令: {' '.join(cmd)}")
        print("🌐 Web界面将在浏览器中打开...")
        print("💡 使用 Ctrl+C 停止服务")
        
        subprocess.run(cmd)
        return True
        
    except KeyboardInterrupt:
        print("\n👋 Web服务已停止")
        return True
    except Exception as e:
        print(f"❌ 启动Web界面失败: {str(e)}")
        return False

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'requests', 'pandas', 'matplotlib', 'seaborn', 'streamlit', 'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖包已安装")
    return True

def main():
    """主函数"""
    print("🎯 Dify知识库召回测试工具 - 快速启动")
    print("=" * 60)
    
    # 检查依赖
    print("\n🔍 检查依赖包...")
    if not check_dependencies():
        return
    
    while True:
        print("\n📋 请选择操作:")
        print("1. 交互式配置并运行测试")
        print("2. 启动Web界面")
        print("3. 创建示例测试用例")
        print("4. 查看使用说明")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == '1':
            # 交互式配置并测试
            config = create_config_interactive()
            if config:
                config_file = "user_config.json"
                save_config(config, config_file)
                
                # 创建测试用例
                use_sample = input("\n使用示例测试用例? (y/n) [y]: ").strip().lower()
                if use_sample != 'n':
                    test_file = create_sample_test_cases()
                else:
                    test_file = input("请输入测试用例CSV文件路径: ").strip()
                    if not os.path.exists(test_file):
                        print(f"❌ 文件不存在: {test_file}")
                        continue
                
                # 运行测试
                run_quick_test(config_file, test_file)
        
        elif choice == '2':
            # 启动Web界面
            start_web_interface()
        
        elif choice == '3':
            # 创建示例测试用例
            create_sample_test_cases()
        
        elif choice == '4':
            # 显示使用说明
            print("\n📖 使用说明:")
            print("1. 首先确保已安装所有依赖包: pip install -r requirements.txt")
            print("2. 准备您的Dify API密钥和知识库ID")
            print("3. 选择运行方式:")
            print("   - 命令行工具: 适合自动化和批量处理")
            print("   - Web界面: 适合交互式操作和结果查看")
            print("4. 准备测试用例CSV文件，包含id、query、category、description列")
            print("5. 运行测试并查看结果")
            print("\n📁 文件说明:")
            print("- dify_kb_recall_test.py: 基础命令行工具")
            print("- enhanced_recall_tester.py: 增强版命令行工具")
            print("- web_interface.py: Web图形界面")
            print("- test_cases_sample.csv: 示例测试用例")
            print("- config_template.json: 配置文件模板")
        
        elif choice == '5':
            print("👋 再见！")
            break
        
        else:
            print("❌ 无效选项，请重新选择")

if __name__ == '__main__':
    main()