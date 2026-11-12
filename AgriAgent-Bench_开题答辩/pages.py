"""15 页开题答辩幻灯片内容定义。坐标基于 1280x720。"""

import os
import sys
from pptx_engine import Slide, build

C_MAIN = "1E4FA8"     # 学术宝蓝
C_SUB = "3D7BD9"      # 中蓝
C_PALE = "E8EFF8"     # 浅蓝底
C_RED = "D9534F"      # 警示红
C_TXT = "1A2230"      # 正文
C_TXT2 = "4A5568"     # 次级
C_TXT3 = "8B97A8"     # 弱化
C_LINE = "D6DCE5"     # 分隔线
C_WHITE = "FFFFFF"


def page_header(s, num, title, section):
    """内容页统一母版：顶条 + 标题 + 页脚"""
    s.rect(0, 0, 1280, 64, fill=C_MAIN)
    s.rect(60, 20, 6, 24, fill=C_WHITE)
    s.text(80, 16, 760, 36, title, size=28, bold=True, color=C_WHITE, anchor="c")
    s.text(980, 18, 240, 30, section, size=14, color="B9CDEE", align="r", anchor="c")
    s.text(60, 676, 700, 20, "AgriAgent-Bench　·　农业工程课程开题答辩", size=13, color=C_TXT3)
    s.text(1120, 676, 100, 20, f"{num:02d} / 15", size=13, color=C_TXT3, align="r")


def conclusion_bar(s, y, text, h=44):
    """底部结论条"""
    s.rect(60, y, 1160, h, fill=C_PALE)
    s.rect(60, y, 4, h, fill=C_MAIN)
    s.text(84, y, 1120, h, text, size=17, color=C_TXT, anchor="c")


# ---------------------------------------------------------------- P1 封面

def p01():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    s.rect(100, 74, 22, 22, fill=C_MAIN)
    s.text(136, 72, 420, 26, "农业工程 · 课程开题答辩", size=15, color=C_TXT2)

    s.rect(100, 206, 6, 172, fill=C_MAIN)
    s.text(130, 198, 1000, 62, "AgriAgent-Bench", size=50, bold=True, color=C_TXT, lnspc=1.15)
    s.text(130, 268, 1000, 56, "面向种植决策的大模型智能体", size=40, bold=True, color=C_MAIN, lnspc=1.25)
    s.text(130, 328, 1000, 56, "长程规划与纠偏能力评测基准", size=40, bold=True, color=C_MAIN, lnspc=1.25)

    s.text(130, 408, 1000, 30, "A Benchmark for Long-horizon Planning and Recovery of Agricultural LLM Agents",
           size=17, color=C_TXT3)

    s.rect(100, 566, 1080, 1, fill=C_LINE)
    s.text(100, 590, 900, 28, "汇报人：徐毅成　　指导教师：曾松伟　吴达胜", size=16, color=C_TXT2)
    s.text(100, 624, 900, 26, "浙江农林大学　·　2026 年 11 月", size=15, color=C_TXT3)

    s.rect(0, 710, 1280, 10, fill=C_MAIN)
    return s


# ---------------------------------------------------------------- P2 研究框架

def p02():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 2, "研究框架", "00 · 总览")
    s.text(60, 88, 900, 26, "从生产痛点出发，落到一个可量化、可复现的评测装置", size=15, color=C_TXT2)

    steps = [
        ("01", "问题起点", "农事决策依赖经验，\n难复制、难规模化"),
        ("02", "技术现状", "大模型能答题，\n但不能连续决策"),
        ("03", "评测缺口", "现有基准只测感知，\n不测决策轨迹"),
        ("04", "本研究", "建农场模拟环境，\n测长程规划"),
        ("05", "初步验证", "五条基线校准，\n区分度成立"),
    ]
    x0, gap, w = 100, 16, 208
    for i, (num, head, body) in enumerate(steps):
        x = x0 + i * (w + gap)
        s.rect(x, 158, w, 212, fill=C_WHITE, line=C_LINE, lw=1)
        s.rect(x, 158, w, 5, fill=C_MAIN if i < 4 else C_RED)
        s.text(x + 20, 176, 60, 30, num, size=22, bold=True, color=C_MAIN)
        s.text(x + 20, 214, w - 40, 30, head, size=19, bold=True, color=C_TXT)
        s.text(x + 20, 252, w - 40, 110, body, size=15, color=C_TXT2, lnspc=1.65)
        if i < 4:
            s.rect(x + w + 2, 258, 12, 2, fill=C_TXT3)

    conclusion_bar(s, 402, "本研究把评测对象从「答案」换成「决策轨迹」：不再问模型知不知道，而问它做得好不好。", 46)

    s.text(60, 478, 1160, 80,
           "评测三要素沿用通用智能体基准的范式——环境定义状态与动作，任务定义目标，评分器定义什么叫「做得好」。",
           size=16, color=C_TXT2, lnspc=1.6)

    s.rect(60, 586, 1160, 1, fill=C_LINE)
    s.text(60, 602, 1160, 30,
           "评测对象：决策轨迹　｜　评测粒度：单步 / 整季 / 扰动　｜　驱动数据：浙北实况 + 当时起报的 EC 预报",
           size=14, color=C_TXT3)
    return s


# ---------------------------------------------------------------- P3 研究背景

def p03():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 3, "从「能回答」到「能决策」", "01 · 研究背景")

    s.text(60, 96, 700, 30, "农业 AI 的三段演进", size=18, bold=True, color=C_MAIN)

    stages = [
        ("2024—2025", "农业垂直大模型集中发布",
         "问豆（大豆）、蟹小智（河蟹）、慧种稻、慧耕耘、工耕（机器人）相继落地，形态以「解答」为主。"),
        ("2026", "从对话助手转向自主操作",
         "开始对接传感器与农机：牧原的养猪模型可主动捕捉异常并生成工单，工耕尝试打通感知—决策—执行。"),
        ("当前瓶颈", "长程规划与鲁棒性不足",
         "综述明确指出，农业生成式 AI 多数仍停在第一阶段（对话助手），少数进入第二阶段（被动执行）。"),
    ]
    y = 140
    for i, (tag, head, body) in enumerate(stages):
        s.rect(60, y, 640, 118, fill=C_WHITE, line=C_LINE, lw=1)
        s.rect(60, y, 4, 118, fill=C_MAIN if i < 2 else C_RED)
        s.text(80, y + 12, 140, 24, tag, size=14, bold=True, color=C_MAIN if i < 2 else C_RED)
        s.text(80, y + 36, 600, 26, head, size=19, bold=True, color=C_TXT)
        s.text(80, y + 66, 590, 44, body, size=14, color=C_TXT2, lnspc=1.45)
        y += 134

    s.rect(740, 140, 480, 372, fill=C_MAIN)
    s.text(772, 168, 420, 24, "核心矛盾", size=14, color="B9CDEE")
    s.text(772, 200, 420, 200,
           "模型能说清一株稻缺什么，但决定不了一整季的氮肥怎么分配。",
           size=27, bold=True, color=C_WHITE, lnspc=1.45)
    s.text(772, 410, 420, 80,
           "单点知识已经够用，缺的是把几十个决策串成一个生长季的能力。",
           size=15, color="C9D9F0", lnspc=1.5)

    conclusion_bar(s, 548, "评测标准必须跟着变：从「答对没有」转向「管理得好不好」。", 44)
    s.text(60, 616, 1160, 40,
           "依据：2026 年农业生成式 AI 综述对发展阶段的划分；南京农业大学、中国农业大学等公开成果；国家发改委农作物种植方向 AI 中试基地建设规划。",
           size=12, color=C_TXT3, lnspc=1.4)
    return s


# ---------------------------------------------------------------- P4 文献综述

def p04():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 4, "现有基准的共同错位", "02 · 文献综述")

    cols = [
        ("Ⅰ", "能力分层类", "AgriBench（CVPPA@ECCV 2024）",
         "五级能力分层，从基础识别到「人机对齐建议」；配套 MM-LUCAS 1784 幅景观图像。",
         "止于给出建议，不考察建议被执行后的后果。"),
        ("Ⅱ", "知识问答类", "AI-AgriBench（2026）",
         "416 组专家审核农学问答，设置训练截止后子集以规避数据污染。",
         "前沿模型准确率普遍超过 95%，基准已饱和，叠加 RAG 无显著增益。"),
        ("Ⅲ", "遥感制图类", "SwissCrop25（2026）",
         "七个生长季、73 类作物，采用留一年验证协议。",
         "评的是分类精度，不是管理决策的好坏。"),
    ]
    x = 60
    for num, head, src, desc, limit in cols:
        s.rect(x, 100, 373, 372, fill=C_WHITE, line=C_LINE, lw=1)
        s.text(x + 24, 118, 60, 46, num, size=30, bold=True, color=C_MAIN)
        s.text(x + 24, 168, 325, 28, head, size=20, bold=True, color=C_TXT)
        s.text(x + 24, 202, 325, 26, src, size=13, color=C_TXT3)
        s.rect(x + 24, 236, 325, 1, fill=C_LINE)
        s.text(x + 24, 250, 325, 100, desc, size=15, color=C_TXT2, lnspc=1.5)
        s.text(x + 24, 356, 325, 100, [("局限  ", {"color": C_RED, "bold": True, "size": 13}),
                                       (limit, {"color": C_TXT, "size": 15})], lnspc=1.5)
        x += 393

    conclusion_bar(s, 500, "三类基准的共性：输入静态、答案唯一、评分靠比对——而农业决策恰好动态、多解、看长期后果。", 46)

    s.text(60, 574, 1160, 80,
           "共同空白：没有基准考察模型在数十至上百步决策中的能力衰减，也没有基准把「获取信息的成本」纳入考量。",
           size=16, color=C_TXT, lnspc=1.6)
    return s


# ---------------------------------------------------------------- P5 研究问题

def p05():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 5, "三个可验证的研究问题", "03 · 研究问题")

    qs = [
        ("Q1", "能力衰减", "决策链条拉长后，决策质量如何变化？",
         "步数 1 → 20 → 184", "综合决策得分"),
        ("Q2", "纠偏能力", "遭遇外部扰动后，能否识别并恢复？",
         "扰动类型（暴雨 / 病虫 / 药害）", "恢复步数、产量损失率"),
        ("Q3", "信息成本", "获取信息的代价如何影响策略？",
         "观测单价 0 / 8 / 40 元　·　预报 3 / 5 / 7 天", "观测频次、净收益"),
    ]
    y = 100
    for code, name, question, iv, dv in qs:
        s.rect(60, y, 1160, 144, fill=C_WHITE, line=C_LINE, lw=1)
        s.rect(60, y, 96, 144, fill=C_MAIN)
        s.text(60, y + 44, 96, 40, code, size=30, bold=True, color=C_WHITE, align="c")
        s.text(180, y + 16, 480, 28, name, size=20, bold=True, color=C_TXT)
        s.text(180, y + 50, 520, 30, question, size=16, color=C_TXT2)
        s.text(180, y + 96, 540, 40, [("自变量  ", {"color": C_TXT3, "size": 12}),
                                       (iv, {"color": C_TXT, "size": 14})], lnspc=1.4)

        s.rect(740, y + 86, 1, 42, fill=C_LINE)
        s.text(764, y + 96, 420, 40, [("因变量  ", {"color": C_TXT3, "size": 12}),
                                       (dv, {"color": C_MAIN, "size": 14, "bold": True})], lnspc=1.4)
        y += 168

    conclusion_bar(s, 612, "三个问题都有明确的自变量与因变量，均可通过环境实验给出量化答案。", 44)
    return s


# ---------------------------------------------------------------- P6 技术路线

def p06():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 6, "技术路线", "04 · 研究设计")

    phases = [
        ("第 1 阶段", "环境建模", "状态变量、动作空间、\n观测模型"),
        ("第 2 阶段", "基线校准", "五条基线，\n确认上下界"),
        ("第 3 阶段", "任务集编写", "L1 单步 / L2 整季 /\nL3 扰动"),
        ("第 4 阶段", "多模型评测", "6—8 个模型，\n统一协议"),
        ("第 5 阶段", "失效分析", "错误归类，\n迭代评分"),
    ]
    x0, gap, w = 60, 11, 223
    for i, (tag, head, body) in enumerate(phases):
        x = x0 + i * (w + gap)
        s.rect(x, 110, w, 150, fill=C_WHITE, line=C_LINE, lw=1)
        s.text(x + 18, 124, w - 36, 22, tag, size=12, color=C_TXT3)
        s.text(x + 18, 148, w - 36, 28, head, size=19, bold=True, color=C_MAIN)
        s.text(x + 18, 184, w - 36, 62, body, size=14, color=C_TXT2, lnspc=1.45)
        if i < 4:
            s.rect(x + w + 2, 180, 7, 2, fill=C_TXT3)

    s.text(60, 286, 400, 24, "阶段交付物", size=15, bold=True, color=C_MAIN)
    s.rect(60, 316, 1160, 70, fill=C_PALE)
    outs = ["env.py\n评分器", "基线结果\nJSON", "任务集\n30+ 条", "榜单\n与画像", "失效模式\n报告"]
    for i, o in enumerate(outs):
        x = 60 + i * 232
        s.text(x + 4, 322, 220, 58, o, size=14, color=C_TXT, align="c", anchor="c", lnspc=1.4)

    s.text(60, 416, 400, 24, "关键方法选择", size=15, bold=True, color=C_MAIN)
    methods = [
        ("天气用实况 + 当时起报的 EC 预报", "预报误差是当年真实的，不是人为加噪"),
        ("状态转移用农学规则简化", "追求决策逻辑合理，不追求产量数值精确"),
        ("评分结果与过程并重", "只看结果会奖励蛮干，只看过程会奖励表演"),
        ("裁判跨厂商交叉", "规避模型自评偏好"),
    ]
    y = 448
    for name, why in methods:
        s.rect(60, y, 1160, 44, fill=C_WHITE, line=C_LINE, lw=1)
        s.text(80, y, 400, 44, name, size=15, bold=True, color=C_TXT, anchor="c")
        s.rect(492, y + 10, 1, 24, fill=C_LINE)
        s.text(512, y, 690, 44, why, size=14, color=C_TXT2, anchor="c")
        y += 50

    s.text(60, 656, 1160, 24, "虚线回路：评分体系随失效分析结果迭代，不是一次性设定。", size=12, color=C_TXT3)
    return s


# ---------------------------------------------------------------- P7 环境设计

def p07():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 7, "环境设计：浙北三站点 × 三个生长季", "04 · 研究设计")

    s.text(60, 96, 600, 26, "三个代表性点位（杭嘉湖平原水稻主产区）", size=15, bold=True, color=C_MAIN)

    rows = [
        ("湖州南浔", "30.87°N / 120.09°E", "杭嘉湖平原东部"),
        ("嘉兴桐乡", "30.63°N / 120.56°E", "浙北平原中部"),
        ("杭州余杭", "30.42°N / 120.30°E", "杭州北部"),
    ]
    s.rect(60, 132, 620, 40, fill=C_PALE)
    s.text(76, 132, 160, 40, "点位", size=14, bold=True, color=C_MAIN, anchor="c")
    s.text(240, 132, 220, 40, "经纬度", size=14, bold=True, color=C_MAIN, anchor="c")
    s.text(464, 132, 200, 40, "区域", size=14, bold=True, color=C_MAIN, anchor="c")
    y = 176
    for name, coord, region in rows:
        s.text(76, y, 160, 42, name, size=15, color=C_TXT, anchor="c")
        s.text(240, y, 220, 42, coord, size=14, color=C_TXT2, anchor="c")
        s.text(464, y, 200, 42, region, size=14, color=C_TXT2, anchor="c")
        s.rect(60, y + 42, 620, 1, fill=C_LINE)
        y += 43

    s.text(60, 320, 600, 26, "三个生长季（5—10 月季降水，三站点均值）", size=15, bold=True, color=C_MAIN)
    years = [("2024", "1196 mm", "梅雨偏涝", C_MAIN), ("2025", "1127 mm", "平水", C_SUB), ("2026", "1196 mm", "偏涝", C_SUB)]
    x = 60
    for yr, rain, tag, color in years:
        s.rect(x, 356, 196, 96, fill=C_WHITE, line=C_LINE, lw=1)
        s.text(x + 16, 366, 80, 22, yr, size=13, color=C_TXT3)
        s.text(x + 16, 388, 160, 30, rain, size=22, bold=True, color=color)
        s.text(x + 16, 422, 160, 22, tag, size=13, color=C_TXT2)
        x += 212

    s.rect(720, 96, 500, 356, fill=C_WHITE, line=C_LINE, lw=1)
    s.rect(720, 96, 500, 4, fill=C_MAIN)
    s.text(744, 118, 452, 26, "数据与参数", size=16, bold=True, color=C_TXT)
    items = [
        "实况：ERA5 再分析，经 Open-Meteo 分发",
        "预报：当时起报的 ECMWF IFS，滚动 7 天",
        "逐日 184 天（5 月 1 日 — 10 月 31 日）",
        "含气温、降水、湿度、辐射、ET₀",
        "主实验 9 组 + 扩展验证 9 组驱动数据",
    ]
    y = 154
    for it in items:
        s.rect(744, y + 9, 5, 5, fill=C_MAIN)
        s.text(760, y, 434, 28, it, size=13, color=C_TXT2, lnspc=1.4)
        y += 36

    s.text(744, 350, 452, 84,
           "物候按有效积温标定，成熟期落在 10 月中下旬，与浙北单季晚稻实际一致。",
           size=13, color=C_TXT, lnspc=1.55)

    conclusion_bar(s, 476, "实况与预报都取自当年真实数据，使「换个年景还灵不灵」成为可测量的指标。", 44)

    s.text(60, 546, 1160, 100,
           "数据边界（主动说明）：ECMWF 预报存档起于 2024 年 3 月，故主实验为 2024—2026。缺的干旱年改用日本气象厅 JMA 的真实预报补做——其存档 2021 年起可用，据此重建 2021—2023 扩展验证集，季降水分别为 1,539 / 592 / 1,050 mm。",
           size=13, color=C_TXT2, lnspc=1.65)
    return s


# ---------------------------------------------------------------- P8 关键设计

def p08():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 8, "关键设计：信息不是免费的", "04 · 研究设计")

    s.text(60, 96, 560, 26, "默认可见：模糊等级", size=16, bold=True, color=C_TXT2)
    left = [
        ("土壤墒情", "偏干 / 适宜 / 偏湿"),
        ("叶片颜色", "偏淡 / 正常 / 偏浓"),
        ("病虫情况", "未见 / 零星 / 明显"),
        ("未来天气", "7 天预报（当时起报）"),
    ]
    y = 136
    for k, v in left:
        s.rect(60, y, 540, 62, fill=C_WHITE, line=C_LINE, lw=1)
        s.text(80, y, 180, 62, k, size=16, color=C_TXT, anchor="c")
        s.text(268, y, 316, 62, v, size=15, color=C_TXT2, anchor="c")
        y += 70

    s.text(680, 96, 560, 26, "付费获取：精确数据", size=16, bold=True, color=C_MAIN)
    right = [
        ("土壤含水量", "±1.5 mm 测量误差"),
        ("速效氮", "±0.08 kg/亩"),
        ("病虫指数", "0—1 连续值"),
        ("代价", "8 元 / 次，且当天不能再决策"),
    ]
    y = 136
    for k, v in right:
        s.rect(680, y, 540, 62, fill=C_PALE, line="C3D5EE", lw=1)
        s.text(700, y, 180, 62, k, size=16, bold=True, color=C_MAIN, anchor="c")
        s.text(888, y, 316, 62, v, size=15, color=C_TXT, anchor="c")
        y += 70

    s.rect(60, 436, 1160, 100, fill=C_MAIN)
    s.text(88, 452, 1100, 30, "为什么要这样设计", size=14, color="B9CDEE")
    s.text(88, 480, 1100, 46,
           "真实农业里，下田查看要花时间和人工。默认信息免费、状态全知，模型就会靠猜也能拿高分。",
           size=19, bold=True, color=C_WHITE, lnspc=1.4)

    s.text(60, 550, 1160, 40,
           "信息有两种成本：一是「查得到」的单价（8 元/次），二是「看得远」的时效（3 / 5 / 7 天）。",
           size=15, color=C_TXT, lnspc=1.5)
    s.text(60, 596, 1160, 56,
           "预报取自 ECMWF 历史存档——每天 08:00 起报、覆盖未来 7 天，误差是当年真实的预报误差，不是人为噪声。",
           size=14, color=C_TXT2, lnspc=1.6)
    return s


# ---------------------------------------------------------------- P9 评分体系

def p09():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 9, "四维评分：总分 100", "04 · 研究设计")

    rows = [
        ("效益", "45", "净收益 / 480 元·亩⁻¹，上限 45 分", "防「不计成本堆产量」"),
        ("产量", "20", "实际产量 / 640 kg·亩⁻¹，上限 20 分", "防「为省钱不种地」"),
        ("合规", "15", "15 − 4 × 违规次数", "守住生产安全底线"),
        ("过程", "20", "5 项关键农时，每项 4 分", "考察管理动作规范性"),
    ]
    s.rect(60, 100, 800, 40, fill=C_PALE)
    s.text(76, 100, 120, 40, "维度", size=14, bold=True, color=C_MAIN, anchor="c")
    s.text(196, 100, 70, 40, "分值", size=14, bold=True, color=C_MAIN, anchor="c")
    s.text(280, 100, 330, 40, "计算方式", size=14, bold=True, color=C_MAIN, anchor="c")
    s.text(624, 100, 220, 40, "设计意图", size=14, bold=True, color=C_MAIN, anchor="c")

    y = 144
    for name, score, formula, intent in rows:
        s.text(76, y, 120, 56, name, size=17, bold=True, color=C_TXT, anchor="c")
        s.text(196, y, 70, 56, score, size=22, bold=True, color=C_MAIN, anchor="c")
        s.text(280, y, 330, 56, formula, size=13, color=C_TXT2, anchor="c", lnspc=1.35)
        s.text(624, y, 220, 56, intent, size=13, color=C_TXT, anchor="c", lnspc=1.35)
        s.rect(60, y + 56, 800, 1, fill=C_LINE)
        y += 57

    s.text(60, 386, 800, 26, "关键农时五项（各 4 分，窗口按有效积温判定）", size=14, bold=True, color=C_MAIN)
    s.text(60, 414, 800, 62,
           "分蘖肥到位　·　晒田至 45 mm 以下　·　孕穗保水（70% 时间 ≥ 48 mm）　·　病虫峰值 < 0.35　·　成熟后 20 天内收获",
           size=13, color=C_TXT2, lnspc=1.7)

    s.rect(900, 100, 320, 368, fill=C_WHITE, line=C_LINE, lw=1)
    s.text(920, 116, 280, 24, "权重结构", size=14, bold=True, color=C_TXT)
    bars = [("效益", 45, C_MAIN), ("产量", 20, C_SUB), ("合规", 15, "7FA3D4"), ("过程", 20, "B9CDEE")]
    y = 152
    for name, val, color in bars:
        s.text(920, y, 46, 20, name, size=12, color=C_TXT2)
        s.rect(968, y + 3, int(val * 4.4), 14, fill=color)
        s.text(968 + int(val * 4.4) + 8, y, 40, 20, str(val), size=12, bold=True, color=C_TXT2)
        y += 44
    s.text(920, 340, 280, 110,
           "效益占 45 分，是因为农业经营的最终检验是「划不划算」，不是「产量高不高」。",
           size=13, color=C_TXT2, lnspc=1.6)

    conclusion_bar(s, 484, "只看结果会奖励蛮干，只看过程会奖励表演——四维并用，才能挑出真正会种地的模型。", 44)

    s.text(60, 544, 1160, 90,
           "防作弊：所有评分项基于状态轨迹而非动作序列直接匹配；扰动型任务的事件注入不提前告知，模型必须自己发现异常。",
           size=13, color=C_TXT2, lnspc=1.6)
    return s


# ---------------------------------------------------------------- P10 结果

def p10():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 10, "前期验证：五条基线 + 大模型实测", "05 · 初步结果")

    s.text(60, 86, 620, 24, "综合得分（279 次完整生长季运行）", size=14, color=C_TXT3)

    data = [
        ("全知上界", 95.1, C_MAIN, "信息完备的理论天花板"),
        ("规则+预报", 80.1, C_SUB, "同一套农艺，多看一份预报"),
        ("农技规则", 78.8, "7FA3D4", "专家经验的可执行化"),
        ("DeepSeek V4.1", 73.8, "D97706", "9 局实测，未做任何提示工程调优"),
        ("只收不管", 50.8, "A9B6C6", "靠天吃饭的对照"),
        ("随机乱动", 35.7, "C7D0DB", "无策略的下界"),
    ]
    y = 116
    maxw = 620
    for name, val, color, note in data:
        is_llm = name.startswith("DeepSeek")
        s.text(56, y, 140, 26, name, size=13 if is_llm else 15, bold=True,
               color="B45309" if is_llm else C_TXT, anchor="c")
        s.rect(200, y + 2, maxw, 24, fill="F2F5F9")
        s.rect(200, y + 2, int(val / 100 * maxw), 24, fill=color)
        s.text(828, y, 76, 26, f"{val:.1f}", size=18, bold=True,
               color=color if val > 60 else C_TXT2, anchor="c")
        if is_llm:
            s.text(902, y, 46, 26, "实测", size=11, color="D97706", anchor="c")
        s.text(200, y + 26, 600, 18, note, size=11,
               color="B45309" if is_llm else C_TXT3)
        y += 54

    s.rect(960, 110, 260, 330, fill=C_WHITE, line=C_LINE, lw=1)
    s.text(978, 124, 224, 24, "四点验证结论", size=14, bold=True, color=C_MAIN)
    concl = [
        ("排序合理", "五条基线在 9 个站点年上无一例外，稳定分出 5 档"),
        ("惩罚有效", "随机策略产量 579 最高，净亏 1,001 元，得分垫底"),
        ("大模型落位", "73.8 分：高过「只收不管」23 分，低于农技规则 5 分"),
        ("短板在过程", "效益 36.9 反超规则 3.6 分；合规 10.1、过程 12.9 拖后腿"),
    ]
    cy = 156
    for h, b in concl:
        s.text(978, cy, 224, 20, h, size=12, bold=True, color=C_TXT)
        s.text(978, cy + 20, 224, 46, b, size=11, color=C_TXT2, lnspc=1.4)
        cy += 72

    conclusion_bar(s, 458,
                   "大模型实测落在 73.8 分——能干活、有区分度，但离「会种地」还差 5 分。", 44)

    s.text(60, 518, 1160, 24,
           "运行规模：主实验 135 次（2024—2026）＋ 扩展验证 135 次（2021—2023，JMA 预报）＋ 大模型实测 9 次，共 279 次完整生长季。",
           size=13, color=C_TXT2)
    s.text(60, 552, 1160, 26,
           "大模型为 DeepSeek V4.1-Flash，temperature 0.2，单局 159—166 步、约 20 分钟；使用与基线完全相同的观察单、动作空间与评分器。",
           size=13, color=C_TXT3, lnspc=1.5)
    s.text(60, 592, 1160, 44,
           "「规则」与「规则+预报」除灌溉决策外完全相同，两者之差（+1.3 分）即预报信息的边际价值——这条单点差异是为 Q3 专门设计的测量基线。",
           size=13, color=C_TXT3, lnspc=1.5)
    return s


# ---------------------------------------------------------------- P11 讨论

def p11():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 11, "三个验证发现", "05 · 初步结果")

    cards = [
        ("发现一", "排序符合农学常识", "95.1", "分（全知上界）",
         "全知 > 规则+预报 > 规则 > 只收不管 > 随机乱动，主实验 9 个站点年完全一致；扩展验证中仅极端涝年（2021）反转，说明排序有年型边界。"),
        ("发现二", "惩罚机制确实起作用", "−1,001", "元 / 亩",
         "随机策略的产量 579 kg 是全场最高，但投入成本 2,565 元/亩，净收益为负、得分垫底。只看产量会被它骗过。"),
        ("发现三", "信息不是越多越好", "5 天", "预报增益的拐点",
         "可见时效 3 / 5 / 7 天分别带来 +1.0 / +1.5 / +1.3 分。换成技巧更差的 JMA 预报（7 天相关系数 0.37→0.21），增益掉到 ±0.4 分：信息值多少钱，取决于它准不准。"),
    ]
    x = 60
    for tag, head, num, unit, body in cards:
        s.rect(x, 100, 373, 340, fill=C_WHITE, line=C_LINE, lw=1)
        s.rect(x, 100, 373, 4, fill=C_MAIN)
        s.text(x + 24, 118, 200, 22, tag, size=12, color=C_TXT3)
        s.text(x + 24, 144, 325, 28, head, size=19, bold=True, color=C_TXT)
        s.text(x + 24, 188, 320, 56, num, size=36, bold=True, color=C_MAIN)
        s.text(x + 24, 244, 320, 22, unit, size=13, color=C_TXT3)
        s.rect(x + 24, 280, 325, 1, fill=C_LINE)
        s.text(x + 24, 294, 325, 130, body, size=14, color=C_TXT2, lnspc=1.6)
        x += 393

    s.rect(60, 466, 1160, 96, fill=C_PALE)
    s.rect(60, 466, 4, 96, fill=C_MAIN)
    s.text(88, 480, 1100, 24, "对研究设计的启发", size=13, bold=True, color=C_MAIN)
    s.text(88, 506, 1100, 46,
           "既然多给信息换不来多少分数，任务集的重心就该放在「什么时候查、查几次」，而不是「再增加几路传感器」。",
           size=16, color=C_TXT, lnspc=1.5)

    s.text(60, 586, 1160, 70,
           "这也解释了一个现实现象：农业数据平台堆了几十项指标，收益却没见涨——真正稀缺的不是数据，而是把数据换成动作的判断力。",
           size=14, color=C_TXT2, lnspc=1.6)
    return s


# ---------------------------------------------------------------- P12 创新与成果

def p12():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 12, "创新点与预期成果", "06 · 研究价值")

    s.text(60, 96, 500, 26, "四点创新", size=16, bold=True, color=C_MAIN)
    inn = [
        ("评测范式", "把农业 AI 评测从静态问答推进到动态闭环决策，评测对象由答案变为轨迹。"),
        ("无泄漏预报驱动", "不用人为噪声模拟预报，直接取当年当时起报的 ECMWF 场，误差真实存在。"),
        ("信息成本双重建模", "既建模「查一次多少钱」，也建模「能看多远」，把查得起与看得远分开测。"),
        ("五级基线坐标系", "随机下界到全知上界五个参照，其中两条只差一个判断点，可直接量化信息价值。"),
    ]
    y = 132
    for i, (h, b) in enumerate(inn, 1):
        s.rect(60, y, 560, 76, fill=C_WHITE, line=C_LINE, lw=1)
        s.text(76, y, 34, 76, str(i), size=18, bold=True, color=C_MAIN, anchor="c")
        s.text(120, y + 12, 490, 24, h, size=16, bold=True, color=C_TXT)
        s.text(120, y + 38, 486, 34, b, size=13, color=C_TXT2, lnspc=1.4)
        y += 86

    s.text(680, 96, 500, 26, "预期成果", size=16, bold=True, color=C_MAIN)
    outs = [
        ("开源工具包", "环境、任务集、评分器三件套，Python 实现，可通过配置文件接入新模型"),
        ("评测报告", "6—8 个主流模型的能力画像、失效模式分类与典型失败案例库"),
        ("课程论文", "一篇完整的研究报告，含环境设计、基线验证与结果分析"),
    ]
    y = 132
    for h, b in outs:
        s.rect(680, y, 540, 110, fill=C_PALE)
        s.text(700, y + 16, 500, 26, h, size=17, bold=True, color=C_MAIN)
        s.text(700, y + 48, 500, 52, b, size=13, color=C_TXT2, lnspc=1.5)
        y += 118

    conclusion_bar(s, 560, "一句话概括：把「模型会不会种地」变成一张可以打分的卷子。", 46)
    return s


# ---------------------------------------------------------------- P13 进度

def p13():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 13, "进度安排", "06 · 研究价值")

    s.text(60, 96, 700, 24, "8 周计划（已完成部分以实色标注）", size=14, color=C_TXT3)

    phases = [
        ("第 1—2 周", "环境建模与基线校准", "已完成", 0, 2),
        ("第 3—4 周", "任务集编写与评分定稿", "进行中", 2, 4),
        ("第 5—6 周", "多模型批量评测", "计划中", 4, 6),
        ("第 7 周", "失效模式分析", "计划中", 6, 7),
        ("第 8 周", "论文撰写与答辩", "计划中", 7, 8),
    ]
    cell_w = (1080 - 160) / 8
    for i, wk in enumerate(range(1, 9)):
        s.text(220 + i * cell_w, 136, cell_w, 22, f"W{wk}", size=12, color=C_TXT3, align="c")

    y = 168
    for name, task, status, a, b in phases:
        s.text(60, y, 150, 56, name, size=13, bold=True, color=C_TXT, anchor="c")
        s.rect(220, y + 16, cell_w * 8, 24, fill="F2F5F9")
        color = C_MAIN if status == "已完成" else (C_SUB if status == "进行中" else "B9CDEE")
        s.rect(220 + a * cell_w + 2, y + 16, cell_w * (b - a) - 4, 24, fill=color)
        s.text(220 + a * cell_w + 6, y + 16, cell_w * (b - a) - 10, 24,
               status, size=11, color=C_WHITE if status != "计划中" else C_TXT2,
               align="c", anchor="c")
        y += 66

    s.rect(220, 168, 1, 330, fill=C_LINE)
    for wk in range(9):
        s.rect(220 + wk * cell_w, 168, 1, 330, fill="EEF1F5")

    s.text(60, 502, 1160, 26, "各阶段交付物", size=14, bold=True, color=C_MAIN)
    outs = [
        ("W1—W2", "环境代码 + 五基线 270 次 + 大模型首轮 9 局（均分 73.8）"),
        ("W3—W4", "L1/L2/L3 任务集 30+ 条、评分器定稿"),
        ("W5—W6", "6—8 个模型的完整榜单与轨迹数据"),
        ("W7—W8", "失效模式报告、课程论文、答辩材料"),
    ]
    y = 532
    for tag, txt in outs:
        s.text(60, y, 120, 26, tag, size=13, bold=True, color=C_MAIN)
        s.text(190, y, 1020, 26, txt, size=13, color=C_TXT2)
        y += 30
    return s


# ---------------------------------------------------------------- P14 参考文献

def p14():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    page_header(s, 14, "参考文献", "07 · 文献")

    refs = [
        "周雨桐, Ryo M. AgriBench: A Hierarchical Agriculture Benchmark for Multimodal Large Language Models[C]. CVPPA Workshop @ ECCV, 2024. arXiv:2412.00465.",
        "AI AgriBench: A domain-grounded benchmark for reliable agricultural question answering (v0.5)[EB/OL]. 2026.",
        "Lauber T, Turkoglu M O, Ledain S, et al. SwissCrop25: A National Multi-Year Benchmark for Operational Crop Mapping[J]. arXiv preprint, 2026.",
        "AI for Productivity in the Age of Agentic AI[R]. Preprints, 202608.1248, 2026.",
        "中国农业大学. 「工耕」大模型为农业机器人装上「具身智能」大脑[N]. 科技日报, 2026-07-05.",
        "全国农业技术推广服务中心. 智慧肥水大模型 1.0 版[EB/OL]. 中国农业农村信息网, 2026-08-28.",
        "南京农业大学. 全国首个开放式大豆产业大语言模型「问豆」(SoyAI) 发布[EB/OL]. 中国农业农村信息网, 2026-09-24.",
        "国家农作物种植方向人工智能应用中试基地建设启动[EB/OL]. 中国农业农村信息网, 2026-08-31.",
        "算法「养猪」、数据「种地」，AI 智能体如何重塑现代农业格局[N]. 中国经济网, 2026-06-03.",
        "Martinez-Sanchez L, Hufkens K, Kearsley E, et al. Semantic segmentation dataset of LUCAS rural landscape Street View Images[J]. Data in Brief, 2024, 54: 110394.",
        "Hersbach H, Bell B, Berrisford P, et al. The ERA5 global reanalysis[J]. Quarterly Journal of the Royal Meteorological Society, 2020, 146(730): 1999-2049.",
        "Zippenfenig P. Open-Meteo.com Weather API[EB/OL]. Zenodo, 2023. DOI: 10.5281/ZENODO.7970649.",
        "ECMWF. IFS Documentation CY49r1, Part V: Ensemble and Probabilistic Forecasting[M]. Reading: ECMWF, 2025.",
    ]
    y = 86
    for i, r in enumerate(refs, 1):
        s.text(60, y, 42, 26, f"[{i}]", size=12, bold=True, color=C_MAIN)
        s.text(100, y, 1120, 42, r, size=11, color=C_TXT2, lnspc=1.4)
        y += 44
    return s


# ---------------------------------------------------------------- P15 结束

def p15():
    s = Slide()
    s.rect(0, 0, 1280, 720, fill=C_WHITE)
    s.rect(0, 0, 1280, 10, fill=C_MAIN)
    s.rect(100, 274, 6, 76, fill=C_MAIN)
    s.text(130, 268, 840, 60, "请各位老师批评指正", size=36, bold=True, color=C_TXT, lnspc=1.3)
    s.text(130, 330, 840, 40, "AgriAgent-Bench　·　面向种植决策的大模型智能体长程规划与纠偏能力评测基准",
           size=14, color=C_TXT3)

    # 仓库二维码
    qr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "repo_qr.png")
    if os.path.exists(qr):
        s.rect(972, 228, 196, 196, fill=C_WHITE, line=C_LINE, lw=1)
        s.pic(982, 238, 176, 176, qr, name="repo_qr")
        s.text(952, 434, 236, 22, "扫码查看项目仓库", size=13, color=C_TXT2, align="c")
        s.text(932, 458, 276, 22, "github.com/maemi123/AgriAgent-Bench",
               size=11, color=C_MAIN, align="c")

    s.rect(100, 500, 1080, 1, fill=C_LINE)
    s.text(100, 522, 900, 26, "汇报人：徐毅成　　指导教师：曾松伟　吴达胜", size=14, color=C_TXT2)
    s.text(100, 554, 900, 24, "浙江农林大学　·　2026 年 11 月", size=13, color=C_TXT3)
    s.rect(0, 710, 1280, 10, fill=C_MAIN)
    return s


PAGES = [p01, p02, p03, p04, p05, p06, p07, p08, p09, p10, p11, p12, p13, p14, p15]


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    # 必须始终以「零幻灯片」的空白模板为底，否则 rels / Content_Types 会被追加两遍
    template = os.path.join(base, "AgriAgent-Bench_开题答辩.pptx")
    out = os.path.join(base, "AgriAgent-Bench_开题答辩_终稿.pptx")
    slides = [fn() for fn in PAGES]
    build(template, out, slides)
    print(f"generated {len(slides)} slides -> {out}")
