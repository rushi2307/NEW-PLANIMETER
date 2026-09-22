"""
Control Panel for New Planimeter
Engineering dashboard housing preprocessing sliders, boundary mode selectors,
calibration tools, live measurement readouts, and AutoCAD export actions.
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QGroupBox, QRadioButton, QButtonGroup, QScrollArea, QFrame,
    QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from core.calibration import UnitManager, ScaleCalibration
from gui.canvas_view import CanvasMode


class ControlPanel(QWidget):
    """
    Sidebar control and engineering readout panel.
    """

    # Signals
    preprocessingChanged = Signal(dict)
    modeChanged = Signal(str)
    epsilonChanged = Signal(float)
    calibrationRequested = Signal()
    unitChanged = Signal(str)
    exportJsonRequested = Signal()
    exportScrRequested = Signal()
    verifyRequested = Signal()
    perspectiveRequested = Signal()
    resetViewRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(340)
        self.setMaximumWidth(420)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1c23;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #2e3440;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 14px;
                background-color: #1e212b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #00f5d4;
            }
            QPushButton {
                background-color: #2b2f3a;
                border: 1px solid #3b4252;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #3b4252;
                border-color: #00f5d4;
            }
            QPushButton:pressed {
                background-color: #00f5d4;
                color: #000;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #2b2f3a;
                border: 1px solid #3b4252;
                border-radius: 4px;
                padding: 4px 8px;
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #2b2f3a;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #00f5d4;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 1px solid #00f5d4;
                width: 14px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 7px;
            }
        """)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        # ----------------------------------------------------------------------
        # 1. Measurement Mode Selector (Semi-Auto Recommended Default)
        # ----------------------------------------------------------------------
        mode_grp = QGroupBox("1. Measurement Mode")
        mode_l = QVBoxLayout(mode_grp)

        self.btn_mode_semi = QRadioButton("Semi-Automatic (Recommended)")
        self.btn_mode_semi.setChecked(True)
        self.btn_mode_semi.setToolTip("Auto-detects candidate boundaries. Click on desired plot region to select.")
        self.btn_mode_semi.setStyleSheet("color: #00f5d4; font-weight: bold;")

        self.btn_mode_auto = QRadioButton("Automatic Detection")
        self.btn_mode_auto.setToolTip("Auto-detects and highlights all closed contours on the plan.")

        self.btn_mode_draw = QRadioButton("Manual Polygon Draw")
        self.btn_mode_draw.setToolTip("Click point-by-point to draw an irregular boundary.")

        self.btn_mode_edit = QRadioButton("Manual Vertex Edit (Drag/Insert)")
        self.btn_mode_edit.setToolTip("Drag vertices to fine-tune, double-click edges to insert, right-click to delete.")

        self.mode_btn_group = QButtonGroup(self)
        self.mode_btn_group.addButton(self.btn_mode_semi, 1)
        self.mode_btn_group.addButton(self.btn_mode_auto, 2)
        self.mode_btn_group.addButton(self.btn_mode_draw, 3)
        self.mode_btn_group.addButton(self.btn_mode_edit, 4)
        self.mode_btn_group.idClicked.connect(self._on_mode_radio_clicked)

        mode_l.addWidget(self.btn_mode_semi)
        mode_l.addWidget(self.btn_mode_auto)
        mode_l.addWidget(self.btn_mode_draw)
        mode_l.addWidget(self.btn_mode_edit)

        # Douglas-Peucker Epsilon slider
        eps_h = QHBoxLayout()
        eps_lbl = QLabel("Polygon Approx (ε):")
        self.eps_slider = QSlider(Qt.Horizontal)
        self.eps_slider.setRange(1, 50)  # 0.1% to 5.0%
        self.eps_slider.setValue(10)     # default 1.0%
        self.eps_val_lbl = QLabel("1.0 %")
        self.eps_slider.valueChanged.connect(self._on_eps_slider_changed)

        eps_h.addWidget(eps_lbl)
        eps_h.addWidget(self.eps_slider)
        eps_h.addWidget(self.eps_val_lbl)
        mode_l.addLayout(eps_h)

        layout.addWidget(mode_grp)

        # ----------------------------------------------------------------------
        # 2. Scale Calibration Panel
        # ----------------------------------------------------------------------
        calib_grp = QGroupBox("2. Scale Calibration")
        calib_l = QVBoxLayout(calib_grp)

        self.calib_btn = QPushButton("🎯 Click 2-Point Reference Line")
        self.calib_btn.setStyleSheet("background-color: #ff9e00; color: #000; font-weight: bold;")
        self.calib_btn.clicked.connect(lambda: self.calibrationRequested.emit())
        calib_l.addWidget(self.calib_btn)

        # Unit selector
        unit_h = QHBoxLayout()
        unit_lbl = QLabel("Unit:")
        self.unit_combo = QComboBox()
        for u_code, u_name in UnitManager.LINEAR_NAMES.items():
            self.unit_combo.addItem(u_name, u_code)
        self.unit_combo.currentIndexChanged.connect(self._on_unit_combo_changed)
        unit_h.addWidget(unit_lbl)
        unit_h.addWidget(self.unit_combo)
        calib_l.addLayout(unit_h)

        # Scale status readout
        self.scale_status_lbl = QLabel("Scale: 1 px = 1.000000 m (Uncalibrated)")
        self.scale_status_lbl.setStyleSheet("color: #ffb703; font-size: 11px;")
        self.scale_status_lbl.setWordWrap(True)
        calib_l.addWidget(self.scale_status_lbl)

        layout.addWidget(calib_grp)

        # ----------------------------------------------------------------------
        # 3. Live Geometry Measurement Readout
        # ----------------------------------------------------------------------
        res_grp = QGroupBox("3. Measured Plot Geometry")
        res_l = QVBoxLayout(res_grp)

        # Big Area Card
        self.area_card = QFrame()
        self.area_card.setStyleSheet("background-color: #11141a; border: 1px solid #00f5d4; border-radius: 6px; padding: 6px;")
        card_l = QVBoxLayout(self.area_card)
        card_l.setContentsMargins(4, 4, 4, 4)

        card_title = QLabel("CALCULATED REAL-WORLD AREA")
        card_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        card_title.setStyleSheet("color: #888;")
        self.area_value_lbl = QLabel("0.0000 m²")
        self.area_value_lbl.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.area_value_lbl.setStyleSheet("color: #00f5d4;")
        self.area_value_lbl.setAlignment(Qt.AlignCenter)

        card_l.addWidget(card_title, alignment=Qt.AlignCenter)
        card_l.addWidget(self.area_value_lbl, alignment=Qt.AlignCenter)
        res_l.addWidget(self.area_card)

        # Perimeter & Vertices
        self.perim_lbl = QLabel("<b>Perimeter:</b> 0.0000 m")
        self.vertices_lbl = QLabel("<b>Vertices:</b> 0 points")
        self.valid_lbl = QLabel("<span style='color: #70e000;'>✔ Valid Simple Polygon</span>")

        res_l.addWidget(self.perim_lbl)
        res_l.addWidget(self.vertices_lbl)
        res_l.addWidget(self.valid_lbl)

        # Decimal precision selector
        dec_h = QHBoxLayout()
        dec_lbl = QLabel("Display Decimals:")
        self.dec_spin = QSpinBox()
        self.dec_spin.setRange(2, 6)
        self.dec_spin.setValue(4)
        dec_h.addWidget(dec_lbl)
        dec_h.addWidget(self.dec_spin)
        res_l.addLayout(dec_h)

        layout.addWidget(res_grp)

        # ----------------------------------------------------------------------
        # 4. AutoCAD Integration & Accuracy Verification
        # ----------------------------------------------------------------------
        cad_grp = QGroupBox("4. AutoCAD Integration")
        cad_l = QVBoxLayout(cad_grp)

        self.export_json_btn = QPushButton("💾 Export for AutoCAD (.JSON)")
        self.export_json_btn.setStyleSheet("background-color: #00b4d8; color: #000; font-weight: bold;")
        self.export_json_btn.clicked.connect(lambda: self.exportJsonRequested.emit())
        cad_l.addWidget(self.export_json_btn)

        self.export_scr_btn = QPushButton("📐 Generate AutoCAD Script (.SCR)")
        self.export_scr_btn.setToolTip("Generates script that draws layers, closed polyline, centroid area text and zooms extents.")
        self.export_scr_btn.clicked.connect(lambda: self.exportScrRequested.emit())
        cad_l.addWidget(self.export_scr_btn)

        self.verify_btn = QPushButton("🔍 Verify Accuracy vs AutoCAD")
        self.verify_btn.setStyleSheet("background-color: #70e000; color: #000; font-weight: bold;")
        self.verify_btn.clicked.connect(lambda: self.verifyRequested.emit())
        cad_l.addWidget(self.verify_btn)

        layout.addWidget(cad_grp)

        # ----------------------------------------------------------------------
        # 5. Image Preprocessing & Filters (Collapsible / Advanced)
        # ----------------------------------------------------------------------
        proc_grp = QGroupBox("5. Image Processing Filters (Tuning)")
        proc_l = QVBoxLayout(proc_grp)

        # Perspective button
        persp_btn = QPushButton("🔄 4-Point Perspective Rectification")
        persp_btn.clicked.connect(lambda: self.perspectiveRequested.emit())
        proc_l.addWidget(persp_btn)

        # Threshold method
        thresh_h = QHBoxLayout()
        t_lbl = QLabel("Threshold:")
        self.thresh_combo = QComboBox()
        self.thresh_combo.addItems(["Otsu (Auto)", "Adaptive Gaussian", "Adaptive Mean", "Manual Binary"])
        self.thresh_combo.currentIndexChanged.connect(self._emit_pipeline)
        thresh_h.addWidget(t_lbl)
        thresh_h.addWidget(self.thresh_combo)
        proc_l.addLayout(thresh_h)

        # Threshold value slider (for manual)
        th_val_h = QHBoxLayout()
        th_val_lbl = QLabel("Thresh Val:")
        self.thresh_slider = QSlider(Qt.Horizontal)
        self.thresh_slider.setRange(0, 255)
        self.thresh_slider.setValue(127)
        self.thresh_slider.valueChanged.connect(self._emit_pipeline)
        th_val_h.addWidget(th_val_lbl)
        th_val_h.addWidget(self.thresh_slider)
        proc_l.addLayout(th_val_h)

        # Noise filter
        noise_h = QHBoxLayout()
        n_lbl = QLabel("Denoise:")
        self.blur_combo = QComboBox()
        self.blur_combo.addItems(["Gaussian", "Bilateral", "Median", "None"])
        self.blur_combo.currentIndexChanged.connect(self._emit_pipeline)
        noise_h.addWidget(n_lbl)
        noise_h.addWidget(self.blur_combo)
        proc_l.addLayout(noise_h)

        # Invert toggle
        self.invert_cb = QCheckBox("Invert Binary (Dark Lines on Light BG)")
        self.invert_cb.setChecked(True)
        self.invert_cb.stateChanged.connect(self._emit_pipeline)
        proc_l.addWidget(self.invert_cb)

        # Canny toggle
        self.canny_cb = QCheckBox("Use Canny Edge Detector")
        self.canny_cb.setChecked(False)
        self.canny_cb.stateChanged.connect(self._emit_pipeline)
        proc_l.addWidget(self.canny_cb)

        # Morphology
        morph_h = QHBoxLayout()
        m_lbl = QLabel("Morphology:")
        self.morph_combo = QComboBox()
        self.morph_combo.addItems(["Close (Bridge Gaps)", "Open (Remove Noise)", "Dilate", "Erode", "None"])
        self.morph_combo.currentIndexChanged.connect(self._emit_pipeline)
        morph_h.addWidget(m_lbl)
        morph_h.addWidget(self.morph_combo)
        proc_l.addLayout(morph_h)

        layout.addWidget(proc_grp)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _on_mode_radio_clicked(self, btn_id: int):
        if btn_id == 1:
            self.modeChanged.emit(CanvasMode.SEMI_AUTO)
        elif btn_id == 2:
            self.modeChanged.emit(CanvasMode.AUTO)
        elif btn_id == 3:
            self.modeChanged.emit(CanvasMode.MANUAL_DRAW)
        elif btn_id == 4:
            self.modeChanged.emit(CanvasMode.MANUAL_EDIT)

    def _on_eps_slider_changed(self, val: int):
        eps_float = val / 10.0
        self.eps_val_lbl.setText(f"{eps_float:.1f} %")
        self.epsilonChanged.emit(eps_float)

    def _on_unit_combo_changed(self, idx: int):
        unit_code = self.unit_combo.currentData()
        self.unitChanged.emit(unit_code)

    def _emit_pipeline(self):
        method_map = {
            0: "otsu",
            1: "adaptive_gaussian",
            2: "adaptive_mean",
            3: "binary"
        }
        blur_map = {
            0: "gaussian",
            1: "bilateral",
            2: "median",
            3: "none"
        }
        morph_map = {
            0: "close",
            1: "open",
            2: "dilate",
            3: "erode",
            4: "none"
        }

        params = {
            "thresh_method": method_map.get(self.thresh_combo.currentIndex(), "otsu"),
            "thresh_val": self.thresh_slider.value(),
            "blur_method": blur_map.get(self.blur_combo.currentIndex(), "gaussian"),
            "blur_ksize": 5,
            "invert": self.invert_cb.isChecked(),
            "use_canny": self.canny_cb.isChecked(),
            "morph_op": morph_map.get(self.morph_combo.currentIndex(), "close"),
            "morph_ksize": 3,
            "morph_iter": 1
        }
        self.preprocessingChanged.emit(params)

    def update_measurement_readout(self, area: float, perimeter: float,
                                   vertex_count: int, unit: str,
                                   validation: Dict[str, Any]):
        dec = self.dec_spin.value()
        self.area_value_lbl.setText(f"{area:.{dec}f} {unit}²")
        self.perim_lbl.setText(f"<b>Perimeter:</b> {perimeter:.{dec}f} {unit}")
        self.vertices_lbl.setText(f"<b>Vertices:</b> {vertex_count} points")

        if validation.get("is_valid", True):
            self.valid_lbl.setText("<span style='color: #70e000;'>✔ Valid Simple Polygon</span>")
        else:
            err = "; ".join(validation.get("errors", ["Invalid polygon"]))
            self.valid_lbl.setText(f"<span style='color: #ff0055;'>✖ {err}</span>")

    def update_calibration_readout(self, calibration: ScaleCalibration):
        scale = calibration.scale_factor
        unit = calibration.unit
        if calibration.is_calibrated:
            self.scale_status_lbl.setText(
                f"<b>Scale:</b> 1 px = {scale:.6f} {unit} ({(1.0/scale if scale > 0 else 0):.2f} px/{unit})<br>"
                f"<span style='color:#00f5d4;'>Calibrated via {calibration.calibration_type}</span>"
            )
        else:
            self.scale_status_lbl.setText("<b>Scale:</b> 1 px = 1.000000 m (Uncalibrated)")
