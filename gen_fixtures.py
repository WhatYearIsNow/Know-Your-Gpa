# -*- coding: utf-8 -*-
"""生成合成 GPA 雷达图测试夹具(替代真实成绩截图)。

生成的图是标准微北洋 GPA 雷达图样式:
- 深色背景, 白色雷达多边形轮廓(课程轴)
- 内圆(外半径的 2/3)与外圆(轴端点)
- N 条从中心辐射的轴
- 成绩点(白色小圆)沿轴分布
- 顶部学分卡显示总学分

参数可控, 测试断言按此处参数编写。
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

OUT_DIR = r"D:\Documents\AI-System\.github-audit\Know-Your-Gpa\tests\fixtures"


def draw_radar(
    filename,
    n_axes,
    center,
    outer_radius,
    inner_radius,
    scores,       # 每轴成绩点距中心的比例 (0~1), None=无点
    credits,      # 每轴学分
    credit_ring,  # 学分环位置(距中心比例)
    total_credits_display,
    img_size=(812, 1800),
    bg=(8, 17, 31),
    line=(255, 255, 255),
    axis=(42, 59, 85),
    score_color=(255, 255, 255),
    credit_color=(46, 126, 223),
):
    """绘制一张 GPA 雷达图。"""
    w, h = img_size
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    cx, cy = center

    angles = [2 * math.pi * i / n_axes - math.pi / 2 for i in range(n_axes)]

    # 内圆 + 外圆
    d.ellipse([cx - inner_radius, cy - inner_radius, cx + inner_radius, cy + inner_radius],
              outline=(58, 74, 100), width=2)
    d.ellipse([cx - outer_radius, cy - outer_radius, cx + outer_radius, cy + outer_radius],
              outline=(58, 74, 100), width=2)

    # 轴(从中心到外圆)
    for a in angles:
        x1, y1 = cx, cy
        x2 = cx + math.cos(a) * outer_radius
        y2 = cy + math.sin(a) * outer_radius
        d.line([x1, y1, x2, y2], fill=axis, width=2)

    # 雷达轮廓(白色多边形, 连接各轴的成绩点位置)
    poly = []
    for i, a in enumerate(angles):
        r = outer_radius * scores[i] if scores and i < len(scores) else outer_radius
        poly.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    d.polygon(poly, outline=line, width=3)

    # 成绩点
    if scores:
        for i, a in enumerate(angles):
            r = outer_radius * scores[i]
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=score_color)

    # 学分环(虚线圆, 位置 credit_ring)
    cr = outer_radius * credit_ring
    d.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], outline=credit_color, width=3)

    # 底部学分卡(白色圆角矩形 + 数字, 位于雷达下方, 避开顶部扫描区)
    card_w, card_h = 300, 130
    card_x, card_y = cx - card_w // 2, cy + outer_radius + 60
    d.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                        radius=18, fill=(255, 255, 255))
    text = str(total_credits_display)
    try:
        from PIL import ImageFont
        f = ImageFont.load_default()
        d.text((cx - 30, card_y + 40), text, fill=(0, 0, 0), font=f)
    except Exception:
        d.text((cx - 20, card_y + 45), text, fill=(0, 0, 0))

    img.save(os.path.join(OUT_DIR, filename))
    print(f"generated: {filename} ({n_axes} axes, credits={credits})")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # 16 轴示例: 标准 16 门课场景(合成成绩/学分)
    # scores 成绩: 大部分高分(0.7~1.0), 个别低 —— 顶点特征明显, 便于轴数检测
    scores16 = [0.96, 0.82, 0.93, 0.99, 0.88, 0.95, 0.76, 0.91,
                0.98, 0.85, 0.94, 0.80, 0.97, 0.87, 0.92, 0.95]
    credits16 = [4, 3, 1, 4, 2, 2, 1, 1, 3, 1, 2, 5, 3, 2, 1, 1]
    draw_radar("synthetic-16axes.jpg", 16, (396, 700), 420, 280, scores16, credits16, 0.62, 36.0)

    # 10 轴示例: 少课程场景(合成成绩/学分)
    scores10 = [0.95, 0.80, 0.90, 0.99, 0.85, 0.93, 0.75, 0.96, 0.91, 0.97]
    credits10 = [4, 3, 1, 4, 2, 3, 1, 2, 1, 2]
    draw_radar("synthetic-10axes.jpg", 10, (396, 700), 420, 280, scores10, credits10, 0.60, 23.0)

    print("done")


if __name__ == "__main__":
    main()
