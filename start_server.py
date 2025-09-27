#!/usr/bin/env python3
"""
启动智能对话系统服务器
支持多种API提供商：Google Gemini、硅基流动、自定义供应商
"""

import os
import sys

def main():
    print("🚀 启动智能对话系统...")
    print("📋 支持的API提供商:")
    print("   • Google Gemini")
    print("   • 硅基流动 (通义千问)")
    print("   • 自定义供应商 (OpenAI兼容API)")
    print()
    
    # 检查依赖
    try:
        import flask
        import google.generativeai
        import openai
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 启动服务器
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, '.')
        
        from api.index import app
        
        print("🌐 服务器启动中...")
        print("📱 访问地址: http://localhost:5001")
        print("⚙️  API配置: 点击右上角 'API配置' 按钮")
        print("🔧 可配置多种API提供商和自定义URL/模型")
        print()
        
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True
        )
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return

if __name__ == "__main__":
    main()
