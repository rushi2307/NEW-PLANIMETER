"""
Scale Calibration Dialog for New Planimeter
Configures 2-point reference calibration and multi-point least-squares scale estimation.
"""

from typing import List, Tuple, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QComboBox, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from core.calibration import ScaleCalibration, UnitManager


class CalibrationDialog(QDialog):
    """
    Scale calibration manager modal.
    """

    def __init__(self, calibration: ScaleCalibration, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scale Calibration Manager")
        self.resize(520, 420)
        self.calibration = calibration

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # Tab 1: 2-Point Known Reference
        tab2pt = QWidget()
        tab2pt_layout = QVBoxLayout(tab2pt)

        grp2pt = QGroupBox("2-Point Reference Line Details")
        f_layout = QVBoxLayout(grp2pt)

        # Distance input
        dist_h = QHBoxLayout()
        dist_lbl = QLabel("Known Reference Length:")
        self.dist_spin = QDoubleSpinBox()
        self.dist_spin.setRange(0.0001, 1000000.0)
        self.dist_spin.setDecimals(4)
        self.dist_spin.setValue(self.calibration.known_distance if self.calibration.known_distance > 0 else 10.0)
        dist_h.addWidget(dist_lbl)
        dist_h.addWidget(self.dist_spin)
        f_layout.addLayout(dist_h)

        # Unit selector
        unit_h = QHBoxLayout()
        unit_lbl = QLabel("Measurement Unit:")
        self.unit_combo = QComboBox()
        for u_code, u_name in UnitManager.LINEAR_NAMES.items():
            self.unit_combo.addItem(u_name, u_code)

        # Set active unit
        idx = self.unit_combo.findData(self.calibration.unit)
        if idx >= 0:
            self.unit_combo.setCurrentIndex(idx)
        unit_h.addWidget(unit_lbl)
        unit_h.addWidget(self.unit_combo)
        f_layout.addLayout(unit_h)

        # Status info
        px_d = self.calibration.pixel_distance
        scale_val = self.calibration.scale_factor
        status_text = (
            f"<b>Pixel Distance:</b> {px_d:.2f} px<br>"
            f"<b>Active Scale:</b> 1 px = {scale_val:.6f} {self.calibration.unit} "
            f"({(1.0/scale_val if scale_val > 0 else 0):.2f} px/{self.calibration.unit})"
        )
        self.status_lbl = QLabel(status_text)
        self.status_lbl.setStyleSheet("background-color: #222; padding: 10px; border-radius: 4px; color: #00f5d4;")
        f_layout.addWidget(self.status_lbl)

        tab2pt_layout.addWidget(grp2pt)
        tab2pt_layout.addStretch()
        tabs.addTab(tab2pt, "2-Point Reference (Standard)")

        # Tab 2: Manual Direct Scale Entry
        tab_man = QWidget()
        tab_man_layout = QVBoxLayout(tab_man)
        grp_man = QGroupBox("Direct Scale Factor Entry")
        man_f = QVBoxLayout(grp_man)

        scale_h = QHBoxLayout()
        scale_lbl = QLabel("Scale Factor (Units per Pixel):")
        self.direct_scale_spin = QDoubleSpinBox()
        self.direct_scale_spin.setRange(0.000001, 10000.0)
        self.direct_scale_spin.setDecimals(6)
        self.direct_scale_spin.setValue(self.calibration.scale_factor)
        scale_h.addWidget(scale_lbl)
        scale_h.addWidget(self.direct_scale_spin)
        man_f.addLayout(scale_h)

        tab_man_layout.addWidget(grp_man)
        tab_man_layout.addStretch()
        tabs.addTab(tab_man, "Direct Scale")

        layout.addWidget(tabs)

        # Action buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save & Apply Calibration")
        save_btn.setStyleSheet("background-color: #70e000; color: #000; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        save_btn.clicked.connect(self.save_calibration)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def save_calibration(self):
        unit = self.unit_combo.currentData()
        known_dist = self.dist_spin.value()

        if self.calibration.pixel_distance > 0:
            self.calibration.scale_factor = known_dist / self.calibration.pixel_distance
            self.calibration.known_distance = known_dist
            self.calibration.unit = unit
            self.calibration.is_calibrated = True
            self.calibration.calibration_type = "2-point"
        else:
            self.calibration.scale_factor = self.direct_scale_spin.value()
            self.calibration.unit = unit
            self.calibration.is_calibrated = True
            self.calibration.calibration_type = "manual"

        self.accept()
