# 跨境电商商品比对与 Listing 生成助手

## 1. 项目概述

### 1.1 项目名称
CrossBorder AI Copilot（可后续再改名）

### 1.2 项目定位
这是一个面向跨境电商卖家的垂直 AI 应用。用户输入 1688、Alibaba、Amazon 等平台的商品链接、关键词或图片后，系统自动完成以下工作：

- 抓取商品信息
- 识别同款或近似款
- 做跨平台商品比对
- 估算利润空间
- 生成适用于 Amazon 的英文 Listing
- 输出竞品分析与选品建议

### 1.3 核心目标
本项目的目标不是做一个泛用聊天机器人，而是做一个可直接服务跨境电商卖家的业务工具。重点放在三个闭环：

1. **比对**：识别供应链商品与 Amazon 商品是否同款或相似款  
2. **分析**：给出价格、评分、规格、差评、利润等维度的业务分析  
3. **生成**：自动生成可用于 Amazon 上架的 Listing 内容

### 1.4 目标用户
- Amazon 卖家
- 跨境电商选品运营
- 跨境电商创业团队
- 采购与供应链人员
- 独立站卖家（后续可扩展）

### 1.5 使用场景

#### 场景一：1688 找货，对 Amazon 上是否已有竞品进行比对
用户输入一个 1688 商品链接，系统自动搜索 Amazon 同类商品，返回相似商品列表、价格、评分、评论量、利润测算。

#### 场景二：已有 Amazon 竞品，反查供应链与优化空间
用户输入 Amazon ASIN 或链接，系统分析竞品卖点、差评、关键词，再结合供应链商品生成优化版 Listing。

#### 场景三：批量选品
用户上传多个商品链接，系统批量输出比对结果和利润估算表。

#### 场景四：快速生成 Listing
用户输入商品参数与目标市场，系统输出英文标题、五点描述、长描述、搜索词等内容。

---

## 2. 产品能力边界

### 2.1 第一阶段聚焦范围（MVP）
第一阶段只聚焦以下能力：

- 单商品链接输入
- Amazon 商品搜索与比对
- 结构化商品信息抽取
- 商品匹配评分
- 利润测算
- Listing 生成
- 分析报告导出

### 2.2 暂不纳入第一阶段的能力
以下能力放到第二阶段或第三阶段：

- 直接接入 Amazon 卖家后台进行发布
- 自动刊登到 Seller Central
- 自动调价
- 自动库存同步
- 多人协作
- 多租户权限系统
- 多平台深度 ERP 集成

---

## 3. 总体产品方案

### 3.1 输入方式
支持以下几类输入：

1. 单个链接输入
   - 1688 商品链接
   - Alibaba 商品链接
   - Amazon 商品链接
2. 关键词输入
   - 例如："portable blender"、"pet grooming glove"
3. 批量输入
   - Excel / CSV 导入多个商品链接
4. 图片输入（后续扩展）
   - 以图搜货 / 以图搜 Amazon 竞品

### 3.2 输出内容
系统输出包括：

#### 3.2.1 商品基础信息
- 标题
- 平台
- 链接
- 主图
- 价格
- MOQ
- 规格
- 材质
- 尺寸
- 变体信息
- 发货地

#### 3.2.2 商品匹配结果
- 候选 Amazon 商品列表
- 匹配分（0-100）
- 匹配理由
- 差异字段说明

#### 3.2.3 竞品比对结果
- 售价对比
- 评论量对比
- 评分对比
- 规格差异
- 卖点差异
- 差评主题
- 关键词差异

#### 3.2.4 利润测算
- 采购价
- 国内运费
- 国际头程
- 平台佣金
- FBA 费用
- 广告成本
- 税费
- 毛利率
- 净利率
- 建议售价区间

#### 3.2.5 Listing 生成
- 标题 Title
- 五点描述 Bullet Points
- 商品长描述 Description
- 后台搜索词 Search Terms
- 图片卖点文案建议
- A+ 模块文案草稿（后续）

#### 3.2.6 分析结论
- 是否值得上架
- 价格竞争力判断
- 差异化建议
- 卖点提炼建议
- 风险提示

---

## 4. 核心功能设计

## 4.1 功能一：商品抓取与结构化抽取

### 4.1.1 功能描述
系统接收商品链接后，自动打开商品页面，提取页面中的商品核心信息，并标准化为统一结构。

### 4.1.2 支持平台
- 1688
- Alibaba
- Amazon
- 独立站（Shopify 类页面，后续）

### 4.1.3 需要抽取的字段
- 商品标题
- 主图与图片列表
- 价格与价格梯度
- SKU / 变体
- 规格参数
- 材质
- 尺寸
- 颜色
- MOQ
- 店铺名
- 发货地
- 评分与评论数（适用于 Amazon）
- 卖点描述
- 详情描述

### 4.1.4 处理策略
采用“规则抽取 + LLM 补全抽取”的双层方案：

1. 优先用页面选择器、HTML 解析、结构化脚本解析
2. 若字段缺失，则用 LLM 结合 DOM 文本补充抽取
3. 抽取结果统一映射为内部标准字段

---

## 4.2 功能二：Amazon 候选商品搜索

### 4.2.1 功能描述
根据输入商品的标题、属性、关键词，在 Amazon 搜索同类商品，召回多个候选商品。

### 4.2.2 搜索策略
- 关键词搜索
- 标题改写搜索
- 属性组合搜索
- 品类词扩展搜索

### 4.2.3 候选召回数量
默认召回 10-30 个候选商品，后续再 rerank 到前 5-10 个。

---

## 4.3 功能三：商品匹配评分

### 4.3.1 功能描述
对供应链商品与 Amazon 候选商品进行同款/近似款判断，并输出匹配分。

### 4.3.2 匹配维度
- 标题语义相似度
- 类目一致性
- 规格属性重合度
- 材质一致性
- 尺寸一致性
- 套装数量一致性
- 图片相似度（后续）
- 价格区间合理性
- 品牌约束

### 4.3.3 匹配分计算建议
可以设计为：

```text
match_score =
  0.35 * title_similarity +
  0.25 * attribute_overlap +
  0.15 * category_match +
  0.10 * material_match +
  0.10 * size_match +
  0.05 * price_reasonableness
```

### 4.3.4 输出内容
- 匹配分
- 是否判定为同款 / 高相似 / 中相似 / 低相似
- 关键相似点
- 关键差异点

---

## 4.4 功能四：竞品分析

### 4.4.1 功能描述
针对候选 Amazon 商品，生成业务可读的竞品分析结果。

### 4.4.2 分析维度
- 价格带
- 评论量
- 星级
- 主图风格
- 标题关键词
- Bullet 卖点
- 差评主题
- 变体布局
- 品牌信息

### 4.4.3 输出形式
- 表格对比
- AI 总结段落
- 差异化建议

### 4.4.4 竞品结论示例
- 当前竞品主要集中在 19.99-24.99 美元价位
- 评论高频差评集中在“材质薄”“容量偏小”“密封性一般”
- 若供应链能解决密封性与容量问题，可作为差异化切入点

---

## 4.5 功能五：利润测算

### 4.5.1 功能描述
用户输入成本参数后，系统自动测算毛利和净利。

### 4.5.2 输入参数
- 采购价
- 国内运费
- 国际头程
- Amazon 平台佣金比例
- FBA 费用
- 广告占比
- 税费比例
- 汇率

### 4.5.3 输出结果
- 到岸成本
- 单件总成本
- 建议售价
- 毛利额
- 毛利率
- 净利额
- 净利率

### 4.5.4 利润公式示例
```text
总成本 = 采购价 + 国内运费 + 国际头程 + FBA费用 + 税费 + 广告成本
毛利 = 销售价 - 平台佣金 - 总成本
毛利率 = 毛利 / 销售价
```

---

## 4.6 功能六：Listing 自动生成

### 4.6.1 功能描述
根据商品属性、竞品信息和目标市场，自动生成适合 Amazon 的英文 Listing。

### 4.6.2 生成内容
- 标题（Title）
- 五点描述（Bullet Points）
- 长描述（Description）
- 后台搜索词（Search Terms）
- 图片文案建议

### 4.6.3 输入上下文建议
给大模型的上下文应包括：
- 商品真实规格
- 商品用途
- 目标用户群
- Amazon 竞品标题与卖点
- 高频关键词
- 高频差评问题
- 禁用词/合规词
- 风格要求

### 4.6.4 生成要求
- 避免虚假描述
- 避免夸张宣传
- 避免未证实的医疗/功能性表述
- 优先突出真实可验证卖点
- 标题尽量覆盖核心搜索词

---

## 5. 用户流程设计

## 5.1 单商品分析流程

```text
用户输入 1688/Alibaba 链接
→ 系统抓取商品信息
→ 系统搜索 Amazon 候选商品
→ 系统做匹配打分
→ 系统输出候选比对结果
→ 用户选择目标竞品或直接分析全部候选
→ 系统生成利润测算
→ 系统生成 Listing
→ 用户导出结果
```

## 5.2 Amazon 竞品反查流程

```text
用户输入 Amazon 链接或 ASIN
→ 系统抓取 Amazon 商品信息
→ 系统提取标题/卖点/评论摘要
→ 系统分析差评主题与关键词
→ 系统输出优化建议
→ 用户补充供应链商品参数
→ 系统生成优化版 Listing
```

## 5.3 批量分析流程

```text
用户上传 Excel
→ 系统逐条抓取商品信息
→ 系统异步处理 Amazon 搜索与比对
→ 系统生成批量结果表
→ 用户下载 Excel/CSV
```

---

## 6. 技术架构设计

## 6.1 总体架构
采用前后端分离 + AI 调度服务 + 抓取服务 + 结构化分析服务。

### 6.1.1 架构分层

#### 前端层
- Web 控制台
- 结果展示页面
- 表格与分析报告界面

#### API 层
- 用户请求入口
- 任务创建
- 商品分析接口
- Listing 生成接口
- 导出接口

#### AI 调度层
- 调用 Claude
- 调用 web-access
- prompt orchestration
- 多步骤任务编排

#### 页面抓取层
- web-access
- Playwright/CDP 兜底
- 页面 HTML/DOM 抽取

#### 业务分析层
- 商品结构化抽取
- 匹配评分
- 竞品分析
- 利润测算
- Listing 生成

#### 数据存储层
- PostgreSQL
- Redis
- 对象存储（图片、导出文件）

---

## 6.2 推荐技术栈

### 前端
- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query

### 后端
- FastAPI（推荐）或 NestJS
- Python 更适合做抽取、匹配、文本分析

### AI / Agent 相关
- Claude
- web-access
- 可选 embedding 模型
- 可选 rerank 模型

### 抓取与自动化
- web-access 作为主入口
- Playwright 作为兜底
- BeautifulSoup / lxml 用于静态解析

### 数据层
- PostgreSQL
- Redis
- pgvector（后续相似度检索可用）

### 异步任务
- Celery / RQ / Dramatiq
- 或者 FastAPI + Redis Queue

### 文件导出
- pandas / openpyxl
- reportlab 或前端导出 PDF

---

## 7. 与 Claude 和 web-access 的集成方案

## 7.1 Claude 的职责
Claude 主要负责：

- 多步任务规划
- 页面内容理解
- 结构化字段补全
- 商品相似性分析
- 竞品摘要生成
- Listing 文案生成
- 风险点和业务建议生成

## 7.2 web-access 的职责
web-access 主要负责：

- 搜索网页
- 打开商品页
- 动态页面访问
- 页面交互
- 抓取页面内容
- 并行访问多个候选商品页

## 7.3 推荐调用模式
采用“后端主控、Claude 辅助”的模式，而不是让 Claude 直接无边界自由发挥。

### 推荐流程
1. 后端接收任务
2. 后端调用 web-access 抓页面
3. 后端先做一次基础解析
4. 再把解析结果 + 原始片段交给 Claude
5. Claude 输出结构化结果与分析文本
6. 后端对输出做校验、落库、返回前端

这样做的好处是：
- 可控
- 易调试
- 易缓存
- 易扩展
- 降低 LLM 幻觉风险

---

## 8. 后端模块设计

## 8.1 模块划分

### 8.1.1 task 模块
负责创建与跟踪任务。

### 8.1.2 crawler 模块
负责页面抓取、HTML 获取、内容快照。

### 8.1.3 parser 模块
负责结构化解析商品字段。

### 8.1.4 matcher 模块
负责候选召回、匹配打分、排序。

### 8.1.5 analyzer 模块
负责竞品分析、差评总结、关键词提炼。

### 8.1.6 pricing 模块
负责利润计算。

### 8.1.7 listing 模块
负责 Listing 文案生成与改写。

### 8.1.8 export 模块
负责导出 Excel、CSV、PDF。

---

## 9. 数据模型设计

## 9.1 products_raw
原始抓取商品表

字段建议：
- id
- source_platform
- source_url
- source_id
- raw_html_path
- raw_json
- created_at
- updated_at

## 9.2 products_normalized
标准化商品表

字段建议：
- id
- raw_product_id
- platform
- title
- brand
- category
- price_min
- price_max
- currency
- moq
- material
- size
- color
- package_quantity
- attributes_json
- images_json
- rating
- review_count
- seller_name
- ship_from
- normalized_text
- created_at
- updated_at

## 9.3 product_matches
商品匹配结果表

字段建议：
- id
- source_product_id
- target_product_id
- match_score
- match_level
- similarity_breakdown_json
- match_reason
- diff_summary
- created_at

## 9.4 competitor_reports
竞品分析表

字段建议：
- id
- source_product_id
- report_json
- summary_text
- pain_points_json
- keywords_json
- created_at

## 9.5 margin_calculations
利润测算表

字段建议：
- id
- product_id
- cost_purchase
- domestic_shipping
- international_shipping
- fba_fee
- commission_fee
- ads_cost
- tax_cost
- exchange_rate
- sell_price
- gross_profit
- net_profit
- gross_margin
- net_margin
- created_at

## 9.6 listing_drafts
Listing 草稿表

字段建议：
- id
- product_id
- market
- language
- title
- bullets_json
- description
- search_terms
- image_copy_json
- version
- created_at

---

## 10. API 设计建议

## 10.1 创建单商品分析任务
`POST /api/tasks/product-analysis`

请求体：
```json
{
  "sourceUrl": "https://detail.1688.com/...",
  "targetMarketplace": "amazon-us",
  "cost": {
    "purchasePrice": 2.5,
    "domesticShipping": 0.2,
    "internationalShipping": 1.0,
    "fbaFee": 3.2,
    "commissionRate": 0.15,
    "adsRate": 0.08,
    "taxRate": 0.03,
    "exchangeRate": 7.2
  }
}
```

返回：
```json
{
  "taskId": "task_xxx",
  "status": "queued"
}
```

## 10.2 查询任务状态
`GET /api/tasks/{taskId}`

返回：
```json
{
  "taskId": "task_xxx",
  "status": "running",
  "progress": 65,
  "stage": "matching"
}
```

## 10.3 获取分析结果
`GET /api/tasks/{taskId}/result`

返回内容包含：
- source product
- candidates
- match result
- competitor report
- profit calculation
- listing draft

## 10.4 重新生成 Listing
`POST /api/listings/regenerate`

请求体：
```json
{
  "productId": "prod_xxx",
  "market": "amazon-us",
  "tone": "professional",
  "keywordFocus": ["portable blender", "travel smoothie maker"]
}
```

## 10.5 批量导入分析任务
`POST /api/tasks/batch-import`

支持 Excel/CSV 上传。

---

## 11. 前端页面设计

## 11.1 页面一：首页 / 输入页
功能：
- 输入单个商品链接
- 输入关键词
- 上传 Excel
- 选择目标市场
- 填写成本参数

## 11.2 页面二：任务结果页
模块：
- 原商品信息卡片
- Amazon 候选商品列表
- 匹配分排序
- 竞品对比表
- 差异说明
- 利润卡片
- Listing 草稿区

## 11.3 页面三：批量任务页
模块：
- 上传历史
- 任务状态列表
- 批量分析结果表
- 下载按钮

## 11.4 页面四：Listing 编辑页
模块：
- Title 编辑
- Bullet 编辑
- Description 编辑
- Search Terms 编辑
- 一键再生成

---

## 12. AI Prompt 设计建议

## 12.1 商品结构化抽取 Prompt
目标：从网页内容中提取标准字段。

输出结构要求：
- JSON 格式
- 缺失字段置空
- 不允许虚构不存在的信息

## 12.2 商品比对 Prompt
目标：分析两个商品是否为同款或高相似商品。

输出结构建议：
- match_score
- match_level
- same_points
- diff_points
- final_reason

## 12.3 竞品分析 Prompt
目标：总结多个 Amazon 商品的共性卖点、差评主题、机会点。

输出结构建议：
- market_summary
- top_features
- complaint_topics
- pricing_range
- differentiation_suggestions

## 12.4 Listing 生成 Prompt
目标：根据真实商品属性和竞品洞察，生成 Amazon Listing。

要求：
- 英文输出
- 贴近 Amazon 风格
- 基于真实信息
- 覆盖核心关键词
- 不虚构认证、材质、功能

---

## 13. 缓存与任务策略

## 13.1 缓存建议
为了降低抓取和 LLM 成本，建议做以下缓存：

- URL 级页面抓取缓存
- 商品结构化结果缓存
- Amazon 搜索结果缓存
- Listing 生成结果缓存

## 13.2 异步任务建议
下列操作建议异步执行：
- 抓取多个候选商品页
- 批量分析
- 差评主题聚类
- 批量导出

---

## 14. 错误处理与兜底策略

### 14.1 页面无法打开
- 重试
- 切换抓取模式
- 降级使用静态抓取
- 给前端返回失败原因

### 14.2 页面字段缺失
- 启动 LLM 补提取
- 若仍缺失则标记缺失字段

### 14.3 Amazon 候选召回过少
- 自动扩展搜索词
- 放宽类目限制
- 改写标题重搜

### 14.4 LLM 输出不规范
- 使用 JSON schema 校验
- 自动重试
- 使用后端兜底修复

---

## 15. 合规与风控建议

需要注意：
- 不要在产品上宣传“保证通过 Amazon 审核”
- 不要自动生成违规或夸大宣传文案
- 不要无限制高频抓取目标站点
- 对登录态页面和账号行为要谨慎控制
- 对 AI 输出增加人工确认环节

---

## 16. MVP 开发计划

## 阶段一：最小可用版本
目标：跑通单商品分析闭环。

### 功能范围
- 输入 1688 链接
- 抽取商品信息
- 搜索 Amazon 候选商品
- 做匹配打分
- 输出利润测算
- 生成英文 Listing

### 交付标准
- 前端可输入链接
- 后端可创建任务
- 页面可展示分析结果
- 支持导出 JSON/CSV

## 阶段二：增强版
- 支持 Alibaba
- 支持批量导入
- 增加差评主题分析
- 增加关键词提炼
- 增加 Listing 编辑器

## 阶段三：业务化版本
- 接入 Amazon 官方卖家 API
- 支持刊登草稿管理
- 支持多市场模板
- 增加团队账号系统

---

## 17. 给 Claude 的开发要求

下面是直接给 Claude 的要求：

### 开发目标
请基于本说明书，开发一个 Web 应用，核心能力是：
- 输入跨境电商商品链接
- 自动抓取并结构化商品信息
- 自动搜索 Amazon 候选竞品
- 自动做商品匹配与竞品分析
- 自动生成利润测算与 Amazon Listing

### 技术要求
- 前端使用 Next.js + TypeScript + Tailwind + shadcn/ui
- 后端使用 FastAPI
- 使用 Claude 作为主要大模型
- 集成 web-access 作为网页搜索与访问能力
- 使用 PostgreSQL 保存业务数据
- 使用 Redis 作为缓存与任务队列辅助

### 开发要求
1. 先实现 MVP 版本
2. 所有核心逻辑按模块分层
3. 提供清晰的目录结构
4. 提供可扩展的数据模型
5. 页面风格简洁专业，偏 SaaS 工具风格
6. 尽量把 AI 输出结构化，不要只返回纯文本
7. 对任务处理增加状态追踪
8. 提供 mock 数据和示例页面

### 首批需要产出的内容
请优先输出以下内容：
1. 项目目录结构
2. 数据库表设计 SQL 或 ORM 模型
3. 后端接口设计
4. 前端页面结构
5. 核心流程时序图
6. MVP 版本代码骨架

---

## 18. 一句话总结

这个项目本质上是一个面向跨境电商卖家的垂直 AI 业务工具，核心不是闲聊，而是围绕“商品比对、竞品分析、利润测算、Listing 生成”四个业务动作，形成真正可落地的工作流。

