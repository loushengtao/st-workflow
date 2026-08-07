# Leva Skills — 好用的 Agent Skill 工作流合集

由 [杭州利未智能科技有限公司（Leva）](https://github.com/loushengtao) 维护的 **Claude Code / Agent Skill 工作流分享仓库**。

## 这是什么

Skill 是给 AI Agent（如 Claude Code）用的"工作流说明书"：一个文件夹里装着一份 `SKILL.md`（告诉 Agent 该怎么一步步干活）加上配套的脚本和模板。装好之后，你对 Agent 说一句话（比如"帮我剪一下这条口播"），它就会按照 skill 里沉淀好的完整流程自动执行——而不是每次都从零发挥。

这个仓库收录我们在实际业务中打磨出来、验证过的 skill，每一个都做到**开箱即用**：依赖交代清楚、流程写成步骤、坑都提前标好。

## 有什么用

- **拿来即用**：复制一个文件夹就获得一条完整的自动化工作流，不用自己摸索提示词和流程编排
- **可复现**：同一个 skill 在任何机器、任何项目目录下行为一致，依赖自动解决
- **可进化**：skill 是纯文本 + 脚本，用得不顺手直接改，改完全局生效

## 快速开始

1. 克隆本仓库：

```bash
git clone https://github.com/loushengtao/leva-skills.git
```

2. 把想用的 skill 复制到 Claude Code 的用户级 skill 目录：

```bash
cp -R leva-skills/skills/koubo-edit ~/.claude/skills/
```

3. 在 Claude Code 里直接说需求（如"剪一下这条口播"），或用斜杠命令 `/koubo-edit` 显式调用。

> 前置要求各 skill 不同，均写在各自 `SKILL.md` 的环境说明里，Agent 会照着自检，无需手动配置。

## Skill 目录

| Skill | 一句话说明 | 主要依赖 |
|---|---|---|
| [koubo-edit](skills/koubo-edit/) | 中文口播视频自动剪辑：本机 Whisper 转写 → AI 导演做视觉设计（胶囊字幕、侧方大字、白板讲解卡、AI 配图物料）→ Remotion 渲染成片，三阶段流程（分析确认 → 渲染 → 微调），全程本机 | uv、Node.js ≥ 18（Apple Silicon Mac） |

*持续更新中，后续会陆续放入更多经过实战验证的 skill。*

## 仓库结构

```
leva-skills/
├── README.md
└── skills/
    └── <skill-name>/
        ├── SKILL.md        # 工作流主文档（Agent 读这个干活）
        ├── scripts/        # 配套脚本（PEP 723 内联依赖，uv run 直接跑）
        └── assets/         # 模板等静态资源
```

## 反馈与交流

用得不顺、发现 bug、想要新的工作流，欢迎提 Issue。
