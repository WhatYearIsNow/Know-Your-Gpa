#!/usr/bin/env python3
"""
Radar GPA Extractor  雷达图加权成绩推测工具
=============================================
从微北洋(WePeiYang)等应用的雷达图截图/照片中，
通过交互式点击提取各科成绩，计算加权平均分与GPA。

数学原理：
  Flutter 源码中 _count(x) = x^4 / 10^8
  inner_radius = outer_radius * 2/3
  data_distance = inner_radius * _count(score)
  逆推得: score = (data_distance / inner_radius)^(1/4) * 100

用法：
  python radar_gpa.py <图片路径>
  或直接将图片拖拽到脚本上
"""

import argparse
import math
from collections.abc import Iterable

import numpy as np


GRADE_SCALE = (
    (90, 4.0, "A"),
    (85, 3.7, "A-"),
    (82, 3.3, "B+"),
    (78, 3.0, "B"),
    (75, 2.7, "B-"),
    (72, 2.3, "C+"),
    (68, 2.0, "C"),
    (64, 1.5, "C-"),
    (60, 1.0, "D"),
    (0, 0.0, "F"),
)


def score_to_gpa(score: float) -> float:
    """百分制  4.0 GPA"""
    return next(
        (gpa for minimum, gpa, _ in GRADE_SCALE if score >= minimum),
        0.0,
    )


def gpa_to_label(gpa: float) -> str:
    """GPA  等级标签"""
    return next(
        (label for _, value, label in GRADE_SCALE if value == gpa),
        "?",
    )


def calculate_weighted_averages(
    score_credits: Iterable[tuple[float, float]],
) -> tuple[float, float, float]:
    """返回按学分加权的平均分、平均 GPA 和总学分。"""
    records = list(score_credits)
    if not records:
        raise ValueError("至少需要一门课程")
    if any(
        not math.isfinite(score)
        or not 0 <= score <= 100
        or not math.isfinite(credit)
        or credit <= 0
        for score, credit in records
    ):
        raise ValueError("成绩必须在 0 到 100 之间，学分必须大于 0")

    total_credit = sum(credit for _, credit in records)
    weighted_score = sum(score * credit for score, credit in records)
    weighted_gpa = sum(
        score_to_gpa(score) * credit for score, credit in records
    )
    return (
        weighted_score / total_credit,
        weighted_gpa / total_credit,
        total_credit,
    )


# ---- 核心数学 ----------------------------------------------------------
def calculate_score(center: np.ndarray, outer: np.ndarray,
                    data: np.ndarray) -> float:
    """
    根据中心点、轴外端点、数据点，反推百分制成绩。

    参数均为画布坐标下的 (x, y) 数组，尺度因子会在比值中抵消。
    额外做了一次沿轴方向的投影，提高容错。
    """
    axis_vec = outer - center
    outer_dist = float(np.linalg.norm(axis_vec))
    if outer_dist < 1e-6:
        return 0.0

    # 将数据点投影到轴方向上
    data_vec = data - center
    proj_dist = float(np.dot(data_vec, axis_vec)) / outer_dist

    # inner = outer * 2/3
    inner_radius = outer_dist * 2.0 / 3.0
    if inner_radius < 1e-6:
        return 0.0

    ratio = proj_dist / inner_radius
    if ratio <= 0:
        return 0.0

    # 逆推 _count: score = ratio^(1/4) * 100
    score = (ratio ** 0.25) * 100.0
    return max(0.0, min(100.0, score))


# ---- 主流程 ------------------------------------------------------------
def main():
    import matplotlib

    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser(
        description="从雷达图照片推测加权成绩")
    parser.add_argument("image", help="雷达图图片路径")
    args = parser.parse_args()

    img = plt.imread(args.image)
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.imshow(img)
    ax.set_title("Radar GPA Extractor", fontsize=14, fontweight="bold")

    #  打印操作说明 
    print()
    print("=" * 62)
    print("    雷达图 GPA 推测工具")
    print("=" * 62)
    print()
    print("  流程：")
    print("    1. 在图中点击雷达图的「中心点」")
    print("    2. 输入课程数量 N")
    print("    3. 按顺序点击每条轴的「外端点」（课程名附近）")
    print("    4. 按顺序点击每条轴上的「数据点」（多边形顶点）")
    print("    5. 为每门课输入课程名和学分")
    print()
    print("  提示：")
    print("    - 区分不清时可放大窗口仔细观察")
    print("    - 点击时尽量对准轴心方向，程序会自动做投影修正")
    print("    - 随时可按 Ctrl+C 终止")
    print()

    #  第一步：中心点 
    ax.set_title("Step 1/5  请点击雷达图「中心点」",
                 fontsize=13, color="#e53e3e", fontweight="bold")
    plt.draw()
    center = np.array(plt.ginput(1, timeout=0)[0])
    ax.plot(center[0], center[1], "r+", markersize=22, markeredgewidth=3,
            zorder=10)
    ax.annotate("Center", center + np.array([12, -12]),
                color="red", fontsize=9, fontweight="bold")
    print(f"    中心点: ({center[0]:.0f}, {center[1]:.0f})")
    plt.draw()

    #  第二步：课程数量 
    print()
    while True:
        s = input("  请输入课程数量（轴的数量）: ").strip()
        try:
            n = int(s)
            if n >= 3:
                break
            print("    雷达图至少需要 3 条轴（3 门课），请重新输入。")
        except ValueError:
            print("    请输入一个整数。")

    #  第三步：外端点 
    ax.set_title(f"Step 2/5  请依次点击 {n} 条轴的「外端点」（绿色 +）",
                 fontsize=13, color="#38a169", fontweight="bold")
    plt.draw()
    outer_raw = plt.ginput(n, timeout=0)
    outers = [np.array(p) for p in outer_raw]
    for i, o in enumerate(outers):
        ax.plot(o[0], o[1], "g+", markersize=16, markeredgewidth=2,
                zorder=10)
        ax.plot([center[0], o[0]], [center[1], o[1]],
                "gray", alpha=0.25, linewidth=0.8)
        ax.annotate(str(i + 1), o + np.array([8, -8]),
                    color="green", fontsize=9, fontweight="bold")
    plt.draw()
    print(f"    已标记 {n} 个外端点")

    #  第四步：数据点 
    data_pts = []
    for i in range(n):
        ax.set_title(
            f"Step 3/5  请点击第 {i + 1}/{n} 条轴上的「数据点」（蓝色 ）",
            fontsize=13, color="#3182ce", fontweight="bold")
        plt.draw()
        dp = np.array(plt.ginput(1, timeout=0)[0])
        data_pts.append(dp)
        ax.plot(dp[0], dp[1], "bo", markersize=10, zorder=10)
        plt.draw()

    # 用数据点连线绘制多边形（帮助确认）
    poly_x = [d[0] for d in data_pts] + [data_pts[0][0]]
    poly_y = [d[1] for d in data_pts] + [data_pts[0][1]]
    ax.plot(poly_x, poly_y, "b-", alpha=0.35, linewidth=2, zorder=5)
    plt.draw()
    print(f"    已标记 {n} 个数据点")

    #  第五步：课程信息 
    print()
    print("  现在请输入每门课的「名称」和「学分」：")
    print("  " + "-" * 48)
    courses = []
    for i in range(n):
        ax.set_title(
            f"Step 4/5  请在终端中输入第 {i + 1}/{n} 门课的信息",
            fontsize=13, color="#805ad5", fontweight="bold")
        plt.draw()

        name = input(f"    课程 {i + 1} 名称: ").strip()
        if not name:
            name = f"Course-{i + 1}"

        while True:
            cr_str = input(f"    「{name}」的学分: ").strip()
            try:
                credit = float(cr_str)
                if credit > 0:
                    break
                print("      学分必须大于 0。")
            except ValueError:
                print("      请输入数字。")

        courses.append((name, credit))

    #  计算 & 输出结果 
    ax.set_title("计算结果已输出到终端，关闭图片窗口即可退出。",
                 fontsize=13, color="#718096")
    plt.draw()

    print()
    print("=" * 62)
    print("    推测结果")
    print("=" * 62)
    print(f"  {'课程名称':<22s} {'成绩':>7s}  {'学分':>6s}  {'GPA':>5s}  {'等级':>4s}")
    print("  " + "-" * 52)

    score_credits = []

    for i, ((name, credit), outer, data) in enumerate(
            zip(courses, outers, data_pts)):
        score = calculate_score(center, outer, data)
        gpa = score_to_gpa(score)
        label = gpa_to_label(gpa)

        score_credits.append((score, credit))

        print(f"  {name:<22s} {score:>7.2f}  {credit:>6.1f}  "
              f"{gpa:>5.2f}  {label:>4s}")

    if score_credits:
        weighted_avg, overall_gpa, total_credit = calculate_weighted_averages(
            score_credits
        )
        total_weighted = weighted_avg * total_credit
        overall_label = gpa_to_label(overall_gpa)
        print("  " + "-" * 52)
        print(f"  {'加权平均':<22s} {weighted_avg:>7.2f}  "
              f"{total_credit:>6.1f}  {overall_gpa:>5.2f}  {overall_label:>4s}")
        print(f"  {'加权总分':<22s} {total_weighted:>7.2f}")

    print("=" * 62)
    print()
    print("  关闭图片窗口即可退出。")
    print()

    plt.show(block=True)


if __name__ == "__main__":
    main()
