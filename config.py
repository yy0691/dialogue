import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 直接设置API密钥到环境变量
GOOGLE_API_KEY = "AIzaSyD-mbv6XXPnxuwIuanGrpjNMJ55gQbzoCw"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

def get_google_api_key():
    """获取Google API密钥"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("环境变量 GOOGLE_API_KEY 未设置。请在.env文件中设置或直接设置环境变量。")
    return api_key
