# llm-wiki

**面向多种 Agent 工具（Cursor、Trae、Claude Code 等）的 LLM Wiki Skill。**

它把资料先沉淀成一个长期维护的 Markdown 知识库，再让 Agent 持续执行 `compile`、`ingest`、`query`、`lint`、`audit`。这不是传统 RAG 每次重新检索原文，而是让 LLM 把原始资料编译成可交叉链接、可审计、可迭代的 wiki。

本项目基于 [lewislulu/llm-wiki-skill](https://github.com/lewislulu/llm-wiki-skill) 改造，适配通用 Agent 工作流：skill 安装在 `.agents/skills/`、wiki 使用标准 Markdown 链接、本地 Web viewer 提供阅读体验（反向链接、知识图谱、反馈入口）。

灵感来自 [Andrej Karpathy 的 llm-wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)。

## 这个项目解决什么

你负责提供资料、提出问题、指出 AI 写错的地方。Agent 负责读资料、写 wiki、维护链接、更新索引、处理反馈。

项目里包含两部分：

- `llm-wiki/`：Agent skill，定义 wiki 结构和五类操作。
- `web/`：本地预览服务，渲染 Markdown、Mermaid、KaTeX，提供反向链接与知识图谱，可在浏览器里提交反馈到 `audit/`。

## 极简部署流程

1. 安装前置依赖：Python 3、Node.js 20+、Git。
2. 创建一个普通文件夹作为 wiki 根目录。
3. 用 Cursor / Trae 等 Agent 工具打开该文件夹。
4. 把下面「一键部署提示词」发给 Agent。
5. Agent 会自动下载本项目、初始化 wiki、安装 skill；Web viewer 若本机尚未部署才安装，已部署则只注册当前 wiki。

## 推荐安装位置

工具代码不要放进 wiki 知识库里。

```text
工具代码:
macOS:   ~/Library/Application Support/llm-wiki/
Windows: %LOCALAPPDATA%\llm-wiki\

知识库:
任意目录，例如 ~/Documents/my-wiki/
```

部署完成后保留：

- `web/` 和 `audit-shared/` → 用户级应用目录
- `llm-wiki/` skill → `<WIKI_ROOT>/.agents/skills/llm-wiki/`
- 临时 clone → 删除

## 前置依赖

- Python 3：`scaffold.py`、`lint_wiki.py`、`audit_review.py`、`import_source.py`
- Node.js 20+：`web/` 构建与运行
- Git：从 GitHub 下载本项目
- MarkItDown（可选）：导入 PDF、Office、HTML

```bash
python3 --version
node -v
npm -v
git --version
```

## 一键部署提示词

先用 Agent 打开 wiki 根目录，复制下面整段提示词：

```text
请在当前 workspace（Wiki 根目录）里部署 llm-wiki。

请严格按下面要求执行：
- 当前 workspace 就是 WIKI_ROOT。
- 不要把 web/、audit-shared/ 复制到 WIKI_ROOT 里。
- 需要把 llm-wiki skill 安装到：<WIKI_ROOT>/.agents/skills/llm-wiki/
- 从 GitHub 下载：https://github.com/kaerf15/llm-wiki-skill-v2
- clone 只作临时安装源，部署完成后必须删除。
- 运行组件在用户级 APP_ROOT（Web 是全局共享，多个 wiki 共用同一个 viewer）。
- Web 端口：4875
- 作者：lym

参数：
- REPO_URL=https://github.com/kaerf15/llm-wiki-skill-v2
- WIKI_ROOT=当前 workspace 根目录
- APP_ROOT=用户级应用目录下的 llm-wiki
- WIKIS_CONFIG=<APP_ROOT>/wikis.json
- TEMP_CLONE=系统临时目录下的 llm-wiki-skill-v2 clone
- PORT=4875
- AUTHOR=lym

部署原则（重要）：
- Web viewer 是用户级全局服务，多个 wiki 共用；不要每次部署 wiki 都重装 Web。
- 若检测到 Web 已部署且可用，跳过 Web 迁移/构建/自启动，只做 wiki 侧工作。
- 每个 WIKI_ROOT 仍需安装/更新 skill，并把路径注册进 wikis.json。

「Web 已部署」判定（满足即可跳过 Web 重装）：
- <APP_ROOT>/web 与 <APP_ROOT>/audit-shared 存在
- http://127.0.0.1:4875/api/config 可访问
- （可选）macOS LaunchAgent com.llm-wiki.web 或 Windows 任务 LLM Wiki Web 已存在

目标：
1. 检查前置依赖：python3、node 20+、npm、git。缺失则停止并说明。
2. 确认 WIKI_ROOT 是真实目录；确定 APP_ROOT 与 WIKIS_CONFIG。
3. clone REPO_URL 到 TEMP_CLONE（不要 clone 到 WIKI_ROOT）。
4. 若 WIKI_ROOT 尚无 llm-wiki 结构，运行：
   python3 <TEMP_CLONE>/llm-wiki/scripts/scaffold.py "<WIKI_ROOT>" "My Knowledge Base"
5. 安装/更新 skill（每次部署 wiki 都要做）：
   - 创建 <WIKI_ROOT>/.agents/skills
   - 复制 <TEMP_CLONE>/llm-wiki 到 <WIKI_ROOT>/.agents/skills/llm-wiki
   - 若已存在则先删旧版再复制最新版
6. 检测 Web 是否已部署（见上文判定）：
   - 若已部署：跳过步骤 7–8，仅执行步骤 9 把 WIKI_ROOT 注册进 wikis.json
   - 若未部署：执行步骤 7–9 完整安装 Web
7. 【仅 Web 未部署时】迁移 Web runtime 到 APP_ROOT：
   - 创建 APP_ROOT
   - 复制 audit-shared/ 和 web/ 到 APP_ROOT
8. 【仅 Web 未部署时】构建并安装自启动：
   cd <APP_ROOT>/audit-shared && npm install && npm run build
   cd <APP_ROOT>/web && npm install && npm run build
   npm run autostart:install -- --wiki "<WIKI_ROOT>" --port 4875 --author "lym"
9. 注册当前 wiki 到 wikis.json（已部署或未部署都要做）：
   - 若 WIKI_ROOT 尚未在 wikis.json 中，运行：
     cd <APP_ROOT>/web && npm run autostart:install -- --wiki "<WIKI_ROOT>" --port 4875 --author "lym"
   - autostart:install 会合并写入 wikis.json，不会重复注册同一路径
10. 安装 MarkItDown（若尚未安装）：
    python3 -m pip install --user 'markitdown[all]'
11. 验证：
    - http://127.0.0.1:4875 可访问
    - /api/config 的 wikis 列表包含当前 WIKI_ROOT
    - <WIKI_ROOT>/AGENTS.md 存在
    - <WIKI_ROOT>/.agents/skills/llm-wiki/SKILL.md 存在
12. 验证通过后删除 TEMP_CLONE。
13. 汇报：Web 是否跳过重装、Web 地址、APP_ROOT、wikis.json 路径、skill 路径、当前 wiki 是否已注册。
```

## 手动快速开始

```bash
python3 llm-wiki/scripts/scaffold.py ~/my-wiki "My Research Topic"
cp -r llm-wiki ~/.agents/skills/llm-wiki   # 或复制到 ~/my-wiki/.agents/skills/llm-wiki
```

导入非 Markdown 资料：

```bash
python3 -m pip install --user 'markitdown[all]'
python3 llm-wiki/scripts/import_source.py my-paper.pdf ~/my-wiki --kind papers
```

告诉 Agent：

```text
使用 llm-wiki skill，ingest raw/papers/my-paper.md
```

健康检查：

```bash
python3 llm-wiki/scripts/lint_wiki.py ~/my-wiki
python3 llm-wiki/scripts/audit_review.py ~/my-wiki --open
```

## 链接格式

Wiki 内容使用标准 Markdown 链接：

```markdown
[Transformers](wiki/concepts/Transformers.md)
[Andrej Karpathy](wiki/entities/Andrej%20Karpathy.md)
```

Web viewer 负责阅读体验：只显示链接文字、SPA 内导航、反向链接、知识图谱、死链高亮。

## Web Viewer

默认地址：`http://127.0.0.1:4875`

支持**多个 wiki**：路径写在 `wikis.json`，顶栏下拉框切换。

配置文件位置（autostart 默认写入）：

```text
macOS:   ~/Library/Application Support/llm-wiki/wikis.json
Windows: %LOCALAPPDATA%\llm-wiki\wikis.json
Linux:   ~/.config/llm-wiki/wikis.json
```

示例见 `web/wikis.example.json`：

```json
{
  "defaultWikiId": "research",
  "wikis": [
    { "id": "research", "name": "AI Research", "path": "/Users/you/wikis/research" },
    { "id": "work", "name": "Work Notes", "path": "/Users/you/wikis/work" }
  ]
}
```

手动启动（单个 wiki）：

```bash
cd audit-shared && npm install && npm run build && cd ..
cd web && npm install && npm run build
npm start -- --wiki "/path/to/wiki-root"
```

多个 wiki：

```bash
npm start -- --wiki ~/wikis/research --wiki ~/wikis/work
# 或使用配置文件
npm start -- --wikis-config ~/Library/Application\ Support/llm-wiki/wikis.json
```

URL 深链：`http://127.0.0.1:4875/?wiki=research&page=wiki/index.md`

安装自启动（可重复 `--wiki` 追加到 wikis.json）：

```bash
cd web
npm run autostart:install -- --wiki "/path/to/wiki-a" --wiki "/path/to/wiki-b" --port 4875 --author "lym"
```

## MarkItDown 导入器

```bash
python3 llm-wiki/scripts/import_source.py "/path/to/source.pdf" "/path/to/wiki-root" --kind papers
```

可选 `--kind`：`articles` · `papers` · `notes`

## 目录结构

```text
llm-wiki-skill/
├── llm-wiki/           # Agent skill
├── audit-shared/       # 审计 schema（web 使用）
└── web/                # 本地预览服务

<wiki-root>/
├── AGENTS.md
├── CLAUDE.md
├── .agents/skills/llm-wiki/
├── raw/
├── wiki/
├── audit/
├── log/
└── outputs/
```

## 使用场景

- 研究一个主题，持续吸收论文、文章、网页
- 用 Agent 维护可交叉引用的个人/团队知识库
- 用 audit 长期记录「AI 哪里写错了」
- 在浏览器里浏览 wiki、查看反向链接和知识图谱

## 作者

lym [973007435@qq.com](mailto:973007435@qq.com) · GitHub: [kaerf15](https://github.com/kaerf15)

## License

MIT
