"""
AutoCAD Script, LISP Generator and Live COM Bridge for New Planimeter
Provides instant AutoCAD automation via SCR/LISP scripts and COM interop.
"""

from typing import Dict, Any, Optional
import os
import json
from core.data_exporter import DataExporter


class AutoCADScriptGenerator:
    """
    Automates drawing and verification in AutoCAD across all versions.
    """

    @staticmethod
    def generate_all_cad_artifacts(json_path: str) -> Dict[str, str]:
        """
        Given an exported Planimeter JSON file, generate both .scr and .lsp files.
        """
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"JSON file not found: {json_path}")

        with open(json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        base, _ = os.path.splitext(json_path)
        scr_path = base + ".scr"
        lsp_path = base + ".lsp"

        DataExporter.export_autocad_script(scr_path, payload)
        DataExporter.export_autolisp(lsp_path, payload)

        return {
            "json": json_path,
            "scr": scr_path,
            "lsp": lsp_path
        }

    @staticmethod
    def launch_in_running_autocad(json_path: str) -> Dict[str, Any]:
        """
        Attempts to communicate with running AutoCAD instance via Windows COM ActiveX.
        If AutoCAD is not running, generates .scr and provides ready-to-run instructions.
        """
        artifacts = AutoCADScriptGenerator.generate_all_cad_artifacts(json_path)
        scr_path = artifacts["scr"]

        result = {
            "success": False,
            "message": "",
            "scr_path": scr_path,
            "cad_area": None
        }

        try:
            import win32com.client
            acad = win32com.client.GetActiveObject("AutoCAD.Application")
            doc = acad.ActiveDocument
            doc.SendCommand(f'(command "SCRIPT" "{scr_path.replace(os.sep, "/")}")\n')
            result["success"] = True
            result["message"] = "Sent geometry script directly to active AutoCAD document!"
        except Exception as e:
            result["success"] = False
            result["message"] = (
                f"AutoCAD is not actively running or COM is busy ({e}). "
                f"Script generated at: {scr_path}. Drag and drop into AutoCAD or type SCRIPT in AutoCAD."
            )

        return result
