"""
Interactive Canvas View for New Planimeter
High-performance QGraphicsView with smooth pan/zoom, sub-pixel snapping,
interactive vertex handle manipulation, rubber-band drawing, and calibration lines.
"""

from typing import List, Tuple, Optional, Dict, Any
import math
import cv2
import numpy as np

from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsPolygonItem, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsPathItem, QGraphicsSimpleTextItem, QGraphicsItem, QMenu
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QLineF
from PySide6.QtGui import (
    QImage, QPixmap, QPainter, QPen, QBrush, QColor,
    QFont, QPolygonF, QPainterPath, QCursor
)
from core.geometry_engine import GeometryEngine
from core.contour_detector import ContourCandidate


class CanvasMode:
    SEMI_AUTO = "semi_auto"
    AUTO = "auto"
    MANUAL_DRAW = "manual_draw"
    MANUAL_EDIT = "manual_edit"
    CALIBRATION_2PT = "calibration_2pt"


class VertexHandleItem(QGraphicsEllipseItem):
    """
    Interactive draggable handle for polygon vertices.
    """

    def __init__(self, index: int, x: float, y: float, radius: float = 6.0, parent_canvas=None):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.index = index
        self.radius = radius
        self.canvas = parent_canvas

        self.setPos(x, y)
        self.setZValue(100)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        # Style: bright orange with white border
        self.normal_brush = QBrush(QColor(255, 140, 0))
        self.hover_brush = QBrush(QColor(255, 220, 0))
        self.setBrush(self.normal_brush)
        self.setPen(QPen(QColor(255, 255, 255), 2))
        self.setToolTip(f"Vertex #{index + 1}: ({x:.1f}, {y:.1f}) px\nDrag to move | Right-click to delete")

    def hoverEnterEvent(self, event):
        self.setBrush(self.hover_brush)
        self.setScale(1.3)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.normal_brush)
        self.setScale(1.0)
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Notify canvas of live vertex drag
            if self.canvas and not getattr(self.canvas, "_updating_handles", False):
                self.canvas.on_vertex_dragged(self.index, value.x(), value.y())
        return super().itemChange(change, value)


class InteractiveCanvasView(QGraphicsView):
    """
    Hardware-accelerated engineering canvas for viewing, vectorizing, and editing plot boundaries.
    """

    polygonChanged = Signal(list)
    candidateSelected = Signal(int)
    calibrationPointsSelected = Signal(tuple, tuple)
    mouseMovedPixel = Signal(float, float)
    statusMessage = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Viewport configuration
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("background-color: #16181d; border: 1px solid #282a36;")

        # State
        self.mode = CanvasMode.SEMI_AUTO
        self.original_bgr: Optional[np.ndarray] = None
        self.current_pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.img_width = 0
        self.img_height = 0

        # Geometry & Contours
        self.candidates: List[ContourCandidate] = []
        self.active_polygon_points: List[Tuple[float, float]] = []
        self.selected_candidate_index: int = -1

        # Interactive Drawing & Handles
        self._updating_handles = False
        self.vertex_handles: List[VertexHandleItem] = []
        self.active_polygon_item: Optional[QGraphicsPolygonItem] = None
        self.candidate_path_items: List[QGraphicsPathItem] = []
        self.rubber_band_line: Optional[QGraphicsLineItem] = None
        self.drawing_points: List[Tuple[float, float]] = []

        # Calibration State
        self.calib_p1: Optional[Tuple[float, float]] = None
        self.calib_p2: Optional[Tuple[float, float]] = None
        self.calib_line_item: Optional[QGraphicsLineItem] = None
        self.calib_text_item: Optional[QGraphicsSimpleTextItem] = None

        # Panning State
        self._is_panning = False
        self._pan_start_pos = QPointF()

        self.setMouseTracking(True)

    def set_image(self, bgr_img: np.ndarray):
        """
        Load new image into the scene and reset coordinates.
        """
        self.original_bgr = bgr_img
        self.img_height, self.img_width = bgr_img.shape[:2]

        self.scene.clear()
        self.vertex_handles.clear()
        self.candidate_path_items.clear()
        self.active_polygon_item = None
        self.rubber_band_line = None
        self.calib_line_item = None
        self.calib_text_item = None

        rgb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, self.img_width, self.img_height, 3 * self.img_width, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)

        self.current_pixmap_item = self.scene.addPixmap(pix)
        self.current_pixmap_item.setZValue(0)
        self.scene.setSceneRect(0, 0, self.img_width, self.img_height)

        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        self.statusMessage.emit(f"Loaded image: {self.img_width} x {self.img_height} px")

    def set_mode(self, mode: str):
        self.mode = mode
        if mode == CanvasMode.MANUAL_DRAW:
            self.drawing_points = []
            self.setCursor(Qt.CrossCursor)
            self.statusMessage.emit("Manual Draw Mode: Click to add vertices. Double-click or press Enter to close polygon.")
        elif mode == CanvasMode.CALIBRATION_2PT:
            self.calib_p1 = None
            self.calib_p2 = None
            self.setCursor(Qt.CrossCursor)
            self.statusMessage.emit("Calibration Mode: Click first reference point, then click second point.")
        elif mode == CanvasMode.SEMI_AUTO:
            self.setCursor(Qt.PointingHandCursor)
            self.statusMessage.emit("Semi-Automatic Mode: Click inside or near any plot boundary to select it.")
        elif mode == CanvasMode.AUTO:
            self.setCursor(Qt.ArrowCursor)
            self.statusMessage.emit("Automatic Mode: Showing all detected closed contours.")
        else:
            self.setCursor(Qt.ArrowCursor)

    def set_candidates(self, candidates: List[ContourCandidate]):
        """
        Display detected candidate contours as faint reference paths on the canvas.
        """
        self.candidates = candidates
        # Clear old candidate items
        for item in self.candidate_path_items:
            self.scene.removeItem(item)
        self.candidate_path_items.clear()

        for c in candidates:
            path = QPainterPath()
            pts = c.polygon_points
            if len(pts) < 3:
                continue
            path.moveTo(pts[0][0], pts[0][1])
            for p in pts[1:]:
                path.lineTo(p[0], p[1])
            path.closeSubpath()

            item = self.scene.addPath(path)
            item.setPen(QPen(QColor(0, 245, 212, 100), 1.5, Qt.DashLine))
            item.setBrush(QBrush(QColor(0, 245, 212, 15)))
            item.setZValue(10)
            self.candidate_path_items.append(item)

    def set_active_polygon(self, points: List[Tuple[float, float]]):
        """
        Set and render the active measured polygon with vertex handles.
        """
        self.active_polygon_points = list(points)
        self.render_active_polygon()
        self.polygonChanged.emit(self.active_polygon_points)

    def render_active_polygon(self):
        """
        Render polygon outline and create/update interactive vertex handles.
        """
        if self.active_polygon_item:
            self.scene.removeItem(self.active_polygon_item)
            self.active_polygon_item = None

        if len(self.active_polygon_points) >= 3:
            poly = QPolygonF()
            for x, y in self.active_polygon_points:
                poly.append(QPointF(x, y))

            self.active_polygon_item = self.scene.addPolygon(poly)
            # Vibrant emerald green outline with semi-transparent cyan fill
            pen = QPen(QColor(0, 255, 128), 2.5, Qt.SolidLine)
            pen.setJoinStyle(Qt.RoundJoin)
            self.active_polygon_item.setPen(pen)
            self.active_polygon_item.setBrush(QBrush(QColor(0, 245, 212, 45)))
            self.active_polygon_item.setZValue(50)

        self.update_vertex_handles()

    def update_vertex_handles(self):
        """
        Re-synchronize draggable handles with current active polygon vertices.
        """
        self._updating_handles = True
        for h in self.vertex_handles:
            self.scene.removeItem(h)
        self.vertex_handles.clear()

        # Only show draggable handles in edit or semi-auto modes
        for i, (x, y) in enumerate(self.active_polygon_points):
            handle = VertexHandleItem(i, x, y, radius=5.0, parent_canvas=self)
            self.scene.addItem(handle)
            self.vertex_handles.append(handle)

        self._updating_handles = False

    def on_vertex_dragged(self, index: int, new_x: float, new_y: float):
        """
        Handle real-time vertex repositioning.
        """
        if 0 <= index < len(self.active_polygon_points):
            self.active_polygon_points[index] = (new_x, new_y)
            # Update polygon graphic
            if self.active_polygon_item:
                poly = QPolygonF()
                for x, y in self.active_polygon_points:
                    poly.append(QPointF(x, y))
                self.active_polygon_item.setPolygon(poly)
            self.polygonChanged.emit(self.active_polygon_points)

    def insert_vertex_on_edge(self, click_x: float, click_y: float):
        """
        Find closest polygon edge and insert a new vertex at the projected point.
        """
        n = len(self.active_polygon_points)
        if n < 3:
            return

        best_edge = -1
        min_dist = float("inf")
        insert_pt = (click_x, click_y)

        for i in range(n):
            p1 = np.array(self.active_polygon_points[i])
            p2 = np.array(self.active_polygon_points[(i + 1) % n])
            p = np.array([click_x, click_y])

            # Edge vector
            edge_vec = p2 - p1
            edge_len = np.linalg.norm(edge_vec)
            if edge_len < 1e-4:
                continue

            t = max(0.0, min(1.0, float(np.dot(p - p1, edge_vec) / (edge_len ** 2))))
            proj = p1 + t * edge_vec
            dist = float(np.linalg.norm(p - proj))

            if dist < min_dist and dist < 20.0:  # within 20px threshold
                min_dist = dist
                best_edge = i
                insert_pt = (float(proj[0]), float(proj[1]))

        if best_edge != -1:
            self.active_polygon_points.insert(best_edge + 1, insert_pt)
            self.render_active_polygon()
            self.polygonChanged.emit(self.active_polygon_points)
            self.statusMessage.emit(f"Inserted vertex #{best_edge + 2} at ({insert_pt[0]:.1f}, {insert_pt[1]:.1f})")

    def delete_vertex(self, index: int):
        if 0 <= index < len(self.active_polygon_points):
            if len(self.active_polygon_points) <= 3:
                self.statusMessage.emit("Cannot delete vertex: Minimum 3 vertices required.")
                return
            del self.active_polygon_points[index]
            self.render_active_polygon()
            self.polygonChanged.emit(self.active_polygon_points)
            self.statusMessage.emit(f"Deleted vertex #{index + 1}. Remaining: {len(self.active_polygon_points)} vertices.")

    # --------------------------------------------------------------------------
    # Mouse & Keyboard Event Handlers
    # --------------------------------------------------------------------------

    def wheelEvent(self, event):
        """
        Smooth cursor-centered zoom.
        """
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else (1.0 / 1.15)
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        px, py = scene_pos.x(), scene_pos.y()

        # Middle-click or Space+Left-click for panning
        if event.button() == Qt.MiddleButton or (event.button() == Qt.LeftButton and event.modifiers() & Qt.AltModifier):
            self._is_panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            if self.mode == CanvasMode.SEMI_AUTO:
                # Find candidate contour at click
                clicked_candidate = None
                for c in self.candidates:
                    if cv2.pointPolygonTest(c.raw_contour, (px, py), False) >= 0:
                        clicked_candidate = c
                        break
                if not clicked_candidate and self.candidates:
                    # Closest candidate
                    clicked_candidate = min(self.candidates, key=lambda c: abs(cv2.pointPolygonTest(c.raw_contour, (px, py), True)))

                if clicked_candidate:
                    self.selected_candidate_index = clicked_candidate.index
                    self.set_active_polygon(clicked_candidate.polygon_points)
                    self.candidateSelected.emit(clicked_candidate.index)
                    self.statusMessage.emit(f"Selected boundary #{clicked_candidate.index + 1} ({len(clicked_candidate.polygon_points)} vertices)")

            elif self.mode == CanvasMode.MANUAL_DRAW:
                self.drawing_points.append((px, py))
                self.set_active_polygon(self.drawing_points)
                self.statusMessage.emit(f"Added vertex #{len(self.drawing_points)}: ({px:.1f}, {py:.1f})")

            elif self.mode == CanvasMode.CALIBRATION_2PT:
                if self.calib_p1 is None:
                    self.calib_p1 = (px, py)
                    self.statusMessage.emit(f"Calibration Point 1 set: ({px:.1f}, {py:.1f}). Now click Point 2.")
                elif self.calib_p2 is None:
                    self.calib_p2 = (px, py)
                    self.render_calibration_line()
                    self.calibrationPointsSelected.emit(self.calib_p1, self.calib_p2)
                    self.statusMessage.emit(f"Calibration Reference line set! Length = {math.hypot(px - self.calib_p1[0], py - self.calib_p1[1]):.2f} px")

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            px, py = scene_pos.x(), scene_pos.y()

            if self.mode == CanvasMode.MANUAL_DRAW:
                # Close polygon
                if len(self.drawing_points) >= 3:
                    self.set_active_polygon(self.drawing_points)
                    self.set_mode(CanvasMode.MANUAL_EDIT)
                    self.statusMessage.emit(f"Closed polygon with {len(self.drawing_points)} vertices.")
            else:
                # Double click on edge to insert vertex
                self.insert_vertex_on_edge(px, py)

        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        self.mouseMovedPixel.emit(scene_pos.x(), scene_pos.y())

        if self._is_panning:
            delta = event.pos() - self._pan_start_pos
            self._pan_start_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        # Rubber-band line preview in manual draw or calibration mode
        if self.mode == CanvasMode.MANUAL_DRAW and self.drawing_points:
            last_pt = self.drawing_points[-1]
            if not self.rubber_band_line:
                self.rubber_band_line = self.scene.addLine(last_pt[0], last_pt[1], scene_pos.x(), scene_pos.y(),
                                                           QPen(QColor(255, 255, 0), 1.5, Qt.DashLine))
                self.rubber_band_line.setZValue(90)
            else:
                self.rubber_band_line.setLine(last_pt[0], last_pt[1], scene_pos.x(), scene_pos.y())

        elif self.mode == CanvasMode.CALIBRATION_2PT and self.calib_p1 and not self.calib_p2:
            if not self.rubber_band_line:
                self.rubber_band_line = self.scene.addLine(self.calib_p1[0], self.calib_p1[1], scene_pos.x(), scene_pos.y(),
                                                           QPen(QColor(255, 220, 0), 2, Qt.DashLine))
                self.rubber_band_line.setZValue(90)
            else:
                self.rubber_band_line.setLine(self.calib_p1[0], self.calib_p1[1], scene_pos.x(), scene_pos.y())

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_panning and event.button() in [Qt.MiddleButton, Qt.LeftButton]:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor if self.mode != CanvasMode.MANUAL_DRAW else Qt.CrossCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """
        Right-click context menu: delete vertex, close polygon, reset view.
        """
        scene_pos = self.mapToScene(event.pos())
        px, py = scene_pos.x(), scene_pos.y()

        menu = QMenu(self)

        # Check if clicked on a vertex handle
        item_under = self.itemAt(event.pos())
        if isinstance(item_under, VertexHandleItem):
            del_act = menu.addAction(f"Delete Vertex #{item_under.index + 1}")
            del_act.triggered.connect(lambda: self.delete_vertex(item_under.index))
            menu.addSeparator()

        add_v_act = menu.addAction("Insert Vertex on Nearest Edge")
        add_v_act.triggered.connect(lambda: self.insert_vertex_on_edge(px, py))

        if self.mode == CanvasMode.MANUAL_DRAW and len(self.drawing_points) >= 3:
            close_act = menu.addAction("Close Polygon")
            close_act.triggered.connect(lambda: self.set_mode(CanvasMode.MANUAL_EDIT))

        menu.addSeparator()
        reset_zoom_act = menu.addAction("Reset Zoom (Fit in View)")
        reset_zoom_act.triggered.connect(self.reset_view)

        menu.exec(event.globalPos())

    def render_calibration_line(self):
        """
        Render yellow dashed calibration reference line with endpoints and distance text.
        """
        if self.rubber_band_line:
            self.scene.removeItem(self.rubber_band_line)
            self.rubber_band_line = None

        if self.calib_line_item:
            self.scene.removeItem(self.calib_line_item)
            self.calib_line_item = None
        if self.calib_text_item:
            self.scene.removeItem(self.calib_text_item)
            self.calib_text_item = None

        if self.calib_p1 and self.calib_p2:
            x1, y1 = self.calib_p1
            x2, y2 = self.calib_p2
            pen = QPen(QColor(255, 220, 0), 2.5, Qt.DashLine)
            self.calib_line_item = self.scene.addLine(x1, y1, x2, y2, pen)
            self.calib_line_item.setZValue(80)

            dist_px = math.hypot(x2 - x1, y2 - y1)
            mid_x, mid_y = (x1 + x2) / 2.0, (y1 + y2) / 2.0
            self.calib_text_item = self.scene.addSimpleText(f"Ref Line: {dist_px:.1f} px", QFont("Segoe UI", 9, QFont.Bold))
            self.calib_text_item.setBrush(QBrush(QColor(255, 220, 0)))
            self.calib_text_item.setPos(mid_x + 5, mid_y - 15)
            self.calib_text_item.setZValue(85)

    def reset_view(self):
        if self.current_pixmap_item:
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
