#!/usr/bin/env python3
"""
直接测试Flask应用启动和路由注册
"""

import os
import sys

# 添加src目录到Python路径
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

def test_flask_app():
    """测试Flask应用"""
    try:
        print("正在导入WebInterface...")
        from api.web_server import WebInterface
        
        print("正在创建WebInterface实例...")
        web_interface = WebInterface()
        app = web_interface.app
        
        print("\n=== Flask应用路由列表 ===")
        with app.app_context():
            for rule in app.url_map.iter_rules():
                methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
                print(f"{rule.endpoint:30} {methods:15} {rule.rule}")
        
        print("\n=== 检查翻译API路由 ===")
        translation_routes = [rule for rule in app.url_map.iter_rules() 
                            if rule.rule.startswith('/api/translation')]
        
        if translation_routes:
            print(f"✅ 找到 {len(translation_routes)} 个翻译API路由:")
            for route in translation_routes:
                methods = ','.join(route.methods - {'HEAD', 'OPTIONS'})
                print(f"  {route.rule} [{methods}]")
        else:
            print("❌ 未找到翻译API路由")
        
        # 检查具体的translate路由
        translate_route = None
        for rule in app.url_map.iter_rules():
            if rule.rule == '/api/translation/translate':
                translate_route = rule
                break
        
        if translate_route:
            print(f"\n✅ 找到 /api/translation/translate 路由")
            print(f"   方法: {','.join(translate_route.methods - {'HEAD', 'OPTIONS'})}")
            print(f"   端点: {translate_route.endpoint}")
        else:
            print(f"\n❌ 未找到 /api/translation/translate 路由")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Flask应用路由测试")
    print("=" * 50)
    test_flask_app()