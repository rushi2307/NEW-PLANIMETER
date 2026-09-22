# New Planimeter - Engineering User Manual & Workflow Guide

## Table of Contents
1. [Introduction & Quick Start](#1-introduction--quick-start)
2. [Image Loading & Navigation](#2-image-loading--navigation)
3. [Perspective Correction (4-Point Homography)](#3-perspective-correction-4-point-homography)
4. [Boundary Vectorization Modes](#4-boundary-vectorization-modes)
   - [Semi-Automatic Mode (Default)](#semi-automatic-mode-recommended)
   - [Automatic Mode](#automatic-detection-mode)
   - [Manual Polygon Draw & Edit Mode](#manual-polygon-draw--edit-mode)
5. [Scale Calibration Engine](#5-scale-calibration-engine)
6. [Geometric Measurements & Validation](#6-geometric-measurements--validation)
7. [AutoCAD Integration & Plugin Usage](#7-autocad-integration--plugin-usage)
8. [Accuracy Verification & Reporting](#8-accuracy-verification--reporting)

---

## 1. Introduction & Quick Start
**New Planimeter** allows engineers, surveyors, and architects to measure irregular land boundaries, civil plots, and CAD drawing screenshots directly from 2D images with millimeter-level precision.

### Launching the Application
Run the following command from the workspace directory:
```bash
python app.py
```

---

## 2. Image Loading & Navigation
1. Click **File > Open Image** (or press `Ctrl+O`) to load any JPG, PNG, BMP, or TIFF file.
2. Alternatively, test with built-in benchmarks under **File > Open Benchmark Sample Dataset**:
   - Triangle Plot ($300.00\text{ m}^2$)
   - Trapezoid Plot ($650.00\text{ m}^2$)
   - L-Shaped Building Plot ($1125.00\text{ m}^2$)
   - Concave 8-Vertex Irregular Plot ($636.13\text{ m}^2$)
   - Cadastral Land Survey Parcel ($863.13\text{ m}^2$)
3. **Canvas Navigation**:
   - **Zoom**: Scroll the mouse wheel at the cursor position.
   - **Pan**: Hold the middle mouse button and drag, or hold `Alt` + Left-click and drag.
   - **Reset View**: Click the **Fit View** toolbar button or right-click canvas and select **Reset Zoom**.

---

## 3. Perspective Correction (4-Point Homography)
If the input drawing is an angled smartphone photo with perspective distortion:
1. Click **Process > 4-Point Perspective Rectification** (or click the toolbar button).
2. Drag the 4 corner pins on the input photo to match the 4 corners of the site plot / sheet boundary.
3. Observe the live rectified orthophoto preview on the right panel.
4. Click **Apply Perspective Rectification**. The top-down rectified image will immediately load onto the main canvas.

---

## 4. Boundary Vectorization Modes

### Semi-Automatic Mode (Recommended)
1. Ensure **Semi-Automatic** is selected in the control panel.
2. The computer vision engine automatically segments the image and highlights candidate boundaries in faint cyan.
3. Click anywhere inside or near your desired land plot.
4. The system selects the boundary, approximates it to a polygon, displays bright emerald green polygon lines, and generates orange draggable vertex handles.
5. Adjust the **Polygon Approx ($\epsilon$)** slider (0.1% to 5.0%) to fine-tune boundary vertex density.

### Automatic Detection Mode
1. Select **Automatic Detection**.
2. The system automatically identifies all closed contours and selects the principal land parcel by area.

### Manual Polygon Draw & Edit Mode
- **Manual Draw**: Select **Manual Polygon Draw**. Click points sequentially around the boundary. Double-click or press Enter to close the polygon.
- **Manual Edit**:
  - **Move Vertex**: Click and drag any orange vertex handle.
  - **Insert Vertex**: Double-click on any polygon edge to insert a new vertex.
  - **Delete Vertex**: Right-click any vertex handle and select **Delete Vertex**.

---

## 5. Scale Calibration Engine
Raster image pixels do not represent physical units until calibrated.

### 2-Point Reference Line Calibration
1. Click **🎯 Click 2-Point Reference Line** (or press `Ctrl+K`).
2. Click the start point of a known dimension line or scale bar on the image.
3. Click the end point of the reference line.
4. An input dialog appears with the measured pixel distance: enter the real-world distance (e.g., `20.0`) and select the unit (`m`, `ft`, `cm`, `mm`, `in`).
5. Click **OK**. All coordinates, areas, and perimeters are instantly updated in real-world units.

---

## 6. Geometric Measurements & Validation
The **Measured Plot Geometry** card displays:
- **Calculated Area**: In $m^2$, $ft^2$, $yd^2$, $\text{acres}$, or $\text{hectares}$ with user-selected decimal precision (2 to 6 decimals).
- **Perimeter**: Sum of real-world boundary edge lengths.
- **Vertex Count**: Total number of polygon vertices.
- **Validity Checker**: Automatically verifies that the polygon is simple, non-self-intersecting, and has non-zero area.

---

## 7. AutoCAD Integration & Plugin Usage

### Exporting from Planimeter
1. Click **💾 Export for AutoCAD (.JSON)** (or press `Ctrl+E`).
2. Choose your destination file (e.g., `survey_plot_planimeter.json`).
3. The system automatically creates:
   - The structured JSON coordinate file.
   - An AutoCAD Script (`.scr`).
   - An AutoLISP command file (`.lsp`).

### Option A: Using the AutoCAD C# .NET Plugin
1. Open AutoCAD (2018–2026).
2. Type `NETLOAD` and select `autocad_plugin/bin/Release/NewPlanimeterPlugin.dll`.
3. Type `IMPORTPLANIMETER` in the AutoCAD command line.
4. Select the exported `.json` file.
5. AutoCAD will automatically:
   - Create layer `IMAGE_AREA_BOUNDARY` (Cyan) and draw the closed editable `LWPOLYLINE`.
   - Create layer `IMAGE_AREA_LABEL` (Yellow) and place `MText` with Area and Perimeter at the centroid.
   - Zoom to extents (`ZOOM E`).
   - Query native AutoCAD `pline.Area` and export `autocad_verification_result.json`.

### Option B: Drag-and-Drop AutoCAD Script (.SCR)
Simply drag the generated `.scr` file into any open AutoCAD drawing viewport! AutoCAD will execute the layer creation, polyline drawing, and zoom commands in under 1 second.

---

## 8. Accuracy Verification & Reporting
1. Click **🔍 Verify Accuracy vs AutoCAD**.
2. The verification dialog opens with a comparative error table:
   - **Planimeter Shoelace Area**
   - **AutoCAD Polyline Area**
   - **Ground Truth Area**
   - **Absolute Difference**
   - **Percentage Error**
   - **Tolerance Threshold Check ($\le 0.05\%$)**
3. Click **Export Markdown Report** or **Copy Report to Clipboard** to include in engineering submissions.
