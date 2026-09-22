"""
Perspective Correction Dialog for New Planimeter
Allows selecting 4 points on an angled photograph and computing homography for orthorectification.
"""

from typing import List, Tuple, Optional
import cv2
import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QBrush
from core.image_processor import ImageProcessor


class PerspectiveCanvas(QLabel):
    """
    Canvas for placing and dragging 4 perspective quad corner pins.
    """
    pointsChanged = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 400)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")
        self.original_img: Optional[np.ndarray] = None
        self.display_pixmap: Optional[QPixmap] = None
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

        # 4 Corner points in image pixel coordinates [TL, TR, BR, BL]
        self.corner_points: List[Tuple[float, float]] = []
        self.dragged_index: int = -1

    def set_image(self, img: np.ndarray):
        self.original_img = img
        h, w = img.shape[:2]
        # Default 4 corners with 10% margin
        margin_x = w * 0.1
        margin_y = h * 0.1
        self.corner_points = [
            (margin_x, margin_y),
            (w - margin_x, margin_y),
            (w - margin_x, h - margin_y),
            (margin_x, h - margin_y)
        ]
        self.update_display()
        self.pointsChanged.emit(self.corner_points)

    def update_display(self):
        if self.original_img is None:
            return

        h, w = self.original_img.shape[:2]
        # Convert BGR to RGB
        rgb = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)

        # Scale pixmap to fit widget
        lbl_w = max(10, self.width())
        lbl_h = max(10, self.height())
        scaled_pix = pix.scaled(lbl_w, lbl_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.scale_x = scaled_pix.width() / float(w)
        self.scale_y = scaled_pix.height() / float(h)
        self.offset_x = (lbl_w - scaled_pix.width()) / 2.0
        self.offset_y = (lbl_h - scaled_pix.height()) / 2.0

        # Draw quad polygon and pins
        painter = QPainter(scaled_pix)
        painter.setRenderHint(QPainter.Antialiasing)

        if len(self.corner_points) == 4:
            # Draw polygon lines
            poly_points = []
            for px, py in self.corner_points:
                sx = px * self.scale_x
                sy = py * self.scale_y
                poly_points.append(QPointF(sx, sy))

            pen = QPen(QColor(255, 0, 128), 2, Qt.SolidLine)
            painter.setPen(pen)
            brush = QBrush(QColor(255, 0, 128, 40))
            painter.setBrush(brush)
            painter.drawPolygon(poly_points)

            # Draw 4 corner pins with labels
            labels = ["1: Top-Left", "2: Top-Right", "3: Bottom-Right", "4: Bottom-Left"]
            colors = [QColor(0, 255, 200), QColor(0, 200, 255), QColor(255, 200, 0), QColor(255, 100, 0)]

            for i, (px, py) in enumerate(self.corner_points):
                sx = px * self.scale_x
                sy = py * self.scale_y
                painter.setBrush(QBrush(colors[i]))
                painter.setPen(QPen(Qt.white, 2))
                painter.drawEllipse(QPointF(sx, sy), 8, 8)
                painter.setPen(QPen(Qt.white))
                painter.drawText(int(sx + 12), int(sy + 5), labels[i])

        painter.end()
        self.setPixmap(scaled_pix)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.original_img is not None:
            click_x = (event.position().x() - self.offset_x) / self.scale_x
            click_y = (event.position().y() - self.offset_y) / self.scale_y

            # Check if clicked near one of the 4 pins (threshold 25px in display scale)
            thresh = 25.0 / self.scale_x
            for i, (px, py) in enumerate(self.corner_points):
                if (px - click_x) ** 2 + (py - click_y) ** 2 <= thresh ** 2:
                    self.dragged_index = i
                    break

    def mouseMoveEvent(self, event):
        if self.dragged_index != -1 and self.original_img is not None:
            h, w = self.original_img.shape[:2]
            new_x = (event.position().x() - self.offset_x) / self.scale_x
            new_y = (event.position().y() - self.offset_y) / self.scale_y
            new_x = max(0, min(w - 1, new_x))
            new_y = max(0, min(h - 1, new_y))

            self.corner_points[self.dragged_index] = (new_x, new_y)
            self.update_display()
            self.pointsChanged.emit(self.corner_points)

    def mouseReleaseEvent(self, event):
        self.dragged_index = -1


class PerspectiveDialog(QDialog):
    """
    Dialog for Perspective Homography Rectification.
    """

    def __init__(self, original_img: np.ndarray, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Perspective Correction - 4-Point Homography")
        self.resize(1000, 600)
        self.original_img = original_img
        self.corrected_img: Optional[np.ndarray] = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        info_lbl = QLabel(
            "<b>Instructions:</b> Drag the 4 corner pins to match the four corners of the land plot / plan boundary. "
            "The algorithm calculates homography and rectifies the photo into a top-down orthographic plan."
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #ddd; font-size: 13px; margin-bottom: 5px;")
        layout.addWidget(info_lbl)

        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Input with 4 pins
        left_grp = QGroupBox("1. Position 4 Reference Corner Pins (Input Photo)")
        left_layout = QVBoxLayout(left_grp)
        self.canvas = PerspectiveCanvas()
        self.canvas.set_image(self.original_img)
        self.canvas.pointsChanged.connect(self.update_preview)
        left_layout.addWidget(self.canvas)
        splitter.addWidget(left_grp)

        # Right panel: Live Rectified Preview
        right_grp = QGroupBox("2. Rectified Top-Down Preview")
        right_layout = QVBoxLayout(right_grp)
        self.preview_lbl = QLabel("Drag pins on left to generate preview.")
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        self.preview_lbl.setStyleSheet("background-color: #111; color: #888; border: 1px solid #333;")
        right_layout.addWidget(self.preview_lbl)
        splitter.addWidget(right_grp)

        layout.addWidget(splitter, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply Perspective Rectification")
        self.apply_btn.setStyleSheet("background-color: #00f5d4; color: #000; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
        self.apply_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("padding: 8px 16px; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)

        self.update_preview(self.canvas.corner_points)

    def update_preview(self, points: List[Tuple[float, float]]):
        if len(points) == 4 and self.original_img is not None:
            try:
                warped, _ = ImageProcessor.perspective_homography(self.original_img, points)
                self.corrected_img = warped
                h, w = warped.shape[:2]
                rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
                qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
                pix = QPixmap.fromImage(qimg)
                scaled = pix.scaled(self.preview_lbl.width(), self.preview_lbl.height(),
                                    Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_lbl.setPixmap(scaled)
            except Exception as e:
                self.preview_lbl.setText(f"Preview error: {e}")

    def get_corrected_image(self) -> Optional[np.ndarray]:
        return self.corrected_img
