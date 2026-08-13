import argparse

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from tkinter import simpledialog

from radar_gpa import (
    calculate_score,
    calculate_weighted_averages,
    gpa_to_label,
    score_to_gpa,
)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    args = parser.parse_args()
    img = plt.imread(args.image)
    fig, ax = plt.subplots(figsize=(13,9))
    ax.imshow(img)
    ax.set_title("radar GPA", fontsize=14)

    ax.set_title("1 - ", fontsize=13, color="red")
    plt.draw()
    center = np.array(plt.ginput(1, timeout=0)[0])
    ax.plot(center[0], center[1], "r+", markersize=22, markeredgewidth=3, zorder=10)
    ax.annotate("", center + np.array([12,-12]), color="red", fontsize=9)
    plt.draw()

    root = tk.Tk()
    root.withdraw()
    n = simpledialog.askinteger("课程数量", "请输入课程数量：", minvalue=3)
    if n is None:
        root.destroy()
        plt.close(fig)
        return

    ax.set_title("2 - {} ".format(n), fontsize=13, color="green")
    plt.draw()
    outer_raw = plt.ginput(n, timeout=0)
    outers = [np.array(p) for p in outer_raw]
    for i, o in enumerate(outers):
        ax.plot(o[0], o[1], "g+", markersize=16, markeredgewidth=2, zorder=10)
        ax.plot([center[0], o[0]], [center[1], o[1]], "gray", alpha=0.25, linewidth=0.8)
        ax.annotate(str(i+1), o + np.array([8,-8]), color="green", fontsize=9)
    plt.draw()

    data_pts = []
    for i in range(n):
        ax.set_title("3 - {}/{} ".format(i+1, n), fontsize=13, color="blue")
        plt.draw()
        dp = np.array(plt.ginput(1, timeout=0)[0])
        data_pts.append(dp)
        ax.plot(dp[0], dp[1], "bo", markersize=10, zorder=10)
        plt.draw()

    poly_x = [d[0] for d in data_pts] + [data_pts[0][0]]
    poly_y = [d[1] for d in data_pts] + [data_pts[0][1]]
    ax.plot(poly_x, poly_y, "b-", alpha=0.35, linewidth=2, zorder=5)
    plt.draw()

    courses = []
    for i in range(n):
        ax.set_title("4 - {}/{} ".format(i+1, n), fontsize=13, color="purple")
        plt.draw()
        name = simpledialog.askstring("课程名称", "课程 {} 名称：".format(i+1))
        if not name or not name.strip():
            name = "课程 {}".format(i+1)
        while True:
            credit = simpledialog.askfloat(
                "课程学分",
                "{} 的学分：".format(name),
                minvalue=0.1,
            )
            if credit is None:
                root.destroy()
                plt.close(fig)
                return
            if credit > 0:
                break
        courses.append((name, credit))

    ax.set_title(" - ", fontsize=13, color="gray")
    plt.draw()

    print()
    print("="*60)
    print("  ")
    print("="*60)
    print("  {:<22s} {:>7s}  {:>6s}  {:>5s}  {:>4s}".format("","","","GPA",""))
    print("  "+"-"*52)

    score_credits = []
    for i, ((name, credit), outer, data) in enumerate(zip(courses, outers, data_pts)):
        score = calculate_score(center, outer, data)
        gpa = score_to_gpa(score)
        label = gpa_to_label(gpa)
        score_credits.append((score, credit))
        print("  {:<22s} {:>7.2f}  {:>6.1f}  {:>5.2f}  {:>4s}".format(name, score, credit, gpa, label))

    if score_credits:
        wa, og, total_credit = calculate_weighted_averages(score_credits)
        ol = gpa_to_label(og)
        print("  "+"-"*52)
        print("  {:<22s} {:>7.2f}  {:>6.1f}  {:>5.2f}  {:>4s}".format("", wa, total_credit, og, ol))

    print("="*60)
    print(" ")
    root.destroy()
    plt.show(block=True)

if __name__ == "__main__":
    main()
