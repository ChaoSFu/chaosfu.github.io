# 个人项目集合

本仓库包含多个独立项目：

## 📊 [A股板块热度分析系统](./stock-analysis/)
基于 GitHub Pages + GitHub Actions 的 A 股板块热度、核心个股及市场节奏分析系统，每日自动更新。

**在线访问**：[https://chaosfu.github.io/stock-analysis/](https://chaosfu.github.io/stock-analysis/)

---

## 🤖 多智能体团队协作模拟系统

Multi-Agent Debate / Discussion Platform - 让不同 AI 模型以不同身份扮演专业角色，自动进行多轮讨论并生成总结方案。

**在线访问**：[https://chaosfu.github.io/](https://chaosfu.github.io/)

## 🎯 功能特点

- ✅ **纯前端实现** - 无需后端服务器，在浏览器中直接运行
- 🤖 **多 AI 模型支持** - 支持 ChatGPT、Claude、DeepSeek 等主流 AI 模型
- 👥 **多角色协作** - 可添加任意数量的智能体角色，每个角色独立配置
- 🔄 **轮次讨论** - 设定讨论轮数，各智能体依次发言并互相参考
- 📊 **自动总结** - 指定总结角色，综合所有意见生成最终方案
- 💾 **本地存储** - 讨论记录和配置保存在浏览器本地
- 📥 **导出功能** - 支持导出讨论记录为 Markdown 格式
- 🔒 **安全保护** - API Key 仅保存在本地，不上传服务器

## 🚀 快速开始

### 1. 打开应用

直接在浏览器中打开 `index.html` 文件即可使用。

或者部署到 GitHub Pages：
```bash
# 已部署到 GitHub Pages，访问：
https://chaosfu.github.io/
```

### 2. 配置 API Keys

点击右上角"API 设置"按钮，输入你的 API Keys：

- **OpenAI API Key**: 用于 GPT-3.5/GPT-4 模型
- **Claude API Key**: 用于 Claude 3 系列模型
- **DeepSeek API Key**: 用于 DeepSeek 模型

> ⚠️ API Key 仅保存在浏览器本地存储，请妥善保管

### 3. 添加角色

点击"添加角色"按钮，配置智能体：

- **角色名称**: 例如 SurgeonGPT、PathologistGPT
- **AI 模型**: 选择要使用的模型
- **角色描述**: 详细描述该角色的专业背景和职责
- **总结角色**: 勾选后该角色将在最后进行总结

### 4. 开始讨论

1. 输入讨论主题（例如：确定宫颈癌根治术的手术方案）
2. 设置讨论轮数（建议 2-5 轮）
3. 点击"开始讨论"按钮
4. 等待 AI 自动完成讨论
5. 查看最终总结方案

## 📋 使用场景

### 医学场景示例

**主题**: 确定宫颈癌根治术的手术方案

**角色配置**:
- **SurgeonGPT** (GPT-4): 外科主任医师，负责手术方案
- **PathologistGPT** (Claude 3 Opus): 病理科专家，分析病理报告
- **RadiologistGPT** (DeepSeek): 影像科医生，解读影像检查
- **ChiefGPT** (GPT-4): 科室主任，最终决策和总结

### 其他应用场景

- 🏢 **产品设计**: 产品经理、设计师、工程师、运营角色讨论产品方案
- 📚 **学术研究**: 不同领域专家对研究问题进行多角度分析
- 💼 **商业决策**: 财务、市场、技术、法务角色评估商业计划
- 🎓 **教育辅导**: 不同学科教师对教学方案进行讨论
- 🔬 **科研评审**: 多位评审专家对论文或项目进行评估

## 🛠️ 技术架构

### 前端技术栈

- **Vue 3**: 响应式 UI 框架
- **Tailwind CSS**: 实用优先的 CSS 框架
- **Font Awesome**: 图标库
- **LocalStorage**: 本地数据持久化

### API 集成

- **OpenAI API**: GPT-3.5/GPT-4 系列模型
- **Anthropic API**: Claude 3 系列模型
- **DeepSeek API**: DeepSeek Chat 模型

### 核心功能模块

```
┌─────────────────────────────┐
│       Web App (Vue 3)        │
├─────────────────────────────┤
│  🧠 Agent Manager            │
│  💬 Discussion Engine        │
│  ⚙️ API Connector            │
│  💾 Context Memory           │
│  🎨 UI Components            │
└─────────────────────────────┘
```

## 📝 讨论流程

```
1. 用户输入主题和配置角色
   ↓
2. 系统初始化讨论上下文
   ↓
3. 第一轮讨论
   ├─ Agent 1 基于主题发言
   ├─ Agent 2 基于主题发言
   └─ Agent 3 基于主题发言
   ↓
4. 第二轮讨论
   ├─ Agent 1 参考前轮发言，补充观点
   ├─ Agent 2 参考前轮发言，补充观点
   └─ Agent 3 参考前轮发言，补充观点
   ↓
5. 总结阶段
   └─ Chief Agent 综合所有意见，生成最终方案
   ↓
6. 导出讨论记录
```

## 🔧 自定义配置

### 修改默认角色

编辑 `app.js` 中的 `loadAgents()` 方法，修改默认角色配置：

```javascript
this.agents = [
    {
        name: '你的角色名',
        model: 'gpt-4-turbo',
        role: '角色描述',
        isSummarizer: false
    },
    // ... 更多角色
];
```

### 调整模型参数

在 `callOpenAI()`, `callClaude()`, `callDeepSeek()` 方法中调整：

- `temperature`: 控制输出随机性 (0-1)
- `max_tokens`: 限制输出长度
- 其他模型特定参数

## 📦 数据存储

所有数据保存在浏览器的 LocalStorage 中：

- `apiKeys`: API 密钥配置
- `agents`: 角色列表
- `discussion`: 讨论记录
- `topic`: 当前讨论主题

清除浏览器缓存将删除所有数据。

## 🔐 安全说明

1. ✅ API Keys 仅保存在本地浏览器
2. ✅ 不会上传到任何服务器
3. ✅ 所有 API 调用直接从浏览器发起
4. ⚠️ 请勿在公共电脑上保存 API Keys
5. ⚠️ 定期更换 API Keys 保证安全

## 🚧 功能扩展计划

- [ ] 支持更多 AI 模型（Gemini、文心一言等）
- [ ] 投票机制：各 AI 对方案进行评分
- [ ] 知识库集成：支持上传文档供 AI 参考
- [ ] 思维导图：可视化讨论流程
- [ ] 语音模式：TTS 朗读 + STT 输入
- [ ] 历史记录管理：查看和恢复历史讨论
- [ ] 模板系统：预设场景模板快速创建讨论

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，欢迎通过 GitHub Issues 联系。
