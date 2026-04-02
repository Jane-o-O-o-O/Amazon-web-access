# CrossBorder AI Copilot

面向跨境电商卖家的垂直 AI 工具：输入 1688/Alibaba 商品链接，自动完成竞品比对、利润测算与 Amazon Listing 生成。

---

## 一、项目目录结构

```
crossborder-ai-copilot/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # FastAPI 入口 + CORS
│   │   ├── config.py            # 配置（Pydantic Settings）
│   │   ├── database.py          # SQLAlchemy async engine
│   │   ├── models/              # ORM 数据模型
│   │   │   ├── product.py       # ProductRaw / ProductNormalized
│   │   │   ├── task.py          # AnalysisTask
│   │   │   ├── match.py         # ProductMatch
│   │   │   ├── competitor.py    # CompetitorReport
│   │   │   ├── margin.py        # MarginCalculation
│   │   │   └── listing.py       # ListingDraft
│   │   ├── routers/             # API 路由
│   │   │   ├── tasks.py         # POST /api/tasks/product-analysis
│   │   │   ├── listings.py      # POST /api/listings/regenerate
│   │   │   └── export.py        # GET /api/export/tasks/{id}/csv|json
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── crawler.py       # 页面抓取（web-access + httpx 兜底）
│   │   │   ├── parser.py        # 商品结构化解析
│   │   │   ├── matcher.py       # 匹配打分 + 排名
│   │   │   ├── analyzer.py      # 竞品分析
│   │   │   ├── pricing.py       # 利润测算
│   │   │   └── listing.py       # Listing 生成
│   │   ├── ai/                  # Claude 集成
│   │   │   ├── client.py        # Anthropic SDK 调用 + web-access
│   │   │   └── prompts.py       # 所有 Prompt 模板
│   │   └── worker/
│   │       └── tasks.py         # Celery 异步任务（完整 pipeline）
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                    # Next.js 14 前端
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # 首页：输入链接 + 成本参数
│   │   │   ├── tasks/[taskId]/
│   │   │   │   ├── page.tsx     # 结果页（比对+利润+Listing）
│   │   │   │   └── progress/    # 进度等待页（自动轮询跳转）
│   │   │   └── batch/page.tsx   # 批量任务页
│   │   ├── components/
│   │   │   ├── TaskProgress.tsx  # 进度条 + 阶段展示
│   │   │   ├── ProductCard.tsx   # 商品信息卡片
│   │   │   ├── MatchResults.tsx  # Amazon 候选商品列表
│   │   │   ├── ProfitCalculator.tsx  # 利润拆解卡片
│   │   │   └── ListingEditor.tsx # Listing 预览 + 一键再生成
│   │   ├── lib/
│   │   │   ├── api.ts            # Axios API 客户端
│   │   │   └── utils.ts          # cn / formatUSD / matchLevelColor
│   │   └── types/index.ts        # 完整 TypeScript 类型定义
│   ├── Dockerfile
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── package.json
│
├── infra/
│   └── init.sql                 # PostgreSQL 建表 SQL
├── docker-compose.yml
└── README.md
```

---

## 二、技术选型

| 层次 | 选型 |
|---|---|
| 前端 | Next.js 14 · TypeScript · Tailwind CSS · shadcn/ui · TanStack Query |
| 后端 | FastAPI · SQLAlchemy 2 (async) · Pydantic v2 |
| AI | Claude (claude-sonnet-4-6) · web_search tool (web-access) |
| 数据库 | PostgreSQL 16 |
| 缓存/任务 | Redis 7 · Celery 5 |
| 导出 | pandas · openpyxl |
| 容器 | Docker Compose |

---

## 三、核心 API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/tasks/product-analysis` | 创建分析任务，返回 taskId |
| GET | `/api/tasks/{taskId}` | 查询任务状态 + 进度 |
| GET | `/api/tasks/{taskId}/result` | 获取完整分析结果 |
| POST | `/api/listings/regenerate` | 重新生成 Listing |
| GET | `/api/export/tasks/{taskId}/csv` | 导出 CSV |
| GET | `/api/export/tasks/{taskId}/json` | 导出 JSON |
| GET | `/health` | 健康检查 |

---

## 四、核心流程时序

```
用户输入链接
    │
    ▼
POST /api/tasks/product-analysis  ← 返回 taskId (立即)
    │
    ▼  [Celery Worker 异步执行]
1. crawl_product_page()      ← Claude web-access 抓取原始页面
2. parse_product_page()      ← Claude LLM 结构化解析
3. search_amazon_candidates()← Claude web-access 搜索 Amazon
4. rank_candidates()         ← Claude LLM 逐一匹配打分
5. run_competitor_analysis() ← Claude LLM 竞品报告
6. calculate_margin()        ← 纯公式计算（无 LLM）
7. create_listing()          ← Claude LLM 生成 Listing
    │
    ▼
结果写入 Redis (TTL 24h)
    │
    ▼  [前端轮询]
GET /api/tasks/{taskId}           ← progress 0→100 + stage
GET /api/tasks/{taskId}/result    ← 完整结果 JSON
```

---

## 五、快速启动

### 前置要求
- Docker & Docker Compose
- Anthropic API Key（支持 web_search tool）

### 启动

```bash
# 1. 复制并填写环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 ANTHROPIC_API_KEY

cp frontend/.env.local.example frontend/.env.local

# 2. 启动全部服务
docker compose up --build

# 前端: http://localhost:3000
# 后端: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 本地开发（不用 Docker）

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Celery Worker（新终端）
celery -A app.worker.tasks.celery_app worker --loglevel=info

# 前端（新终端）
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

---

## 六、MVP 页面说明

| 页面 | 路径 | 说明 |
|---|---|---|
| 首页/输入页 | `/` | 输入商品 URL + 成本参数，一键提交分析 |
| 进度页 | `/tasks/[taskId]/progress` | 实时进度条 + 阶段说明，完成后自动跳转 |
| 结果页 | `/tasks/[taskId]` | 源商品信息、竞品比对列表、利润卡片、Listing 编辑器、导出 |
| 批量页 | `/batch` | CSV 上传批量处理（Phase 2 完整实现） |

---

## 七、后续扩展方向

- **Phase 2**：Alibaba 全支持、批量导入、差评聚类、Listing 编辑器增强
- **Phase 3**：Amazon Seller API 接入、多市场模板、团队账号系统