// ==============================================================================
// New Planimeter AutoCAD .NET Plugin - Command Definition Entry Point
// Implements commands: IMPORTPLANIMETER, PLANIMETERVERIFY, PLANIMETERINFO
// ==============================================================================

using System;
using System.IO;
using System.Windows.Forms;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Runtime;

[assembly: CommandClass(typeof(PlanimeterAutoCADPlugin.PlanimeterCommands))]

namespace PlanimeterAutoCADPlugin
{
    public class PlanimeterCommands
    {
        [CommandMethod("IMPORTPLANIMETER")]
        public void ImportPlanimeterCommand()
        {
            Document doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;
            Editor ed = doc.Editor;

            try
            {
                // Prompt user to select exported Planimeter JSON or use default
                PromptOpenFileOptions opt = new PromptOpenFileOptions("Select New Planimeter JSON Export File");
                opt.Filter = "Planimeter JSON (*.json)|*.json|All files (*.*)|*.*";
                opt.DialogCaption = "Import Planimeter Plot Geometry";

                PromptFileNameResult res = ed.GetFileNameForOpen(opt);
                if (res.Status != PromptStatus.OK)
                {
                    ed.WriteMessage("\n[New Planimeter] Import canceled by user.");
                    return;
                }

                string filePath = res.StringResult;
                ed.WriteMessage("\n[New Planimeter] Importing plot geometry from: " + filePath + "...");

                VerificationResponse response = PolylineImporter.ImportAndDraw(filePath, doc);

                ed.WriteMessage("\n=======================================================");
                ed.WriteMessage("\n[New Planimeter] Geometry imported successfully!");
                ed.WriteMessage(string.Format("\n  - AutoCAD Polyline Area : {0:F4} {1}²", response.autocad_polyline_area, response.unit));
                ed.WriteMessage(string.Format("\n  - App Shoelace Area     : {0:F4} {1}²", response.app_calculated_area, response.unit));
                ed.WriteMessage(string.Format("\n  - Absolute Difference   : {0:F6}", response.absolute_difference));
                ed.WriteMessage(string.Format("\n  - Percentage Error      : {0:F4}%", response.percentage_error));
                ed.WriteMessage(string.Format("\n  - Polyline Perimeter    : {0:F4} {1}", response.autocad_perimeter, response.unit));
                ed.WriteMessage(string.Format("\n  - Vertices Imported     : {0}", response.vertex_count));
                ed.WriteMessage(string.Format("\n  - Polyline Entity Handle: {0}", response.boundary_handle));
                ed.WriteMessage("\n=======================================================\n");
            }
            catch (System.Exception ex)
            {
                ed.WriteMessage("\n[New Planimeter ERROR] " + ex.Message);
            }
        }

        [CommandMethod("PLANIMETERVERIFY")]
        public void PlanimeterVerifyCommand()
        {
            Document doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;
            Editor ed = doc.Editor;

            ed.WriteMessage("\n[New Planimeter] Running accuracy verification module...");
            ImportPlanimeterCommand();
        }

        [CommandMethod("PLANIMETERINFO")]
        public void PlanimeterInfoCommand()
        {
            Document doc = Autodesk.AutoCAD.ApplicationServices.Application.DocumentManager.MdiActiveDocument;
            if (doc == null) return;
            Editor ed = doc.Editor;

            ed.WriteMessage("\n=======================================================");
            ed.WriteMessage("\n  New Planimeter - AutoCAD Integration Suite v1.0");
            ed.WriteMessage("\n  Image-Based Plot Area Measurement & CAD Polyline Generator");
            ed.WriteMessage("\n  Commands available:");
            ed.WriteMessage("\n    - IMPORTPLANIMETER : Select and import calibrated JSON polygon");
            ed.WriteMessage("\n    - PLANIMETERVERIFY : Verify polygon area against Shoelace formula");
            ed.WriteMessage("\n    - PLANIMETERINFO   : Show plugin build information");
            ed.WriteMessage("\n=======================================================\n");
        }
    }
}
