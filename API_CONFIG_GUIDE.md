# API配置指南

## 概述

智能对话系统现已支持多种API提供商，包括：

1. **Google Gemini** - Google的生成式AI模型
2. **硅基流动** - 支持通义千问等国产大模型
3. **自定义供应商** - 支持任意OpenAI兼容的API服务

## 功能特性

### 🔧 多供应商支持
- 一键切换不同的API提供商
- 支持自定义API地址和模型
- 预设配置管理，方便快速切换

### 🛡️ 安全性
- API密钥本地存储
- 密钥显示/隐藏切换
- 连接测试功能

### 🎯 灵活配置
- **硅基流动**: 支持多种通义千问模型
- **自定义供应商**: 完全自定义API地址、模型名称
- **预设管理**: 保存常用配置，一键切换

## 使用方法

### 1. 启动系统
```bash
python start_server.py
```

### 2. 配置API
1. 点击右上角 "API配置" 按钮
2. 选择API提供商
3. 输入相应的配置信息
4. 点击 "测试连接" 验证配置
5. 点击 "保存并使用" 应用配置

### 3. 硅基流动配置
- **API密钥**: 从硅基流动官网获取
- **API地址**: 默认 `https://api.siliconflow.cn/v1`
- **模型选择**: 支持多种通义千问模型
  - Qwen2.5-7B-Instruct
  - Qwen2.5-14B-Instruct
  - Qwen2.5-32B-Instruct
  - Qwen2.5-72B-Instruct
  - DeepSeek-V2.5
  - Llama系列模型

### 4. 自定义供应商配置
- **API密钥**: 目标服务的API密钥
- **API地址**: OpenAI兼容的API基础地址
- **模型名称**: 可选择预设模型或输入自定义模型名
- **供应商名称**: 自定义显示名称

## 支持的API格式

### OpenAI兼容格式
系统支持所有遵循OpenAI API格式的服务，包括：
- OpenAI官方API
- Azure OpenAI
- 各种开源模型API服务
- 自建的模型服务

### 请求格式
```json
{
  "model": "模型名称",
  "messages": [
    {"role": "user", "content": "用户输入"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

## 配置示例

### 硅基流动配置
```
API提供商: 硅基流动
API密钥: sk-xxxxxxxxxxxxxx
API地址: https://api.siliconflow.cn/v1
模型名称: qwen/Qwen2.5-7B-Instruct
```

### 自定义OpenAI配置
```
API提供商: 自定义供应商
API密钥: sk-xxxxxxxxxxxxxx
API地址: https://api.openai.com/v1
模型名称: gpt-3.5-turbo
供应商名称: OpenAI
```

### 自定义本地服务配置
```
API提供商: 自定义供应商
API密钥: your-local-key
API地址: http://localhost:8000/v1
模型名称: llama2-7b-chat
供应商名称: 本地Llama服务
```

## 故障排除

### 常见问题
1. **连接测试失败**
   - 检查API密钥是否正确
   - 确认API地址格式正确
   - 验证网络连接

2. **模型响应异常**
   - 确认模型名称正确
   - 检查API配额是否充足
   - 验证API服务状态

3. **配置不生效**
   - 确保点击了"保存并使用"
   - 刷新页面重新加载配置
   - 检查浏览器控制台错误信息

### 调试建议
- 使用浏览器开发者工具查看网络请求
- 检查服务器控制台输出
- 验证API服务的响应格式

## 技术架构

### 后端支持
- Flask Web框架
- 统一的APIClient抽象层
- 支持流式和非流式响应
- 自动错误处理和重试

### 前端功能
- 响应式配置界面
- 实时配置验证
- 本地配置存储
- 预设配置管理

## 更新日志

### v2.0.0
- ✨ 新增硅基流动API支持
- ✨ 新增自定义供应商支持
- ✨ 新增预设配置管理
- 🔧 重构API配置系统
- 🎨 优化配置界面UI
- 🛡️ 增强安全性和错误处理
