#!/usr/bin/env python3
"""
启动文档学习平台Web服务器
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

# 设置环境变量
os.environ['PYTHONPATH'] = f"{project_root}:{os.path.join(project_root, 'src')}:{os.environ.get('PYTHONPATH', '')}"

if __name__ == '__main__':
    try:
        # 导入并运行web服务器
        from src.api.web_server import WebInterface
        
        # 创建web接口实例
        web_interface = WebInterface()
        
        # 启动服务器
        print("启动文档学习平台Web服务器...")
        print("访问地址: http://localhost:8080")
        print("文档学习功能: http://localhost:8080/documents")
        print("按 Ctrl+C 停止服务器")
        
        web_interface.app.run(
            host='0.0.0.0',
            port=8080,
            debug=True,
            use_reloader=False  # 避免重载时的导入问题
        )
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有依赖都已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)