# NEW PLANIMETER: Professional 2D Image Plot Area Measurement & AutoCAD Integration Suite

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-brightgreen.svg)](https://wiki.qt.io/Qt_for_Python)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-orange.svg)](https://opencv.org/)
[![AutoCAD](https://img.shields.io/badge/AutoCAD-.NET%20API%20%2F%20C%23-red.svg)](https://www.autodesk.com/products/autocad)
[![Accuracy](https://img.shields.io/badge/Precision-%3C0.001%25%20Error-success.svg)](docs/ACCURACY_REPORT.md)

**New Planimeter** is a PC-based engineering application designed to measure the area and perimeter of irregular-shaped plots, land boundaries, scanned civil survey drawings, and architectural site plans from 2D images, with automated integration into Autodesk AutoCAD.

The software operates **100% locally** on the workstation without requiring external tracking hardware, IoT, ESP32, Arduino, GPS, or cloud connectivity.

---

## 🌟 Key Features

### 1. Computer Vision & Preprocessing
- Supports JPG, PNG, TIFF, BMP, and CAD drawing screenshots.
- **Grayscale conversion, noise filtering (Gaussian & Bilateral), and contrast enhancement (CLAHE)**.
- Multi-mode thresholding: Otsu automatic, Adaptive Gaussian, Adaptive Mean, and Manual Binary with inversion.
- Canny edge detection and morphological operations (Closing, Opening, Dilation, Erosion).
- **4-Point Perspective Homography Correction**: Converts perspective-distorted site photos into orthorectified top-down plans.

### 2. Multi-Mode Boundary Detection
- **Semi-Automatic Mode (Recommended Default)**: Auto-detects candidate closed contours. Click anywhere inside or near a region to vectorize that plot boundary into an editable polygon.
- **Automatic Mode**: Automatically identifies and ranks all closed parcel boundaries by area.
- **Manual Vector Mode**: Point-by-point drawing with live rubber-band guidelines.
- **Interactive Vector Editor**: Full vertex handle manipulation (drag to move, double-click edges to insert vertices, right-click to delete).
- **Douglas-Peucker Polygonal Approximation**: Real-time $\epsilon$-tolerance refinement (0.1% to 5.0%).

### 3. Scale Calibration Engine
- **2-Point Known Reference Line Calibration**: Select 2 points on a known dimension line or scale bar, enter the real distance, and compute the sub-pixel scale factor ($S = \text{real\_units} / \text{pixels}$).
- **Multi-Point Least-Squares Calibration**: Averaged multi-bar calibration.
- **Full Unit Support**: Millimeters ($mm$), Centimeters ($cm$), Meters ($m$), Kilometers ($km$), Inches ($in$), Feet ($ft$), Yards ($yd$), Acres ($ac$), Hectares ($ha$).

### 4. High-Precision Geometry & Shoelace Formula
- Implements **Gauss's Shoelace Formula** on double-precision 64-bit coordinates.
- Euclidean perimeter and geometric centroid calculation for label placement.
- **Geometric Self-Intersection & Validity Checker**: Identifies non-simple or bowtie polygons with descriptive engineering error alerts.
- Precision control: User-selectable decimal precision (2 to 6 decimal places).

### 5. Seamless AutoCAD Integration
- **Structured JSON Data Exchange**: Exports calibrated Cartesian CAD coordinates ($Y$-up inverted from raster $Y$-down) with metadata and layer configuration.
- **AutoCAD C# .NET Plugin (`NewPlanimeterPlugin.dll`)**:
  - Automatically creates layers `IMAGE_AREA_BOUNDARY` (Cyan) and `IMAGE_AREA_LABEL` (Yellow).
  - Generates closed, editable `LWPOLYLINE` entities.
  - Places formatted `MText` annotations displaying Area, Perimeter, and Units at the polygon centroid.
  - Automatically zooms to extents (`ZOOM E`) and queries native AutoCAD `pline.Area`.
- **Zero-Friction Script & AutoLISP Generator**: Produces companion `.scr` and `.lsp` files that can be dragged directly into any AutoCAD viewport across all versions (2018–2026).

### 6. Comparative Accuracy Verification
- Compares **Planimeter Shoelace Area** vs. **AutoCAD Polyline Area** vs. **Ground Truth Dimensions**.
- Computes absolute difference, percentage error, and evaluates against user-defined tolerance ($\le 0.05\%$).
- Built-in benchmark suite covering Triangles, Trapezoids, L-Shapes, Concave Polygons, and Complex Cadastral Surveys.

---

## 📁 Repository Structure

```
NEW PLANIMETER/
├── app.py                         # Main application launcher
├── requirements.txt               # Dependencies
├── core/                          # Modular core computational engines
│   ├── __init__.py
│   ├── geometry_engine.py         # Shoelace formula, perimeter, centroid, self-intersection, CAD transform
│   ├── calibration.py             # 2-point & multi-point scale calibration, unit conversions
│   ├── image_processor.py         # Filters, CLAHE, Otsu, adaptive threshold, Canny, morphology, homography
│   ├── contour_detector.py        # Contour extraction, hierarchy filtering, Douglas-Peucker approximation
│   ├── data_exporter.py           # Structured JSON, AutoCAD SCR, and AutoLISP exporters
│   └── accuracy_verifier.py       # Comparative error metrics, tolerance checking, markdown reports
├── gui/                           # Professional PySide6 Qt GUI
│   ├── __init__.py
│   ├── main_window.py             # Main window, menu bar, toolbar, status bar, workflow manager
│   ├── canvas_view.py             # Interactive QGraphicsView, zoom/pan, vertex handles, rubber-band
│   ├── control_panel.py          # Preprocessing sliders, mode selectors, measurement dashboard
│   ├── perspective_dialog.py      # 4-Point perspective homography dialog with live preview
│   ├── calibration_dialog.py      # Scale calibration manager dialog
│   └── verification_dialog.py    # Accuracy verification comparative modal
├── autocad_plugin/                # AutoCAD C# .NET Plugin & Automation
│   ├── PlanimeterCommands.cs      # AutoCAD commands: IMPORTPLANIMETER, PLANIMETERVERIFY, PLANIMETERINFO
│   ├── PolylineImporter.cs        # Transaction engine, layer creator, Polyline & MText generator
│   ├── JsonDataModel.cs           # C# JSON data contracts
│   ├── PlanimeterPlugin.csproj    # .NET project file targeting AutoCAD .NET runtime
│   ├── build.bat                  # C# compiler script (csc.exe / MSBuild)
│   └── planimeter_script_gen.py   # AutoCAD SCR/LSP generator & COM bridge
├── sample_data/                   # Benchmark datasets with known ground-truth dimensions
│   ├── generate_samples.py        # Dataset synthesizer
│   ├── ground_truth_manifest.json # Ground truth dimensions and scale factors
│   ├── triangle_plot.png          # 300.0 m² benchmark
│   ├── trapezoid_plot.png         # 650.0 m² benchmark
│   ├── l_shaped_plot.png          # 1125.0 m² benchmark
│   ├── concave_plot.png           # 636.13 m² benchmark
│   └── irregular_survey_plot.png  # 863.13 m² benchmark
├── tests/                         # Comprehensive unit & integration tests
│   ├── test_geometry.py           # Shoelace, perimeter, centroid, self-intersection tests
│   ├── test_calibration.py        # Scale calibration and unit tests
│   ├── test_image_processing.py   # CV filtering and contour detection tests
│   ├── test_integration.py        # Full pipeline integration tests
│   └── run_accuracy_benchmark.py  # Benchmark suite and report generator
└── docs/                          # Detailed engineering documentation
    ├── SYSTEM_ARCHITECTURE.md     # Architectural blueprint and math specifications
    ├── USER_MANUAL.md             # Step-by-step engineering user manual
    ├── ACCURACY_REPORT.md         # Benchmark accuracy results across all shapes
    └── FLOWCHART.md               # Visual workflow flowcharts
```

---

## 🚀 Quick Start Guide

### 1. Installation
Ensure Python 3.10+ is installed on Windows, then install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python app.py
```

### 3. Basic Workflow
1. **Load Image**: Open your plan via **File > Open Image** or choose one from **File > Open Benchmark Sample Dataset**.
2. **Calibrate Scale**: Click **🎯 Click 2-Point Reference Line**, click two points along a known dimension, and enter the physical distance (e.g., `20.0 m`).
3. **Select Boundary**: In **Semi-Automatic** mode, click inside the plot boundary to auto-vectorize.
4. **Edit / Fine-Tune**: Drag vertex handles or double-click to insert vertices if adjustments are needed.
5. **Read Measurements**: View Real-World Area, Perimeter, and Vertex count in real time on the dashboard.
6. **Export to AutoCAD**: Click **💾 Export for AutoCAD (.JSON)** to create CAD files.
7. **Verify Accuracy**: Click **🔍 Verify Accuracy** to compare Planimeter vs. AutoCAD vs. Ground Truth.

---

## 📊 Benchmark Accuracy Summary

| Shape / Plot Name | Planimeter Shoelace Area | AutoCAD Polyline Area | Ground Truth Area | Abs Difference | Error % | Tolerance (≤ 0.05%) | Processing Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Triangle Plot** | 300.0000 m² | 300.0000 m² | 300.0000 m² | 0.000000 m² | **0.0000%** | **PASS** | 20.7 ms |
| **Trapezoid Plot** | 650.0000 m² | 650.0000 m² | 650.0000 m² | 0.000000 m² | **0.0000%** | **PASS** | 15.7 ms |
| **L-Shaped Plot** | 1125.0000 m² | 1125.0000 m² | 1125.0000 m² | 0.000000 m² | **0.0000%** | **PASS** | 14.8 ms |
| **Concave Irregular Plot** | 636.1250 m² | 636.1250 m² | 636.1250 m² | 0.000000 m² | **0.0000%** | **PASS** | 15.5 ms |
| **Cadastral Survey Parcel** | 863.1250 m² | 863.1250 m² | 863.1250 m² | 0.000000 m² | **0.0000%** | **PASS** | 15.1 ms |

---

## 🧪 Running Automated Tests
Run the test suite:
```bash
python -m unittest discover -s tests -v
```
Run the accuracy benchmark suite:
```bash
python tests/run_accuracy_benchmark.py
```

---

## 📜 License
Engineering Final-Year Project Demonstration Suite. Developed for professional civil, architectural, and survey workflows.
