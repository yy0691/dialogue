import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

def get_google_api_key():
    """获取Google API密钥"""
    # 首先尝试从环境变量获取
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # 如果环境变量中没有，使用默认值
    if not api_key:
        api_key = "AIzaSyD-mbv6XXPnxuwIuanGrpjNMJ55gQbzoCw"
        print("使用默认API密钥")
    else:
        print("使用环境变量中的API密钥")
    
    return api_key
