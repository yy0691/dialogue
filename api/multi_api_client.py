"""
多API提供商客户端 - Serverless优化版本
支持 Google Gemini, OpenAI, 硅基流动等多种API
"""
import os
import json
from typing import Optional, Dict, Any

class MultiAPIClient:
    """支持多种API提供商的客户端"""
    
    def __init__(self):
        self.clients = {}
        self.current_provider = None
        
    def _lazy_init_gemini(self, api_key: str):
        """延迟初始化Gemini客户端"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-1.5-flash')
        except ImportError:
            raise Exception("google-generativeai 包未安装")
        except Exception as e:
            raise Exception(f"Gemini初始化失败: {e}")
    
    def _lazy_init_openai(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        """延迟初始化OpenAI兼容客户端"""
        try:
            from openai import OpenAI
            return OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            raise Exception("openai 包未安装")
        except Exception as e:
            raise Exception(f"OpenAI客户端初始化失败: {e}")
    
    def set_provider(self, provider: str, config: Dict[str, Any]):
        """设置当前API提供商"""
        api_key = config.get('api_key')
        if not api_key:
            raise Exception(f"{provider} API密钥未提供")
        
        try:
            if provider == "gemini":
                client = self._lazy_init_gemini(api_key)
                self.clients[provider] = {
                    'client': client,
                    'type': 'gemini'
                }
            elif provider == "openai":
                client = self._lazy_init_openai(api_key)
                self.clients[provider] = {
                    'client': client,
                    'type': 'openai',
                    'model': config.get('model', 'gpt-3.5-turbo')
                }
            elif provider == "siliconflow":
                base_url = config.get('base_url', 'https://api.siliconflow.cn/v1')
                client = self._lazy_init_openai(api_key, base_url)
                self.clients[provider] = {
                    'client': client,
                    'type': 'openai',
                    'model': config.get('model', 'qwen/Qwen2.5-7B-Instruct')
                }
            else:
                raise Exception(f"不支持的API提供商: {provider}")
            
            self.current_provider = provider
            print(f"成功设置API提供商: {provider}")
            
        except Exception as e:
            print(f"设置API提供商失败: {e}")
            raise
    
    def generate_content(self, prompt: str, stream: bool = False):
        """生成内容的统一接口"""
        if not self.current_provider or self.current_provider not in self.clients:
            raise Exception("没有可用的API提供商")
        
        client_info = self.clients[self.current_provider]
        client = client_info['client']
        client_type = client_info['type']
        
        try:
            if client_type == 'gemini':
                return client.generate_content(prompt, stream=stream)
            
            elif client_type == 'openai':
                model = client_info.get('model', 'gpt-3.5-turbo')
                messages = [{"role": "user", "content": prompt}]
                
                if stream:
                    return self._handle_openai_stream(client, model, messages)
                else:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    # 创建类似Gemini的响应对象
                    class UnifiedResponse:
                        def __init__(self, text):
                            self.text = text
                    
                    return UnifiedResponse(response.choices[0].message.content)
            
        except Exception as e:
            # 统一错误处理
            error_msg = str(e).lower()
            if "unauthorized" in error_msg or "401" in error_msg:
                raise Exception(f"{self.current_provider} API密钥无效")
            elif "quota" in error_msg or "limit" in error_msg:
                raise Exception(f"{self.current_provider} API配额不足")
            elif "not found" in error_msg or "404" in error_msg:
                raise Exception(f"{self.current_provider} API地址错误")
            else:
                raise Exception(f"{self.current_provider} API调用失败: {e}")
    
    def _handle_openai_stream(self, client, model, messages):
        """处理OpenAI流式响应"""
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            class UnifiedStreamResponse:
                def __init__(self, stream_response):
                    self.stream_response = stream_response
                
                def __iter__(self):
                    for chunk in self.stream_response:
                        if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                            if chunk.choices[0].delta.content:
                                class UnifiedChunk:
                                    def __init__(self, text):
                                        self.text = text
                                yield UnifiedChunk(chunk.choices[0].delta.content)
            
            return UnifiedStreamResponse(response)
        except Exception as e:
            raise Exception(f"流式响应处理失败: {e}")
    
    def test_connection(self, provider: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """测试API连接"""
        try:
            # 临时设置提供商进行测试
            old_provider = self.current_provider
            old_clients = self.clients.copy()
            
            self.set_provider(provider, config)
            response = self.generate_content("请回复'测试成功'")
            
            if response and hasattr(response, 'text') and response.text:
                return {
                    "success": True,
                    "message": f"{provider} 连接成功",
                    "response": response.text
                }
            else:
                return {
                    "success": False,
                    "message": f"{provider} 响应为空"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"{provider} 测试失败: {str(e)}"
            }
        finally:
            # 恢复原来的设置
            self.current_provider = old_provider
            self.clients = old_clients
    
    def get_available_providers(self) -> list:
        """获取可用的API提供商列表"""
        return [
            {
                "id": "gemini",
                "name": "Google Gemini",
                "description": "Google的生成式AI模型",
                "requires": ["api_key"]
            },
            {
                "id": "openai", 
                "name": "OpenAI",
                "description": "OpenAI的GPT模型",
                "requires": ["api_key", "model"]
            },
            {
                "id": "siliconflow",
                "name": "硅基流动",
                "description": "国内AI服务提供商",
                "requires": ["api_key", "base_url", "model"]
            }
        ]
    
    def switch_provider(self, provider: str):
        """切换到已配置的API提供商"""
        if provider in self.clients:
            self.current_provider = provider
            print(f"已切换到: {provider}")
            return True
        else:
            print(f"提供商 {provider} 未配置")
            return False

# 全局实例
multi_api_client = MultiAPIClient()

def get_multi_api_client():
    """获取多API客户端实例"""
    return multi_api_client
