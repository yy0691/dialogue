#!/usr/bin/env python3
"""
测试Gemini API连接
"""

import google.generativeai as genai
from config import get_google_api_key

def test_gemini_api():
    """测试Gemini API连接"""
    try:
        # 获取API密钥
        api_key = get_google_api_key()
        print(f"✅ API密钥获取成功: {api_key[:20]}...")
        
        # 配置API
        genai.configure(api_key=api_key)
        
        # 创建模型
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("✅ 模型创建成功")
        
        # 测试生成内容
        response = model.generate_content("你好，请简单介绍一下你自己。")
        print("✅ API调用成功")
        print(f"AI回复: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

if __name__ == "__main__":
    print("正在测试Gemini API连接...")
    success = test_gemini_api()
    if success:
        print("🎉 API连接测试成功！")
    else:
        print("💥 API连接测试失败！")
