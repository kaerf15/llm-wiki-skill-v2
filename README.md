# llm-wiki

**面向 Cursor + Obsidian 的 LLM Wiki Agent Skill。**

它把资料先沉淀成一个长期维护的 Markdown 知识库，再让 Agent 持续执行 `compile`、`ingest`、`query`、`lint`、`audit`。这不是传统 RAG 每次重新检索原文，而是让 LLM 把原始资料编译成可交叉链接、可审计、可迭代的 wiki。

本项目基于 [lewislulu/llm-wiki-skill](https://github.com/lewislulu/llm-wiki-skill) 改造，重点适配 Cursor + Obsidian 使用场景，包括 `AGENTS.md` 主入口、本地 Web viewer 自启动、MarkItDown 导入器和中文部署说明。

灵感来自 [Andrej Karpathy 的 llm-wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)。

## 这个项目解决什么

你负责提供资料、提出问题、指出 AI 写错的地方。Agent 负责读资料、写 wiki、维护链接、更新索引、处理反馈。

项目里包含三部分：

- `llm-wiki/`：给 Cursor/Agent 读取的 skill，定义 wiki 结构和五类操作。
- `plugins/obsidian-audit/`：Obsidian 插件，选中文本后写反馈，反馈会落到 `audit/`。
- `web/`：本地预览服务，渲染 Markdown、Mermaid、KaTeX 和 wikilinks，也可以在浏览器里提交反馈。

`plugins/obsidian-audit/` 和 `web/` 共用 `audit-shared/`，所以两边写出来的审计文件格式一致。

## 极简部署流程

面向普通用户，推荐这样用：

1. 安装前置依赖：Python 3、Node.js 20+、Git、Obsidian。
2. 打开 Obsidian，新建一个 vault，作为你的知识库。
3. 打开 Cursor，选择 `Open Folder`，打开刚才创建的 Obsidian vault。
4. 把下面“一键部署提示词”直接发给 Cursor。
5. Cursor 会自动下载本项目、初始化当前 vault、安装 Web viewer、配置开机自启动、链接 Obsidian 插件。

用户不需要手动下载本仓库，也不需要知道 `web/` 应该放在哪里。

## 推荐安装位置

工具代码不要放进 Obsidian 知识库里。

推荐结构：

```text
工具代码:
macOS:   ~/Library/Application Support/llm-wiki/
Windows: %LOCALAPPDATA%\llm-wiki\

知识库:
任意 Obsidian vault，例如 ~/Documents/MyVault/
```

`web/` 作为本地服务运行，只通过 `--wiki` 指向你的 Obsidian vault / wiki root。

## 前置依赖

部署前需要用户电脑已经安装：

- Python 3：用于 `scaffold.py`、`lint_wiki.py`、`audit_review.py`、`import_source.py`
- Node.js 20+：用于 `web/` 和 Obsidian 插件构建；Node.js 会自带 `npm`
- Git：用于从 GitHub 下载本项目
- Obsidian：用于打开和浏览 vault
- MarkItDown：可选，仅在导入 PDF、Office、HTML 等非 Markdown 文件时需要

检查命令：

```bash
python3 --version
node -v
npm -v
git --version
```

Windows 用户如果没有 `python3` 命令，可尝试：

```powershell
py -3 --version
```

## 一键交给 Cursor 的部署提示词

先用 Cursor 打开你的 Obsidian vault 文件夹，然后把下面整段提示词直接复制给 Cursor。

```text
请在当前 Cursor workspace（也就是我当前打开的 Obsidian vault）里部署 llm-wiki。

请严格按下面要求执行：
- 当前 workspace 就是 Wiki 根目录 / Obsidian vault。
- 不要把 web/、audit-shared/、plugins/ 复制到我的 Obsidian vault 里。
- 请从 GitHub 下载项目：https://github.com/kaerf15/llm-wiki-skill
- 工具代码放到用户级应用目录：
  - macOS：~/Library/Application Support/llm-wiki/llm-wiki-skill
  - Windows：%LOCALAPPDATA%\llm-wiki\llm-wiki-skill
- Web 端口：4875
- 作者：lym

参数：
- REPO_URL=https://github.com/kaerf15/llm-wiki-skill
- WIKI_ROOT=当前 Cursor workspace 根目录
- PORT=4875
- AUTHOR=lym

目标：
1. 先检查前置依赖：
   - 运行 `python3 --version`；如果 Windows 没有 `python3`，尝试 `py -3 --version`。
   - 运行 `node -v`，确认 Node.js 版本是 20 或更高。
   - 运行 `npm -v`，确认 npm 可用。
   - 运行 `git --version`，确认 Git 可用。
   - 如果 Python 3、Node.js 20+、npm 或 Git 不存在，请停止部署，并告诉我需要先安装什么。
2. 确认当前 Cursor workspace 是一个真实目录。把这个目录作为 WIKI_ROOT。
3. 根据操作系统确定工具安装目录：
   - macOS：~/Library/Application Support/llm-wiki/llm-wiki-skill
   - Windows：%LOCALAPPDATA%\llm-wiki\llm-wiki-skill
4. 如果工具目录不存在，请从 REPO_URL clone 到工具目录；如果已经存在，请进入工具目录并拉取最新代码。
5. 如果 WIKI_ROOT 还不是 llm-wiki 结构，请运行：
   python3 <工具目录>/llm-wiki/scripts/scaffold.py "<WIKI_ROOT>" "My Knowledge Base"
   生成 AGENTS.md、CLAUDE.md、raw/、wiki/、audit/、log/、outputs/。
6. 构建共享库：
   cd <工具目录>
   cd audit-shared
   npm install
   npm run build
   cd ..
7. 构建 Web viewer 并安装开机自启动：
   cd web
   npm install
   npm run build
   npm run autostart:install -- --wiki "<WIKI_ROOT>" --port 4875 --author "lym"
   cd ..
8. 构建并链接 Obsidian 插件：
   cd plugins/obsidian-audit
   npm install
   npm run build
   npm run link -- "<WIKI_ROOT>"
   cd ../..
9. 可选安装 MarkItDown：
   pip install 'markitdown[all]'
10. 验证：
   - 检查 http://127.0.0.1:4875 是否可访问。
   - 检查 "<WIKI_ROOT>/AGENTS.md" 存在。
   - 检查 "<WIKI_ROOT>/CLAUDE.md" 内容是 @AGENTS.md。
   - 检查 "<WIKI_ROOT>/audit" 存在。
   - 在 Obsidian 中提示我启用 Community Plugins 里的 "LLM Wiki Audit"。
11. 最后告诉我：
   - Web viewer 地址
   - 工具代码安装目录
   - 自启动是否安装成功
   - Obsidian 插件目录位置
   - 如果有失败，给出失败命令和下一步修复建议。
```

## 手动快速开始

创建一个新 wiki：

```bash
python3 llm-wiki/scripts/scaffold.py ~/my-wiki "My Research Topic"
```

加入已有 Markdown 资料：

```bash
cp my-article.md ~/my-wiki/raw/articles/
```

导入 PDF、Office、HTML 等非 Markdown 资料：

```bash
pip install 'markitdown[all]'
python3 llm-wiki/scripts/import_source.py my-paper.pdf ~/my-wiki --kind papers
```

然后告诉 Cursor：

```text
使用 llm-wiki skill，ingest raw/papers/my-paper.md
```

周期性检查：

```bash
python3 llm-wiki/scripts/lint_wiki.py ~/my-wiki
python3 llm-wiki/scripts/audit_review.py ~/my-wiki --open
```

## Web Viewer

默认地址：

```text
http://127.0.0.1:4875
```

手动启动：

```bash
cd audit-shared && npm install && npm run build && cd ..
cd web && npm install && npm run build
npm start -- --wiki "/path/to/your/wiki-root"
```

安装开机自启动：

```bash
cd web
npm run autostart:install -- --wiki "/path/to/your/wiki-root" --port 4875 --author "lym"
```

卸载自启动：

```bash
cd web
npm run autostart:uninstall
```

自启动行为：

- macOS：创建 `~/Library/LaunchAgents/com.llm-wiki.web.plist`
- Windows：创建当前用户的 Task Scheduler 登录任务 `LLM Wiki Web`
- 服务只绑定 `127.0.0.1`
- 不建议直接暴露到公网

## Obsidian 插件

构建并链接到 vault：

```bash
cd audit-shared && npm install && npm run build && cd ..
cd plugins/obsidian-audit
npm install
npm run build
npm run link -- "/path/to/your/Obsidian vault"
```

然后在 Obsidian 里启用：

```text
Settings → Community plugins → LLM Wiki Audit
```

插件命令：

- `Audit: Add feedback on selection`
- `Audit: List open feedback for current file`
- `Audit: Open audit folder`

## MarkItDown 导入器

项目内置 `llm-wiki/scripts/import_source.py`，但 MarkItDown 是可选依赖。

安装：

```bash
pip install 'markitdown[all]'
```

导入：

```bash
python3 llm-wiki/scripts/import_source.py "/path/to/source.pdf" "/path/to/wiki-root" --kind papers
```

可选 `--kind`：

- `articles`：网页、HTML、文章
- `papers`：论文、PDF、长文档
- `notes`：会议纪要、PPT、表格、杂项资料

MarkItDown 项目地址：[microsoft/markitdown](https://github.com/microsoft/markitdown)。

## 目录结构

```text
llm-wiki-skill/
├── llm-wiki/
│   ├── SKILL.md
│   ├── references/
│   │   ├── schema-guide.md
│   │   ├── article-guide.md
│   │   ├── log-guide.md
│   │   ├── audit-guide.md
│   │   └── tooling-tips.md
│   └── scripts/
│       ├── scaffold.py
│       ├── import_source.py
│       ├── import_source_test.py
│       ├── lint_wiki.py
│       └── audit_review.py
├── audit-shared/
├── plugins/obsidian-audit/
└── web/
```

生成后的 wiki 目录结构：

```text
<wiki-root>/
├── AGENTS.md
├── CLAUDE.md          # 内容为 @AGENTS.md
├── raw/
├── wiki/
├── audit/
├── log/
└── outputs/
```

## 使用场景

- 研究一个主题，持续吸收论文、文章、网页。
- 把 Obsidian vault 变成可由 Agent 维护的知识库。
- 用审计文件长期记录“AI 哪里写错了”。
- 为团队资料建立可追踪、可迭代的 wiki。

## 作者

lym [973007435@qq.com](mailto:973007435@qq.com)

GitHub: [kaerf15](https://github.com/kaerf15)

## License

MIT
