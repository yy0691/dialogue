# SBMA 遗传咨询 AI 对话仿真系统

这是一个基于Flask和Google Gemini AI的遗传咨询对话仿真系统，用于模拟SBMA（肯尼迪病）遗传咨询场景。

## 功能特性

- 🤖 AI驱动的对话系统
- 🧬 专业的遗传咨询场景模拟
- 💬 实时对话交互
- 📱 响应式Web界面
- 🔒 安全的API密钥管理

## 技术栈

- **后端**: Flask (Python)
- **AI模型**: Google Gemini 2.0 Flash
- **前端**: HTML, CSS, JavaScript
- **部署**: 支持多种云平台

## 本地运行

### 1. 克隆仓库
```bash
git clone <your-repo-url>
cd dialogue
```

### 2. 创建虚拟环境
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 设置环境变量
```bash
# 方法1: 使用设置脚本
python setup_env.py

# 方法2: 手动设置
set GOOGLE_API_KEY=your_api_key_here
```

### 5. 运行应用
```bash
python app.py
```

访问 http://localhost:5001 开始使用。

## 部署到云平台

### Railway 部署

1. 在 [Railway](https://railway.app) 创建账户
2. 连接GitHub仓库
3. 在Railway控制台设置环境变量 `GOOGLE_API_KEY`
4. 自动部署完成

### Render 部署

1. 在 [Render](https://render.com) 创建账户
2. 创建新的Web服务
3. 连接GitHub仓库
4. 设置环境变量 `GOOGLE_API_KEY`
5. 部署完成

### Heroku 部署

1. 在 [Heroku](https://heroku.com) 创建账户
2. 安装Heroku CLI
3. 创建应用：
```bash
heroku create your-app-name
heroku config:set GOOGLE_API_KEY=your_api_key_here
git push heroku main
```

## 环境变量

| 变量名 | 描述 | 必需 |
|--------|------|------|
| `GOOGLE_API_KEY` | Google Gemini API密钥 | 是 |
| `PORT` | 应用端口号 | 否 (默认5001) |
| `FLASK_ENV` | Flask环境 (development/production) | 否 |

## API密钥获取

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建新的API密钥
3. 复制密钥并设置到环境变量中

## 项目结构

```
dialogue/
├── app.py                 # 主应用文件
├── config.py             # 配置管理
├── requirements.txt      # 依赖包
├── setup_env.py         # 环境设置脚本
├── test_api.py          # API测试脚本
├── static/              # 静态文件
│   ├── style.css
│   └── script.js
├── templates/           # 模板文件
│   └── index.html
├── .github/workflows/   # GitHub Actions
└── @docs/              # 文档
```

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License