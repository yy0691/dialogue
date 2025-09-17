# Vercel部署指南

## Vercel部署优势

✅ **免费额度充足** - 每月100GB带宽，1000小时函数执行时间  
✅ **全球CDN** - 自动全球加速  
✅ **自动HTTPS** - 免费SSL证书  
✅ **Git集成** - 自动部署，每次push自动更新  
✅ **零配置** - 开箱即用  

## 快速部署步骤

### 1. 准备代码

代码已经配置完成，包含：
- `vercel.json` - Vercel配置文件
- `api/index.py` - 主应用文件
- `api/requirements.txt` - Python依赖

### 2. 创建GitHub仓库

1. 访问 [GitHub](https://github.com) 并登录
2. 点击右上角的 "+" 号，选择 "New repository"
3. 仓库名称建议：`sbma-dialogue-system`
4. 设置为公开仓库（Public）
5. 点击 "Create repository"

### 3. 上传代码到GitHub

```bash
# 添加远程仓库（替换为你的仓库URL）
git remote add origin https://github.com/你的用户名/sbma-dialogue-system.git

# 推送代码到GitHub
git branch -M main
git push -u origin main
```

### 4. 部署到Vercel

#### 方法A: 通过Vercel网站（推荐）

1. 访问 [Vercel](https://vercel.com)
2. 使用GitHub账户登录
3. 点击 "New Project"
4. 选择你的GitHub仓库
5. 点击 "Import"

#### 方法B: 通过Vercel CLI

```bash
# 安装Vercel CLI
npm i -g vercel

# 在项目目录中登录
vercel login

# 部署
vercel

# 设置环境变量
vercel env add GOOGLE_API_KEY
# 输入值：AIzaSyD-mbv6XXPnxuwIuanGrpjNMJ55gQbzoCw

# 重新部署
vercel --prod
```

### 5. 设置环境变量

在Vercel控制台中：

1. 进入项目设置
2. 点击 "Environment Variables"
3. 添加新变量：
   - **Name**: `GOOGLE_API_KEY`
   - **Value**: `AIzaSyD-mbv6XXPnxuwIuanGrpjNMJ55gQbzoCw`
   - **Environment**: Production, Preview, Development

### 6. 部署完成

部署完成后，您将获得：
- **生产环境URL**: `https://your-project-name.vercel.app`
- **预览环境URL**: `https://your-project-name-git-branch.vercel.app`

## 自动部署

每次您推送代码到GitHub的main分支时，Vercel会自动：
1. 检测代码变更
2. 重新构建应用
3. 部署到生产环境
4. 更新URL（如果域名有变化）

## 监控和管理

### 查看部署状态
- 在Vercel控制台查看部署历史
- 监控函数执行时间和错误

### 查看日志
- 在Vercel控制台的"Functions"标签页
- 实时查看应用日志和错误信息

### 性能监控
- 自动监控响应时间
- 错误率统计
- 带宽使用情况

## 故障排除

### 常见问题

1. **部署失败**
   - 检查`vercel.json`配置是否正确
   - 确认`api/requirements.txt`包含所有依赖

2. **环境变量未生效**
   - 确认在Vercel控制台正确设置了环境变量
   - 重新部署应用

3. **静态文件无法访问**
   - 检查`vercel.json`中的静态文件路由配置
   - 确认文件路径正确

### 调试步骤

1. 查看Vercel部署日志
2. 检查函数执行日志
3. 测试API端点
4. 验证环境变量设置

## 成本说明

- **免费计划**: 每月100GB带宽，1000小时函数执行时间
- **Pro计划**: $20/月，无限带宽，更多功能
- 对于大多数项目，免费计划完全够用

## 优势对比

| 特性 | Vercel | Railway | Render |
|------|--------|--------|--------|
| 免费额度 | 100GB/月 | 500小时/月 | 750小时/月 |
| 全球CDN | ✅ | ❌ | ❌ |
| 自动HTTPS | ✅ | ✅ | ✅ |
| Git集成 | ✅ | ✅ | ✅ |
| 冷启动 | 快 | 中等 | 慢 |
| 配置复杂度 | 低 | 低 | 中等 |

Vercel是部署Flask应用的绝佳选择！
