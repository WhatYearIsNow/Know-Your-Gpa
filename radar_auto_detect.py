#!/usr/bin/env python3
"""Radar Chart Auto Detector - 自动检测雷达图成绩。"""

import argparse
import math
from pathlib import Path

import cv2
import numpy as np


def parse_ground_truth(txt_path: str | Path) -> list[dict[str, float | str]]:
    courses = []
    with Path(txt_path).open("r", encoding="utf-8") as file:
        for raw_line in file:
            parts = raw_line.strip().split("\t")
            if len(parts) < 8:
                continue
            try:
                credit = float(parts[5])
                score = float(parts[-2].strip())
            except ValueError:
                continue
            if credit <= 0 or score < 0:
                continue
            try:
                gpa = float(parts[-1].strip())
            except ValueError:
                gpa = 0.0
            courses.append(
                {
                    "name": parts[2],
                    "credit": credit,
                    "score": score,
                    "gpa": gpa,
                }
            )
    return courses


def read_image(image_path: str | Path) -> np.ndarray | None:
    path = Path(image_path)
    image_bytes = np.frombuffer(path.read_bytes(), dtype=np.uint8)
    return cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)


def annotated_output_path(image_path: str | Path) -> Path:
    path = Path(image_path)
    suffix = path.suffix.lower()
    supported = {".bmp", ".jpg", ".jpeg", ".png", ".webp"}
    output_suffix = suffix if suffix in supported else ".png"
    return path.with_name(f"{path.stem}_detected{output_suffix}")


def write_image(image_path: str | Path, image: np.ndarray) -> None:
    path = Path(image_path)
    success, encoded = cv2.imencode(path.suffix, image)
    if not success:
        raise ValueError(f"无法编码输出图片：{path}")
    path.write_bytes(encoded.tobytes())


def angular_distance(first: float, second: float) -> float:
    return abs((first - second + math.pi) % (2 * math.pi) - math.pi)


def detect_center_and_axes(
    image: np.ndarray,
) -> tuple[np.ndarray, float, list[float]]:
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=30,
        param1=80,
        param2=35,
        minRadius=20,
        maxRadius=min(width, height) // 2,
    )
    if circles is None:
        region = gray[: height * 2 // 3, :]
        circles = cv2.HoughCircles(
            region,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=30,
            param1=80,
            param2=30,
            minRadius=15,
            maxRadius=min(width, height) // 3,
        )

    if circles is None:
        center_x, center_y = width // 2, height // 3
        circle_radius = min(width, height) // 8
    else:
        best = max(circles[0], key=lambda circle: circle[2])
        center_x, center_y, circle_radius = map(
            int,
            np.around(best),
        )

    center = np.array([float(center_x), float(center_y)])
    inner_radius = circle_radius * 2.0 / 3.0
    edges = cv2.Canny(gray, 60, 180)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=40,
        minLineLength=inner_radius * 0.5,
        maxLineGap=8,
    )

    axis_angles = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            first_distance = math.hypot(x1 - center_x, y1 - center_y)
            second_distance = math.hypot(x2 - center_x, y2 - center_y)
            if (
                first_distance > inner_radius * 0.1
                and second_distance > inner_radius * 0.1
            ):
                continue
            endpoint = (x1, y1) if first_distance > second_distance else (x2, y2)
            axis_angles.append(
                math.atan2(endpoint[1] - center_y, endpoint[0] - center_x)
            )

    clustered_angles = []
    for angle in sorted(axis_angles):
        if all(
            angular_distance(angle, existing) > 0.15
            for existing in clustered_angles
        ):
            clustered_angles.append(angle)
    return center, inner_radius, clustered_angles


def detect_blue_polygon(image: np.ndarray) -> np.ndarray | None:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv,
        np.array([95, 60, 60]),
        np.array([145, 255, 255]),
    )
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    mask = cv2.erode(mask, kernel, iterations=1)
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    if not contours:
        return None
    main_contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(main_contour, True)
    polygon = cv2.approxPolyDP(main_contour, 0.015 * perimeter, True)
    return polygon.reshape(-1, 2).astype(np.float64)


def match_vertices(
    center: np.ndarray,
    vertices: np.ndarray,
    axis_angles: list[float],
) -> list[float]:
    distances = []
    used = set()
    for target_angle in axis_angles:
        best = None
        for index, vertex in enumerate(vertices):
            if index in used:
                continue
            delta_x, delta_y = vertex - center
            vertex_angle = math.atan2(delta_y, delta_x)
            difference = angular_distance(vertex_angle, target_angle)
            if difference >= 0.35:
                continue
            distance = math.hypot(delta_x, delta_y)
            candidate = (difference, -distance, index, distance)
            if best is None or candidate < best:
                best = candidate
        if best is None:
            distances.append(0.0)
            continue
        used.add(best[2])
        distances.append(best[3])
    return distances


def score_from_dist(distance: float, inner_radius: float) -> float:
    if inner_radius < 1e-6 or distance < 1e-6:
        return 0.0
    score = (distance / inner_radius) ** 0.25 * 100.0
    return max(0.0, min(100.0, score))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="雷达图截图路径")
    parser.add_argument("ground_truth", type=Path, help="成绩明细文本路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ground_truth = parse_ground_truth(args.ground_truth)
    if not ground_truth:
        raise ValueError("成绩明细中没有可计算的课程")

    print(f"GT courses: {len(ground_truth)}")
    for course in ground_truth:
        print(
            f'  {course["name"]:<24s}  score={course["score"]:5.1f}  '
            f'credit={course["credit"]:5.1f}  gpa={course["gpa"]:.1f}'
        )
    total_credit = sum(float(course["credit"]) for course in ground_truth)
    expected_weighted = sum(
        float(course["score"]) * float(course["credit"])
        for course in ground_truth
    ) / total_credit
    print(f"  Expected weighted avg: {expected_weighted:.2f}")

    image = read_image(args.image)
    if image is None:
        raise ValueError(f"无法读取图片：{args.image}")
    height, width = image.shape[:2]
    print(f"Image: {width}x{height}")

    center, inner_radius, angles = detect_center_and_axes(image)
    print(
        f"Center: ({center[0]:.1f}, {center[1]:.1f}), "
        f"inner_r={inner_radius:.1f}, axes={len(angles)}"
    )
    if len(angles) < 3:
        print("检测到的放射轴不足 3 条，停止生成标注图。")
        return 2
    vertices = detect_blue_polygon(image)
    if vertices is None:
        print("没有找到蓝色成绩多边形，停止生成标注图。")
        return 2
    print(f"Blue vertices: {len(vertices)}")

    distances = match_vertices(center, vertices, angles)
    scores = [score_from_dist(distance, inner_radius) for distance in distances]
    print()
    print("=" * 60)
    print(f'  {"#":>3s}  {"Detected":>8s}  {"GT":>8s}  {"Error":>8s}')
    print("  " + "-" * 40)
    errors = []
    for index, (detected, expected) in enumerate(
        zip(scores, (float(course["score"]) for course in ground_truth)),
        start=1,
    ):
        error = detected - expected
        errors.append(error)
        print(f"  {index:>3d}  {detected:>8.2f}  {expected:>8.2f}  {error:>+8.2f}")
    if errors:
        mean_absolute_error = sum(abs(error) for error in errors) / len(errors)
        root_mean_square_error = math.sqrt(
            sum(error**2 for error in errors) / len(errors)
        )
        print("  " + "-" * 40)
        print(
            f"  MAE: {mean_absolute_error:.2f}  "
            f"RMSE: {root_mean_square_error:.2f}"
        )

    if len(scores) >= len(ground_truth):
        detected_weighted = sum(
            scores[index] * float(course["credit"])
            for index, course in enumerate(ground_truth)
        ) / total_credit
        print(
            f"  Detected weighted: {detected_weighted:.2f} "
            f"(expected: {expected_weighted:.2f})"
        )
        print(f"  Weighted error: {detected_weighted - expected_weighted:+.2f}")
    print("=" * 60)

    annotated = image.copy()
    center_point = tuple(center.astype(int))
    cv2.circle(annotated, center_point, 5, (0, 0, 255), -1)
    cv2.circle(annotated, center_point, int(inner_radius), (0, 255, 0), 2)
    for vertex in vertices:
        cv2.circle(annotated, tuple(vertex.astype(int)), 4, (255, 0, 0), -1)
    for angle in angles:
        endpoint = (
            int(center[0] + inner_radius * 1.5 * math.cos(angle)),
            int(center[1] + inner_radius * 1.5 * math.sin(angle)),
        )
        cv2.line(annotated, center_point, endpoint, (0, 255, 255), 1)

    output_path = annotated_output_path(args.image)
    write_image(output_path, annotated)
    print(f"Saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
