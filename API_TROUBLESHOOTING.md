# API配置故障排除指南

## 常见错误及解决方案

### 1. "API地址错误：服务器返回了网页而不是API响应"

**错误原因：**
- API地址不正确，指向了网站首页而不是API端点
- 缺少正确的路径或端点

**解决方案：**
```
❌ 错误示例：
https://api.openai.com
https://your-domain.com

✅ 正确示例：
https://api.openai.com/v1
https://api.siliconflow.cn/v1
http://localhost:8000/v1
```

### 2. "API密钥无效或已过期"

**解决方案：**
1. 检查API密钥是否正确复制（无多余空格）
2. 确认密钥未过期
3. 验证密钥权限是否足够

### 3. "API地址不存在，请检查URL是否正确"

**常见原因：**
- URL拼写错误
- 端口号错误
- 路径不完整

**检查清单：**
- [ ] URL以 http:// 或 https:// 开头
- [ ] 域名拼写正确
- [ ] 端口号正确（如果需要）
- [ ] 路径完整（通常以 /v1 结尾）

### 4. "缺少OpenAI库依赖"

**解决方案：**
```bash
pip install openai>=1.0.0
```

## 不同服务商配置示例

### OpenAI官方
```
API地址: https://api.openai.com/v1
模型: gpt-3.5-turbo, gpt-4
密钥格式: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Azure OpenAI
```
API地址: https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2023-05-15
模型: 你的部署名称
密钥格式: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 硅基流动
```
API地址: https://api.siliconflow.cn/v1
模型: qwen/Qwen2.5-7B-Instruct
密钥格式: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 本地部署服务
```
API地址: http://localhost:8000/v1
模型: 根据你的模型而定
密钥: 根据你的配置而定
```

## 调试步骤

### 1. 检查网络连接
```bash
# 测试基本连通性
ping api.openai.com
curl -I https://api.openai.com/v1
```

### 2. 验证API地址
在浏览器中访问API地址，应该返回JSON格式的错误信息，而不是HTML页面。

### 3. 测试API密钥
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}]}' \
     https://api.openai.com/v1/chat/completions
```

### 4. 查看浏览器控制台
1. 按F12打开开发者工具
2. 切换到Console标签
3. 查看详细的错误信息和调试日志

## 特殊配置说明

### 代理服务器
如果使用代理或中转服务，确保：
1. 代理服务器支持OpenAI API格式
2. 认证方式正确
3. 请求头正确转发

### 自建服务
如果使用自建的API服务：
1. 确保服务实现了OpenAI兼容的接口
2. 检查CORS设置
3. 验证SSL证书（如果使用HTTPS）

## 获取帮助

如果以上方案都无法解决问题：

1. **检查服务状态**：访问对应服务商的状态页面
2. **查看文档**：阅读API提供商的官方文档
3. **联系支持**：向API提供商寻求技术支持
4. **社区求助**：在相关技术社区提问

## 测试建议

1. **从简单开始**：先用默认配置测试
2. **逐步调试**：一次只改变一个参数
3. **保存配置**：成功的配置保存为预设
4. **定期检查**：API密钥和服务状态可能会变化
