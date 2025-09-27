# 依赖安装指南

## 问题诊断

如果您遇到 `'str' object has no attribute 'choices'` 错误，通常是因为缺少必要的依赖库。

## 解决方案

### 1. 安装所有依赖
```bash
pip install -r requirements.txt
```

### 2. 手动安装缺少的库
如果上述命令失败，请手动安装：

```bash
# 安装OpenAI库（用于硅基流动和自定义供应商）
pip install openai>=1.0.0

# 安装其他依赖
pip install requests>=2.25.0
pip install Flask==2.3.3
pip install google-generativeai==0.3.2
pip install python-dotenv==1.0.0
```

### 3. 验证安装
运行以下Python代码验证安装：

```python
try:
    import openai
    print(f"✅ OpenAI库已安装，版本: {openai.__version__}")
except ImportError:
    print("❌ OpenAI库未安装")

try:
    import google.generativeai as genai
    print("✅ Google GenerativeAI库已安装")
except ImportError:
    print("❌ Google GenerativeAI库未安装")
```

## 常见问题

### Q: 为什么需要OpenAI库？
A: 硅基流动和自定义供应商使用OpenAI兼容的API格式，需要OpenAI库来处理请求。

### Q: 只使用Gemini需要安装OpenAI库吗？
A: 不需要。如果只使用Google Gemini，只需要安装 `google-generativeai` 库。

### Q: 安装失败怎么办？
A: 
1. 确保Python版本 >= 3.7
2. 更新pip: `pip install --upgrade pip`
3. 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple openai`

## 启动服务器

安装完依赖后，使用以下命令启动：

```bash
python start_server.py
```

或者直接运行：

```bash
python api/index.py
```

## 测试API配置

1. 打开浏览器访问 http://localhost:5001
2. 点击右上角"API配置"按钮
3. 选择API提供商并输入密钥
4. 点击"测试连接"验证配置

如果仍有问题，请检查浏览器控制台的错误信息。
