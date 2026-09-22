"""
Data Exporter for New Planimeter
Handles structured JSON data exchange with AutoCAD .NET plugin,
CAD coordinate transformations, and fallback direct DXF/SCR/LISP generation.
"""

from typing import List, Tuple, Dict, Any, Optional
import os
import json
import datetime
from core.geometry_engine import GeometryEngine
from core.calibration import ScaleCalibration


class DataExporter:
    """
    Exports calibrated plot boundaries and metadata to JSON, DXF, SCR, and LISP for AutoCAD.
    """

    @classmethod
    def build_export_payload(cls,
                             points_px: List[Tuple[float, float]],
                             calibration: ScaleCalibration,
                             image_width: int,
                             image_height: int,
                             source_image_name: str = "",
                             boundary_layer: str = "IMAGE_AREA_BOUNDARY",
                             label_layer: str = "IMAGE_AREA_LABEL",
                             text_height: float = 1.0) -> Dict[str, Any]:
        """
        Assemble comprehensive JSON payload for AutoCAD .NET plugin.
        """
        scale = calibration.scale_factor
        unit = calibration.unit

        # Transform to CAD Cartesian coordinates (Y-up)
        cad_points = GeometryEngine.transform_pixels_to_cad(
            points_px, scale, float(image_height), origin_mode="bottom_left"
        )

        area_real = GeometryEngine.shoelace_area(cad_points)
        perimeter_real = GeometryEngine.polygon_perimeter(cad_points)
        centroid_cad = GeometryEngine.polygon_centroid(cad_points)
        centroid_px = GeometryEngine.polygon_centroid(points_px)

        payload = {
            "metadata": {
                "application": "New Planimeter",
                "version": "1.0.0",
                "export_timestamp": datetime.datetime.now().isoformat(),
                "source_image": os.path.basename(source_image_name),
                "image_width_px": image_width,
                "image_height_px": image_height,
            },
            "calibration": {
                "scale_factor": scale,
                "unit": unit,
                "is_calibrated": calibration.is_calibrated,
                "calibration_type": calibration.calibration_type,
                "known_distance": calibration.known_distance,
                "pixel_distance": calibration.pixel_distance,
                "pixels_per_unit": (1.0 / scale) if scale > 0 else 0.0
            },
            "geometry": {
                "vertex_count": len(cad_points),
                "area": area_real,
                "area_unit": f"{unit}²",
                "perimeter": perimeter_real,
                "perimeter_unit": unit,
                "centroid_cad": {"x": centroid_cad[0], "y": centroid_cad[1]},
                "centroid_px": {"x": centroid_px[0], "y": centroid_px[1]},
                "cad_vertices": [{"x": p[0], "y": p[1]} for p in cad_points],
                "image_vertices_px": [{"x": p[0], "y": p[1]} for p in points_px]
            },
            "autocad_settings": {
                "boundary_layer": boundary_layer,
                "boundary_color_index": 4,  # Cyan in AutoCAD ACI
                "label_layer": label_layer,
                "label_color_index": 2,     # Yellow in AutoCAD ACI
                "text_height": max(0.5, text_height),
                "auto_zoom": True,
                "create_closed_polyline": True,
                "annotate_area": True
            }
        }
        return payload

    @classmethod
    def export_json(cls, filepath: str, payload: Dict[str, Any]) -> str:
        """
        Write formatted JSON file for AutoCAD plugin.
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return filepath

    @classmethod
    def export_autocad_script(cls, filepath: str, payload: Dict[str, Any]) -> str:
        """
        Generate an AutoCAD .SCR (Script) file that can be dragged into any AutoCAD window
        to automatically create layers, draw the closed LWPOLYLINE, place text, and zoom extents.
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        geo = payload["geometry"]
        cad_pts = geo["cad_vertices"]
        unit = payload["calibration"]["unit"]
        area = geo["area"]
        perim = geo["perimeter"]
        cx = geo["centroid_cad"]["x"]
        cy = geo["centroid_cad"]["y"]
        acad = payload["autocad_settings"]

        lines = [
            "; --- New Planimeter AutoCAD Script ---",
            "; Automatically generated on " + payload["metadata"]["export_timestamp"],
            "-LAYER M " + acad["boundary_layer"] + " C 4 " + acad["boundary_layer"] + " ",
            "-LAYER M " + acad["label_layer"] + " C 2 " + acad["label_layer"] + " ",
            "-LAYER S " + acad["boundary_layer"] + " ",
            "PLINE"
        ]

        for pt in cad_pts:
            lines.append(f"{pt['x']:.6f},{pt['y']:.6f}")

        # Close polyline
        lines.append("C")

        # Place area annotation
        if acad.get("annotate_area", True):
            txt_h = acad.get("text_height", 1.0)
            label_text = f"Area: {area:.4f} {unit}\\PPerimeter: {perim:.4f} {unit}"
            lines.extend([
                "-LAYER S " + acad["label_layer"] + " ",
                f"-MTEXT {cx:.6f},{cy:.6f} H {txt_h:.4f} J MC {cx + 10:.6f},{cy - 5:.6f} {label_text} "
            ])

        # Zoom extents
        lines.append("ZOOM E")
        lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return filepath

    @classmethod
    def export_autolisp(cls, filepath: str, payload: Dict[str, Any]) -> str:
        """
        Generate an AutoLISP (.lsp) command (PLANIMETER_DRAW) for AutoCAD.
        """
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        geo = payload["geometry"]
        cad_pts = geo["cad_vertices"]
        unit = payload["calibration"]["unit"]
        area = geo["area"]
        perim = geo["perimeter"]
        cx = geo["centroid_cad"]["x"]
        cy = geo["centroid_cad"]["y"]
        b_layer = payload["autocad_settings"]["boundary_layer"]
        l_layer = payload["autocad_settings"]["label_layer"]
        txt_h = payload["autocad_settings"]["text_height"]

        pt_list_str = " ".join([f"'( {p['x']:.6f} {p['y']:.6f} 0.0)" for p in cad_pts])

        lisp = f""";; New Planimeter AutoLISP Generator
(defun c:PLANIMETER_DRAW ( / pts doc spc pline)
  (vl-load-com)
  (setq doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq spc (vla-get-ModelSpace doc))
  
  ;; Create layers
  (command "-LAYER" "M" "{b_layer}" "C" "4" "{b_layer}" "")
  (command "-LAYER" "M" "{l_layer}" "C" "2" "{l_layer}" "")
  (command "-LAYER" "S" "{b_layer}" "")
  
  ;; Draw polyline
  (command "PLINE")
"""
        for pt in cad_pts:
            lisp += f'  (command "{pt["x"]:.6f},{pt["y"]:.6f}")\n'

        lisp += f"""  (command "C")
  
  ;; Set label
  (command "-LAYER" "S" "{l_layer}" "")
  (command "-MTEXT" "{cx:.6f},{cy:.6f}" "H" "{txt_h:.4f}" "J" "MC" "@{txt_h*10},-{txt_h*5}" "Area: {area:.4f} {unit}\\PPerimeter: {perim:.4f} {unit}" "")
  
  (command "ZOOM" "E")
  (princ "\\n[New Planimeter] Plot geometry loaded successfully! Area = {area:.4f} {unit}²")
  (princ)
)
(princ "\\nType PLANIMETER_DRAW to generate plot in AutoCAD.")
(princ)
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(lisp)

        return filepath
