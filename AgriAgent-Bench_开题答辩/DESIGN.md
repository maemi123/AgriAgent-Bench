# DESIGN.md — AgriAgent-Bench 开题答辩

## 一、全局视觉约定

### ① 画布与安全区
- 画布 1280×720
- padding：上下 60px / 左右 60px
- 内容区 1160×600
- 页脚：顶边 y=670，左右受 60px 安全区约束，14px，灰色
- 顶条：高 64px，全宽，深蓝实色；左侧主标题白色 32px Bold，右侧章节标识 16px
- 封面 / 结束页不加顶条与页脚

### ② 配色
| 槽位 | Hex | 用途 |
|---|---|---|
| 主色 | `#1E4FA8` | 顶条、编号块、强调线、主标题 |
| 辅色 | `#3D7BD9` | 图表第二序列、次级强调 |
| 浅辅 | `#E8EFF8` | 结论条底、表头底、卡片底（≤2 处/页） |
| 强调 | `#D9534F` | 关键发现、异常值（全篇 ≤3 处/页，总量稀缺） |
| 正文 | `#1A2230` | 主文字 |
| 次级 | `#4A5568` | 说明文字 |
| 弱化 | `#8B97A8` | 注释、来源 |
| 分隔 | `#D6DCE5` | 1px 细线、表格边框 |
| 底色 | `#FFFFFF` | 主背景（≥60%） |

纪律：蓝族 20-40%；红 ≤3%；金色 = 0；白底 ≥60%。

### ③ 字体与字号
- 中文：思源黑体（SimHei 兜底）；数字英文：Arial
- 封面主标 54px Bold｜页主标题 32px Bold｜卡内小标题 22px Bold
- 正文 20px / 行高 1.5｜表格 17px｜注释页脚 14px
- KPI 巨数字 64px Bold（单位 18px，右侧底部对齐）

### ④ 视觉母题
全篇统一：**顶部 64px 深蓝标题条 + 标题条左侧 6px 白色竖条**；内容页正文区顶部统一用一条 1px `#D6DCE5` 贯通细线分隔（位于顶条下方 0px）。

### ⑤ 配图清单
本 deck 不使用照片类配图（学术开题以图表与结构图为主），全部视觉元素用原生 Box / Chart / Table / SVG 绘制，保证矢量清晰与可编辑。

---

## 二、页面清单（15 页）

| # | 标题 | type | role | rhythm | layout | 说明 |
|---|---|---|---|---|---|---|
| P1 | 封面 | cover | hero | peak | 左对齐大标题 + 右侧装饰竖条 | 题目 + 英文副标 + 汇报信息 |
| P2 | 研究框架 | content | supporting | valley | 五段式逻辑链 | 用一条横向流程串起"背景→空白→问题→方法→验证" |
| P3 | 从"能回答"到"能决策" | content | supporting | valley | 左右 6:4 | 左侧三段演进时间线，右侧关键判断条 |
| P4 | 现有基准的共同错位 | content | supporting | valley | 三栏卡片 + 底部结论条 | 三类基准 → 三个局限 → 一句空白 |
| P5 | 三个可验证的研究问题 | content | hero | peak | 三行纵排 + 左编号 | Q1/Q2/Q3 各含自变量→因变量 |
| P6 | 技术路线 | content | supporting | valley | 阶段流程链 | 五阶段 + 下方输出条 |
| P7 | 环境设计：浙北三站点 | content | supporting | valley | 左表 + 右要点 | 站点/年型表 + 天气数据说明 |
| P8 | 关键设计：信息不完全 | content | hero | peak | 左右对照 | 粗粒度观测 vs 付费精确调查 |
| P9 | 四维评分体系 | content | supporting | valley | 表格 + 右侧权重条 | 效益45/产量20/合规15/过程20 |
| P10 | 四基线校准结果 | content | hero | peak | 图表主图 + 结论条 | 横向条形图，总分排序 |
| P11 | 三个验证发现 | content | supporting | valley | 三栏 + 数字锚点 | 排序合理 / 惩罚有效 / 天花板位置 |
| P12 | 创新点与预期成果 | content | supporting | valley | 上下两段 | 4 条创新 + 3 项成果 |
| P13 | 进度安排 | content | supporting | valley | 五阶段甘特式 | 8 周排期 |
| P14 | 参考文献 | content | supporting | valley | 单列文献表 | GB/T 7714，10 条 |
| P15 | 结束页 | ending | hero | peak | 居中大字 | 请指正 |

---

## 三、逐页字段

### P1 封面
- role: hero / rhythm: peak / visual_role: atmosphere
- density: 字数约 40 / 图片 0 / 留白约 45%
- anti_pattern: 禁止放数据指标；禁止超过 4 层信息；禁止居中对称排布
- description: 主标题「AgriAgent-Bench：面向种植决策的大模型智能体长程规划与纠偏能力评测基准」；英文副标「A Benchmark for Long-horizon Planning and Recovery of LLM Agents in Crop Management」；说明行「农业工程课程 · 开题答辩」；信息层「汇报人 / 指导教师：曾松伟、吴达胜 / 浙江农林大学 / 2026.11」

### P2 研究框架
- role: supporting / rhythm: valley / visual_role: evidence
- density: 字数约 120 / 留白约 20%
- anti_pattern: 禁止五等分等宽卡片；禁止加装饰图标
- description: 五个环节横向串联——① 农业生产依赖经验，决策难复制 → ② 农业大模型已能答题，但不会连续决策 → ③ 现有基准只测感知与问答 → ④ 构建农场模拟环境测长程决策 → ⑤ 四基线校准，区分度验证通过。最后一句结论：本研究把评测对象从"答案"换成"决策轨迹"。

### P3 研究背景
- role: supporting / rhythm: valley / visual_role: evidence
- density: 字数约 260 / 留白约 15%
- anti_pattern: 禁止大段政策引述；禁止把三个阶段做成等大卡片
- description: 左侧时间线三段：2024—2025 农业垂直大模型集中发布（问豆/蟹小智/慧种稻/工耕）；2026 从"对话助手"向"自主操作"过渡；瓶颈被明确指出为长程规划与鲁棒性。右侧一条深蓝判断条：「模型能说清一株稻缺什么，但决定不了一整季的氮肥怎么分配」。底部小字注明依据来源。

### P4 文献综述与空白
- role: supporting / rhythm: valley / visual_role: evidence
- density: 字数约 300 / 留白约 12%
- anti_pattern: 禁止把三类基准写成平铺罗列；禁止只列名字不给局限
- description: 三栏：Ⅰ 能力分层类（AgriBench，五级评测，止于"给建议"，不测执行）；Ⅱ 知识问答类（AI-AgriBench，416 题专家审核，前沿模型 95%+ 已饱和，RAG 无增益）；Ⅲ 遥感制图类（SwissCrop25，评分类精度，不评管理决策）。底部结论条：三者共性——输入静态、答案唯一、评分比对，而农业决策动态、多解、看长期后果。

### P5 研究问题
- role: hero / rhythm: peak / visual_role: evidence
- density: 字数约 220 / 留白约 20%
- anti_pattern: 禁止三条等宽横卡；禁止只写问题不写变量
- description: Q1 能力衰减（步数 1→10→120 → 综合得分）；Q2 纠偏能力（扰动类型 → 恢复步数、产量损失率）；Q3 信息成本（观测成本 0/8/40 元 → 观测频次与净收益）。右侧统一标注"三个问题均可实证、均可量化"。

### P6 技术路线
- role: supporting / rhythm: valley / visual_role: evidence
- density: 字数约 200 / 留白约 15%
- anti_pattern: 禁止五个阶段等宽等大；禁止用箭头图标堆砌
- description: 五阶段横向：文献调研 → 环境建模 → 基线校准 → 任务集编写 → 多模型评测；下方输出条列出每阶段产出物；最下方虚线回路表示"评分体系随结果迭代"。

### P7 环境设计
- role: supporting / rhythm: valley / visual_role: evidence
- density: 字数约 240 / 图表 1 表 / 留白约 15%
- anti_pattern: 禁止把表格做成满色块；禁止只讲地点不讲数据来源
- description: 左表列三站点（湖州南浔 30.87N/120.09E、嘉兴桐乡 30.63N/120.56E、杭州余杭 30.42N/120.30E）× 三年型季降水（2022 666mm 干旱 / 2023 1087mm 常态 / 2024 1033mm 偏多）；右侧要点：ERA5-Land 再分析、184 天逐日、含 ET₀ 与辐射、共 9 组驱动数据。

### P8 关键设计：信息不完全
- role: hero / rhythm: peak / visual_role: anchor
- density: 字数约 230 / 留白约 20%
- anti_pattern: 禁止画成普通流程图；禁止省略成本数字
- description: 左侧"模型默认看到"：墒情三档、叶色三档、病虫三档、未来 3 天预报（带误差）；右侧"付费才能拿到"：精确含水量、速效氮、病虫指数，代价 8 元/次 + 信息滞后。中间一条强调：真实农业里，信息是要花钱买的——这条设计把"瞎猜"和"会决策"区分开。

### P9 评分体系
- role: supporting / rhythm: valley / visual_role: evidence
- density: 字数约 250 / 表格 1 / 留白约 12%
- anti_pattern: 禁止把权重画成饼图；禁止只给分值不给设计意图
- description: 表格四行：效益 45（净收益/550 元，防"不计成本堆产量"）、产量 20（防"为省钱不种地"）、合规 15（15−4×违规）、过程 20（5 项农时各 4 分）。右侧竖条示意权重比例。

### P10 四基线校准结果
- role: hero / rhythm: peak / visual_role: anchor
- density: 字数约 180 / 图表 1 / 留白约 15%
- anti_pattern: 禁止用饼图；禁止把四个策略做成等宽卡片
- description: 横向条形图，四条策略综合得分（全知上界 87.1 / 农技规则 82.4 / 只收不管 50.6 / 随机乱动 47.0），右侧一句结论：排序符合农学常识，且"高产量低收益"的随机策略被判为垫底。

### P11 三个验证发现
- role: supporting / rhythm: valley / visual_role: evidence
- density: 字数约 260 / 留白约 15%
- anti_pattern: 禁止三条等宽卡片；禁止只有结论没有数字
- description: ① 排序合理（全知 87.1 > 专家 82.4 > 不作为 50.6 > 乱作为 47.0）；② 惩罚有效（随机策略产量 520.8 接近专家 554.5，但成本 2370 元/亩导致净亏 964 元，综合垫底）；③ 天花板位置合理（专家与全知仅差 4.7 分，瓶颈在决策时机不在信息获取）。

### P12 创新点与预期成果
- role: supporting / rhythm: valley / visual_role: evidence
- density: 字数约 240 / 留白约 18%
- anti_pattern: 禁止"三大创新"式对称罗列标题
- description: 上段四条创新（评测范式从问答到闭环、信息成本建模、区域化气象驱动、四级基线坐标）；下段三项成果（开源工具包、多模型评测报告、课程论文）。

### P13 进度安排
- role: supporting / rhythm: valley / visual_role: evidence
- density: 字数约 180 / 留白约 20%
- anti_pattern: 禁止用甘特图占满整页却不标里程碑
- description: 8 周五阶段：第 1-2 周环境与基线、第 3-4 周任务集、第 5-6 周多模型评测、第 7 周失效分析、第 8 周论文与答辩。每阶段标注交付物。

### P14 参考文献
- role: supporting / rhythm: valley / visual_role: evidence
- density: 字数约 320 / 留白约 10%
- anti_pattern: 禁止编造文献；禁止缩小字号至不可读
- description: 10 条 GB/T 7714 格式文献，方括号序号，17px 可读字号。

### P15 结束页
- role: hero / rhythm: peak / visual_role: atmosphere
- density: 字数约 20 / 留白约 55%
- anti_pattern: 禁止写"谢谢聆听"套话堆砌；禁止加数据
- description: 一行"请各位老师批评指正"，下方小字汇报人与日期。
