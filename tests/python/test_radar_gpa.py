import math

import numpy as np
import pytest

from radar_auto_detect import (
    angular_distance,
    annotated_output_path,
    match_vertices,
    parse_ground_truth,
    score_from_dist,
)
from radar_gpa import (
    calculate_score,
    calculate_weighted_averages,
    gpa_to_label,
    score_to_gpa,
)


@pytest.mark.parametrize(
    ("score", "expected_gpa", "expected_label"),
    [
        (100, 4.0, "A"),
        (90, 4.0, "A"),
        (89.99, 3.7, "A-"),
        (82, 3.3, "B+"),
        (60, 1.0, "D"),
        (59.99, 0.0, "F"),
        (0, 0.0, "F"),
        (-1, 0.0, "F"),
    ],
)
def test_score_to_gpa_boundaries(score, expected_gpa, expected_label):
    gpa = score_to_gpa(score)
    assert gpa == expected_gpa
    assert gpa_to_label(gpa) == expected_label


def test_calculate_score_projects_to_axis_and_clamps():
    center = np.array([0.0, 0.0])
    outer = np.array([15.0, 0.0])
    data = np.array([10 * 0.8**4, 5.0])

    assert calculate_score(center, outer, data) == pytest.approx(80.0)
    assert calculate_score(center, outer, np.array([-1.0, 0.0])) == 0.0
    assert calculate_score(center, outer, np.array([20.0, 0.0])) == 100.0


def test_weighted_gpa_uses_each_course_gpa():
    weighted_score, weighted_gpa, total_credit = calculate_weighted_averages(
        [(90, 1), (60, 3)]
    )

    assert weighted_score == pytest.approx(67.5)
    assert weighted_gpa == pytest.approx(1.75)
    assert total_credit == 4
    assert weighted_gpa != score_to_gpa(weighted_score)


@pytest.mark.parametrize(
    "records",
    [[], [(80, 0)], [(80, -1)], [(-1, 1)], [(101, 1)], [(math.nan, 1)]],
)
def test_weighted_averages_reject_invalid_credits(records):
    with pytest.raises(ValueError):
        calculate_weighted_averages(records)


def test_annotated_output_never_reuses_input_path():
    assert annotated_output_path("chart.JPG").name == "chart_detected.jpg"
    assert annotated_output_path("chart").name == "chart_detected.png"


def test_angular_distance_wraps_at_pi():
    assert angular_distance(math.pi - 0.02, -math.pi + 0.02) == pytest.approx(
        0.04
    )


def test_match_vertices_prefers_farther_point_at_same_angle():
    center = np.array([0.0, 0.0])
    vertices = np.array([[5.0, 0.0], [9.0, 0.0]])

    assert match_vertices(center, vertices, [0.0]) == [9.0]
    assert score_from_dist(9.0, 10.0) == pytest.approx(100 * 0.9**0.25)


def test_parse_ground_truth_skips_pass_fail_rows(tmp_path):
    detail = tmp_path / "detail.txt"
    detail.write_text(
        "semester\tid\t有效课程\tcategory\trequired\t2\t80\t3.0\n"
        "semester\tid\t零分课程\tcategory\trequired\t1\t0\t0\n"
        "semester\tid\t通过课程\tcategory\trequired\t1\tP\t0\n",
        encoding="utf-8",
    )

    courses = parse_ground_truth(detail)

    assert [course["name"] for course in courses] == ["有效课程", "零分课程"]
