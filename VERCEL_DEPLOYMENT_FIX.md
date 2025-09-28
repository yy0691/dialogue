# Vercel 部署问题修复指南

## 🔍 问题分析

你遇到的 `FUNCTION_INVOCATION_FAILED` 错误主要由以下原因造成：

1. **依赖问题**：`api/requirements.txt` 缺少必要的依赖
2. **Serverless兼容性**：原代码在启动时就执行了复杂的初始化逻辑
3. **文件路径问题**：相对路径在Serverless环境中可能失效
4. **环境变量配置**：缺少必要的环境变量设置

## 🛠️ 解决方案

### 1. 替换主文件

将 `api/index.py` 替换为 `api/index_fixed.py`：

```bash
# 备份原文件
mv api/index.py api/index_backup.py

# 使用修复版本
mv api/index_fixed.py api/index.py
```

### 2. 确认依赖文件

确保 `api/requirements.txt` 包含以下内容：
```
Flask==2.3.3
google-generativeai==0.3.2
python-dotenv==1.0.0
openai>=1.0.0
requests>=2.25.0
```

### 3. 确认 vercel.json 配置

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": { 
        "maxLambdaSize": "50mb",
        "runtime": "python3.9"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "FLASK_SECRET_KEY": "@flask_secret_key",
    "GOOGLE_API_KEY": "@google_api_key"
  }
}
```

### 4. 设置环境变量

在Vercel控制台中设置以下环境变量：

1. **FLASK_SECRET_KEY**: 一个随机字符串，用于会话加密
   ```
   例如: your_super_secret_key_here_12345
   ```

2. **GOOGLE_API_KEY**: 你的Google Gemini API密钥
   ```
   例如: AIzaSyD-mbv6XXPnxuwIuanGrpjNMJ55gQbzoCw
   ```

### 5. 部署步骤

1. **提交代码更改**：
   ```bash
   git add .
   git commit -m "修复Vercel部署问题"
   git push
   ```

2. **重新部署**：
   - 在Vercel控制台点击 "Redeploy"
   - 或者推送新的commit触发自动部署

## 🔧 修复的关键改进

### 1. 延迟初始化
- 移除了启动时的复杂初始化
- 改为按需加载和初始化

### 2. 错误处理增强
- 添加了多层错误处理
- 提供了默认数据作为后备

### 3. 路径问题修复
- 使用多个可能的文件路径
- 添加了文件存在性检查

### 4. 简化的API客户端
- 移除了复杂的多提供商支持
- 专注于核心功能

### 5. 会话管理优化
- 简化了会话状态管理
- 添加了会话初始化检查

## 🧪 测试部署

部署后，你可以通过以下方式测试：

1. **健康检查**：访问 `https://your-app.vercel.app/health`
2. **主页**：访问 `https://your-app.vercel.app/`
3. **API测试**：使用前端界面测试对话功能

## 🚨 常见问题

### 如果仍然出现错误：

1. **检查日志**：在Vercel控制台查看Function日志
2. **验证环境变量**：确保所有环境变量都已正确设置
3. **检查API密钥**：确保Google API密钥有效且有足够配额
4. **文件路径**：确保所有必要的文件都已上传

### 如果API调用失败：

1. 检查Google API密钥是否有效
2. 确认API配额是否充足
3. 验证网络连接是否正常

## 📞 需要帮助？

如果问题仍然存在，请提供：
1. Vercel部署日志
2. 浏览器控制台错误信息
3. 具体的错误步骤

这样我可以进一步协助你解决问题。
