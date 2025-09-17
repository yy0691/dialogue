#!/usr/bin/env python3
"""
环境变量设置脚本
用于设置Gemini API密钥
"""

import os

def set_google_api_key():
    """设置Google API密钥到环境变量"""
    api_key = "AIzaSyD-mbv6XXPnxuwIuanGrpjNMJ55gQbzoCw"
    os.environ["GOOGLE_API_KEY"] = api_key
    print(f"✅ Google API密钥已设置: {api_key[:20]}...")
    return True

def verify_api_key():
    """验证API密钥是否已设置"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print(f"✅ API密钥验证成功: {api_key[:20]}...")
        return True
    else:
        print("❌ API密钥未设置")
        return False

if __name__ == "__main__":
    print("正在设置Gemini API环境变量...")
    set_google_api_key()
    verify_api_key()
    print("环境变量设置完成！")
