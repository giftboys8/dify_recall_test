#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Flask应用路由注册情况
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def check_routes():
    """检查Flask应用的路由注册情况"""
    try:
        # 设置环境变量避免相对导入问题
        import os
        os.environ['PYTHONPATH'] = os.path.join(os.getcwd(), 'src')
        
        # 直接导入模块
        import sys
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        from api.web_server import WebInterface
        
        print("正在创建Flask应用...")
        web_interface = WebInterface()
        app = web_interface.app
        
        print("\n=== Flask应用路由列表 ===")
        routes = []
        for rule in app.url_map.iter_rules():
            methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            routes.append((methods, rule.rule))
        
        # 按路径排序
        routes.sort(key=lambda x: x[1])
        
        for methods, rule in routes:
            print(f"{methods:15} {rule}")
        
        # 检查特定的翻译API路由
        print("\n=== 翻译API路由检查 ===")
        translation_routes = [route for route in routes if '/api/translation' in route[1]]
        
        if translation_routes:
            print("找到以下翻译API路由:")
            for methods, rule in translation_routes:
                print(f"  {methods:15} {rule}")
        else:
            print("❌ 未找到翻译API路由")
        
        # 检查蓝图注册
        print("\n=== 蓝图注册检查 ===")
        blueprints = list(app.blueprints.keys())
        print(f"已注册的蓝图: {blueprints}")
        
        if 'translation' in blueprints:
            print("✅ translation蓝图已注册")
        else:
            print("❌ translation蓝图未注册")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_blueprint_file():
    """检查蓝图文件是否存在"""
    print("\n=== 蓝图文件检查 ===")
    
    blueprint_file = Path(__file__).parent / 'src' / 'api' / 'translation_api.py'
    if blueprint_file.exists():
        print(f"✅ 蓝图文件存在: {blueprint_file}")
        
        # 检查文件内容
        try:
            with open(blueprint_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'translation_bp' in content:
                print("✅ 找到translation_bp蓝图定义")
            else:
                print("❌ 未找到translation_bp蓝图定义")
                
            if '@translation_bp.route' in content:
                print("✅ 找到路由装饰器")
                # 统计路由数量
                route_count = content.count('@translation_bp.route')
                print(f"   路由数量: {route_count}")
            else:
                print("❌ 未找到路由装饰器")
                
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
    else:
        print(f"❌ 蓝图文件不存在: {blueprint_file}")

def main():
    """主函数"""
    print("Flask路由检查工具")
    print("=" * 50)
    
    # 检查蓝图文件
    check_blueprint_file()
    
    # 检查路由注册
    if check_routes():
        print("\n✅ 路由检查完成")
    else:
        print("\n❌ 路由检查失败")

if __name__ == '__main__':
    main()