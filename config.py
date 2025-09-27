import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# API提供商配置
API_PROVIDERS = {
    "gemini": {
        "name": "Google Gemini",
        "default_model": "gemini-1.5-flash",
        "api_key_env": "GOOGLE_API_KEY",
        "default_key": "AIzaSyD-mbv6XXPnxuwIuanGrpjNMJ55gQbzoCw"
    },
    "siliconflow": {
        "name": "硅基流动",
        "default_model": "qwen/Qwen2.5-7B-Instruct",
        "api_key_env": "SILICONFLOW_API_KEY", 
        "base_url": "https://api.siliconflow.cn/v1/chat/completions",
        "default_key": None,
        "custom_url": None,
        "custom_model": None
    },
    "custom": {
        "name": "自定义供应商",
        "default_model": "gpt-3.5-turbo",
        "api_key_env": "CUSTOM_API_KEY",
        "base_url": "https://api.openai.com/v1/chat/completions",
        "default_key": None,
        "custom_url": None,
        "custom_model": None
    }
}

# 默认API提供商
DEFAULT_PROVIDER = "gemini"

# 设置默认的Google API密钥
if API_PROVIDERS["gemini"]["default_key"]:
    os.environ["GOOGLE_API_KEY"] = API_PROVIDERS["gemini"]["default_key"]

def get_api_config(provider=None):
    """获取API配置"""
    if provider is None:
        provider = DEFAULT_PROVIDER
    
    if provider not in API_PROVIDERS:
        raise ValueError(f"不支持的API提供商: {provider}")
    
    config = API_PROVIDERS[provider].copy()
    
    # 从环境变量获取API密钥
    api_key = os.getenv(config["api_key_env"])
    if not api_key and config.get("default_key"):
        api_key = config["default_key"]
    
    config["api_key"] = api_key
    return config

def get_google_api_key():
    """获取Google API密钥（保持向后兼容）"""
    config = get_api_config("gemini")
    if not config["api_key"]:
        raise ValueError("环境变量 GOOGLE_API_KEY 未设置。请在.env文件中设置或直接设置环境变量。")
    return config["api_key"]

def set_custom_siliconflow_config(api_key, base_url=None, model=None):
    """设置自定义硅基流动配置"""
    if api_key:
        os.environ["SILICONFLOW_API_KEY"] = api_key
        API_PROVIDERS["siliconflow"]["api_key"] = api_key
    
    if base_url:
        API_PROVIDERS["siliconflow"]["custom_url"] = base_url
    
    if model:
        API_PROVIDERS["siliconflow"]["custom_model"] = model

def get_available_providers():
    """获取所有可用的API提供商"""
    return list(API_PROVIDERS.keys())
