"""
Accuracy Verification & Comparative Report Dialog for New Planimeter
Displays comparison table between App Area, AutoCAD Area, Ground Truth, and Tolerance check.
"""

from typing import List, Optional
import os
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox,
    QGroupBox, QFileDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from core.accuracy_verifier import AccuracyMetrics, AccuracyVerifier


class VerificationDialog(QDialog):
    """
    Accuracy Verification and Error Comparison Window.
    """

    def __init__(self, metrics: AccuracyMetrics, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AutoCAD Integration & Geometric Accuracy Verification")
        self.resize(750, 520)
        self.metrics = metrics

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header Title
        title_lbl = QLabel("<h2>Accuracy Verification & Error Analysis</h2>")
        title_lbl.setStyleSheet("color: #00f5d4; margin-bottom: 0px;")
        layout.addWidget(title_lbl)

        sub_lbl = QLabel(
            "Compares the polygon area computed via Gauss's Shoelace formula with the native "
            "AutoCAD polyline database geometry (.Area) and ground truth reference."
        )
        sub_lbl.setStyleSheet("color: #bbb; font-size: 13px; margin-bottom: 8px;")
        sub_lbl.setWordWrap(True)
        layout.addWidget(sub_lbl)

        # Tolerance control box
        tol_layout = QHBoxLayout()
        tol_lbl = QLabel("<b>Acceptable Error Tolerance:</b>")
        self.tol_spin = QDoubleSpinBox()
        self.tol_spin.setRange(0.001, 10.0)
        self.tol_spin.setDecimals(3)
        self.tol_spin.setSuffix(" %")
        self.tol_spin.setValue(self.metrics.tolerance_percent)
        self.tol_spin.valueChanged.connect(self.on_tolerance_changed)

        tol_layout.addWidget(tol_lbl)
        tol_layout.addWidget(self.tol_spin)
        tol_layout.addStretch()

        # Status badge
        self.status_badge = QLabel()
        self.status_badge.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setMinimumWidth(160)
        tol_layout.addWidget(self.status_badge)

        layout.addLayout(tol_layout)

        # Comparison Table
        self.table = QTableWidget(5, 2)
        self.table.setHorizontalHeaderLabels(["Metric / Parameter", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("QTableWidget { background-color: #1e1e24; color: #fff; gridline-color: #333; }")

        layout.addWidget(self.table, 1)

        # Populate table
        self.refresh_table()

        # Bottom Buttons
        btn_layout = QHBoxLayout()

        copy_btn = QPushButton("Copy Report to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)

        export_md_btn = QPushButton("Export Markdown Report")
        export_md_btn.clicked.connect(self.export_markdown)

        export_json_btn = QPushButton("Export JSON Result")
        export_json_btn.clicked.connect(self.export_json)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 6px 16px;")
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(export_md_btn)
        btn_layout.addWidget(export_json_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def refresh_table(self):
        m = self.metrics
        unit = m.unit

        rows = [
            ("Plot / Shape Name", m.shape_name),
            ("New Planimeter Calculated Area (Shoelace)", f"{m.app_area:.6f} {unit}"),
            ("AutoCAD Native Polyline Area", f"{m.autocad_area:.6f} {unit}" if m.autocad_area is not None else "N/A (AutoCAD plugin output pending)"),
            ("Absolute Area Difference (|App - CAD|)", f"{m.acad_abs_diff:.6f} {unit}"),
            ("Percentage Error (App vs CAD)", f"{m.acad_percent_error:.4f} %"),
        ]

        if m.ground_truth_area is not None:
            rows.extend([
                ("Ground Truth Reference Area", f"{m.ground_truth_area:.6f} {unit}"),
                ("Ground Truth Percentage Error", f"{m.gt_percent_error:.4f} %")
            ])

        if m.execution_time_ms > 0:
            rows.append(("Processing & Calculation Time", f"{m.execution_time_ms:.2f} ms"))

        self.table.setRowCount(len(rows))
        for r, (k, v) in enumerate(rows):
            item_k = QTableWidgetItem(k)
            item_k.setFlags(Qt.ItemIsEnabled)
            item_k.setFont(QFont("Segoe UI", 10, QFont.Bold))
            item_v = QTableWidgetItem(str(v))
            item_v.setFlags(Qt.ItemIsEnabled)
            item_v.setFont(QFont("Segoe UI", 10))

            if "Percentage Error" in k:
                if m.acad_within_tolerance:
                    item_v.setForeground(QColor(0, 245, 212))
                else:
                    item_v.setForeground(QColor(255, 100, 100))

            self.table.setItem(r, 0, item_k)
            self.table.setItem(r, 1, item_v)

        # Update Badge
        if m.acad_within_tolerance:
            self.status_badge.setText("STATUS: PASS (Within Tolerance)")
            self.status_badge.setStyleSheet("background-color: #2b7a0b; color: #fff; padding: 6px 12px; border-radius: 4px;")
        else:
            self.status_badge.setText("STATUS: WARNING (Exceeds Tolerance)")
            self.status_badge.setStyleSheet("background-color: #b7094c; color: #fff; padding: 6px 12px; border-radius: 4px;")

    def on_tolerance_changed(self, val: float):
        self.metrics.tolerance_percent = val
        if self.metrics.autocad_area is not None and self.metrics.autocad_area > 0:
            self.metrics.acad_within_tolerance = self.metrics.acad_percent_error <= val
        self.refresh_table()

    def get_report_text(self) -> str:
        return AccuracyVerifier.generate_markdown_report([self.metrics])

    def copy_to_clipboard(self):
        text = self.get_report_text()
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", "Accuracy report copied to clipboard!")

    def export_markdown(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Markdown Accuracy Report", "Accuracy_Report.md", "Markdown (*.md)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.get_report_text())
            QMessageBox.information(self, "Exported", f"Report saved successfully to:\n{path}")

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Verification JSON", "accuracy_verification.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.metrics.to_dict(), f, indent=2)
            QMessageBox.information(self, "Exported", f"Verification JSON saved to:\n{path}")
