"""
Sample Data Generator for New Planimeter
Generates clean, professional synthetic and realistic 2D engineering drawing plots
with known ground-truth dimensions and visual scale bars for benchmarking.
"""

import os
import math
import json
import cv2
import numpy as np


def create_plot_image(width=1200, height=800, title="Plot Plan"):
    """
    Create a clean engineering blueprint / paper drawing background.
    """
    img = np.full((height, width, 3), 250, dtype=np.uint8)

    # Subtle grid lines
    grid_color = (235, 235, 235)
    for x in range(0, width, 50):
        cv2.line(img, (x, 0), (x, height), grid_color, 1)
    for y in range(0, height, 50):
        cv2.line(img, (0, y), (width, y), grid_color, 1)

    # Header title box
    cv2.rectangle(img, (20, 20), (width - 20, 70), (220, 220, 220), -1)
    cv2.rectangle(img, (20, 20), (width - 20, 70), (50, 50, 50), 2)
    cv2.putText(img, title.upper(), (40, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2, cv2.LINE_AA)

    # Scale bar in bottom right corner: 200px = 10m => scale_factor = 0.05 m/px (20 px/m)
    sb_x1, sb_y1 = width - 260, height - 50
    sb_x2, sb_y2 = width - 60, height - 50
    cv2.line(img, (sb_x1, sb_y1), (sb_x2, sb_y2), (20, 20, 20), 3)
    cv2.line(img, (sb_x1, sb_y1 - 10), (sb_x1, sb_y1 + 10), (20, 20, 20), 3)
    cv2.line(img, (sb_x2, sb_y2 - 10), (sb_x2, sb_y2 + 10), (20, 20, 20), 3)
    cv2.putText(img, "REFERENCE SCALE BAR: 10.00 m (200 px)", (sb_x1 - 30, sb_y1 - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1, cv2.LINE_AA)

    # Drawing border
    cv2.rectangle(img, (20, 20), (width - 20, height - 20), (50, 50, 50), 2)

    return img


def draw_polygon_with_fill(img, pts_px, fill_color=(210, 230, 245), border_color=(20, 20, 20), thickness=3):
    pts_arr = np.array(pts_px, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(img, [pts_arr], fill_color)
    cv2.polylines(img, [pts_arr], isClosed=True, color=border_color, thickness=thickness, lineType=cv2.LINE_AA)
    for p in pts_px:
        cv2.circle(img, (int(p[0]), int(p[1])), 4, (0, 0, 180), -1)


def compute_polygon_metrics(pts_px, scale_factor):
    pts_real = [(p[0] * scale_factor, p[1] * scale_factor) for p in pts_px]
    x = [p[0] for p in pts_real]
    y = [p[1] for p in pts_real]
    n = len(x)
    area = 0.5 * abs(sum(x[i] * y[(i+1)%n] - x[(i+1)%n] * y[i] for i in range(n)))
    perimeter = sum(math.hypot(x[(i+1)%n] - x[i], y[(i+1)%n] - y[i]) for i in range(n))
    return float(area), float(perimeter)


def generate_all_samples(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    scale_factor = 0.05  # 0.05 meters per pixel (1m = 20px)
    unit = "m"
    ground_truths = {}

    # 1. Triangle: Base = 30m (600px), Height = 20m (400px) => Area = 300.0 m^2
    img1 = create_plot_image(title="Survey Plan #1: Triangular Boundary")
    t_pts = [(300, 600), (900, 600), (300, 200)]
    draw_polygon_with_fill(img1, t_pts)
    p1_path = os.path.join(output_dir, "triangle_plot.png")
    cv2.imwrite(p1_path, img1)
    a1, per1 = compute_polygon_metrics(t_pts, scale_factor)
    ground_truths["triangle_plot.png"] = {
        "name": "Triangle Plot",
        "scale_factor": scale_factor,
        "unit": unit,
        "ref_line_px": [(940, 750), (1140, 750)],
        "ref_line_distance": 10.0,
        "ground_truth_area": round(a1, 4),
        "ground_truth_perimeter": round(per1, 4),
        "pixel_points": t_pts
    }

    # 2. Trapezoid: Base1=40m (800px), Base2=25m (500px), Height=20m (400px) => Area = 650.0 m^2
    img2 = create_plot_image(title="Survey Plan #2: Trapezoidal Plot")
    trap_pts = [(200, 600), (1000, 600), (800, 200), (300, 200)]
    draw_polygon_with_fill(img2, trap_pts)
    p2_path = os.path.join(output_dir, "trapezoid_plot.png")
    cv2.imwrite(p2_path, img2)
    a2, per2 = compute_polygon_metrics(trap_pts, scale_factor)
    ground_truths["trapezoid_plot.png"] = {
        "name": "Trapezoid Plot",
        "scale_factor": scale_factor,
        "unit": unit,
        "ref_line_px": [(940, 750), (1140, 750)],
        "ref_line_distance": 10.0,
        "ground_truth_area": round(a2, 4),
        "ground_truth_perimeter": round(per2, 4),
        "pixel_points": trap_pts
    }

    # 3. L-Shaped Plot: 50m x 30m with 25m x 15m notch => Area = 1125.00 m^2
    img3 = create_plot_image(title="Survey Plan #3: L-Shaped Building Plot")
    l_pts = [
        (100, 650),   # Bottom-left
        (1100, 650),  # Bottom-right
        (1100, 350),  # Mid-right
        (600, 350),   # Inner corner
        (600, 50),    # Top-mid
        (100, 50)     # Top-left
    ]
    draw_polygon_with_fill(img3, l_pts)
    p3_path = os.path.join(output_dir, "l_shaped_plot.png")
    cv2.imwrite(p3_path, img3)
    a3, per3 = compute_polygon_metrics(l_pts, scale_factor)
    ground_truths["l_shaped_plot.png"] = {
        "name": "L-Shaped Plot",
        "scale_factor": scale_factor,
        "unit": unit,
        "ref_line_px": [(940, 750), (1140, 750)],
        "ref_line_distance": 10.0,
        "ground_truth_area": round(a3, 4),
        "ground_truth_perimeter": round(per3, 4),
        "pixel_points": l_pts
    }

    # 4. Concave Multi-Vertex Polygon (8 vertices)
    img4 = create_plot_image(title="Survey Plan #4: Concave Irregular Boundary")
    concave_pts = [
        (200, 600), (500, 650), (850, 580), (950, 350),
        (750, 200), (550, 320), (350, 180), (180, 380)
    ]
    draw_polygon_with_fill(img4, concave_pts)
    p4_path = os.path.join(output_dir, "concave_plot.png")
    cv2.imwrite(p4_path, img4)
    a4, per4 = compute_polygon_metrics(concave_pts, scale_factor)
    ground_truths["concave_plot.png"] = {
        "name": "Concave Plot",
        "scale_factor": scale_factor,
        "unit": unit,
        "ref_line_px": [(940, 750), (1140, 750)],
        "ref_line_distance": 10.0,
        "ground_truth_area": round(a4, 4),
        "ground_truth_perimeter": round(per4, 4),
        "pixel_points": concave_pts
    }

    # 5. Irregular Cadastral Land Survey Boundary (14 vertices)
    img5 = create_plot_image(title="Survey Plan #5: Cadastral Survey Land Parcel")
    survey_pts = [
        (180, 580), (320, 640), (520, 620), (740, 660), (960, 590),
        (1020, 440), (940, 290), (820, 180), (660, 220), (530, 160),
        (380, 210), (260, 170), (140, 310), (160, 460)
    ]
    draw_polygon_with_fill(img5, survey_pts)
    p5_path = os.path.join(output_dir, "irregular_survey_plot.png")
    cv2.imwrite(p5_path, img5)
    a5, per5 = compute_polygon_metrics(survey_pts, scale_factor)
    ground_truths["irregular_survey_plot.png"] = {
        "name": "Cadastral Survey Parcel",
        "scale_factor": scale_factor,
        "unit": unit,
        "ref_line_px": [(940, 750), (1140, 750)],
        "ref_line_distance": 10.0,
        "ground_truth_area": round(a5, 4),
        "ground_truth_perimeter": round(per5, 4),
        "pixel_points": survey_pts
    }

    gt_path = os.path.join(output_dir, "ground_truth_manifest.json")
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truths, f, indent=2)

    print(f"Generated 5 sample benchmark plots in: {output_dir}")
    return ground_truths


if __name__ == "__main__":
    generate_all_samples(os.path.dirname(os.path.abspath(__file__)))
