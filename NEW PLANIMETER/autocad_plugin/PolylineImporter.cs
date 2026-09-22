// ==============================================================================
// New Planimeter AutoCAD .NET Plugin - Polyline Importer & Transaction Engine
// Creates layers, closed polylines, centroid annotations, and queries native CAD area.
// ==============================================================================

using System;
using System.IO;
using System.Text;
using System.Web.Script.Serialization; // Standard .NET Framework JSON serializer
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.Geometry;
using Autodesk.AutoCAD.Colors;

namespace PlanimeterAutoCADPlugin
{
    public static class PolylineImporter
    {
        public static VerificationResponse ImportAndDraw(string jsonFilePath, Document doc)
        {
            if (!File.Exists(jsonFilePath))
            {
                throw new FileNotFoundException("Specified Planimeter JSON file was not found.", jsonFilePath);
            }

            string jsonContent = File.ReadAllText(jsonFilePath, Encoding.UTF8);
            JavaScriptSerializer serializer = new JavaScriptSerializer();
            PlanimeterPayload data = serializer.Deserialize<PlanimeterPayload>(jsonContent);

            if (data == null || data.geometry == null || data.geometry.cad_vertices == null)
            {
                throw new InvalidDataException("Invalid Planimeter JSON format: Missing geometry data.");
            }

            Database db = doc.Database;
            Editor ed = doc.Editor;

            double cadArea = 0.0;
            double cadPerim = 0.0;
            string handleStr = "";

            using (DocumentLock docLock = doc.LockDocument())
            {
                using (Transaction tr = db.TransactionManager.StartTransaction())
                {
                    // 1. Ensure Layers Exist
                    string boundaryLayerName = string.IsNullOrEmpty(data.autocad_settings?.boundary_layer) 
                        ? "IMAGE_AREA_BOUNDARY" : data.autocad_settings.boundary_layer;
                    string labelLayerName = string.IsNullOrEmpty(data.autocad_settings?.label_layer) 
                        ? "IMAGE_AREA_LABEL" : data.autocad_settings.label_layer;

                    short boundaryColor = data.autocad_settings != null ? data.autocad_settings.boundary_color_index : (short)4; // Cyan
                    short labelColor = data.autocad_settings != null ? data.autocad_settings.label_color_index : (short)2;       // Yellow

                    EnsureLayer(db, tr, boundaryLayerName, boundaryColor);
                    EnsureLayer(db, tr, labelLayerName, labelColor);

                    // 2. Open BlockTable & ModelSpace
                    BlockTable bt = tr.GetObject(db.BlockTableId, OpenMode.ForRead) as BlockTable;
                    BlockTableRecord btr = tr.GetObject(bt[BlockTableRecord.ModelSpace], OpenMode.ForWrite) as BlockTableRecord;

                    // 3. Create Lightweight Polyline
                    Polyline pline = new Polyline();
                    pline.SetDatabaseDefaults();
                    pline.Layer = boundaryLayerName;

                    int vertexIdx = 0;
                    foreach (var pt in data.geometry.cad_vertices)
                    {
                        pline.AddVertexAt(vertexIdx, new Point2d(pt.x, pt.y), 0, 0, 0);
                        vertexIdx++;
                    }

                    pline.Closed = data.autocad_settings != null ? data.autocad_settings.create_closed_polyline : true;

                    ObjectId plineId = btr.AppendEntity(pline);
                    tr.AddNewlyCreatedDBObject(pline, true);

                    // 4. Query Native AutoCAD Geometry Engine Values
                    cadArea = pline.Area;
                    cadPerim = pline.Length;
                    handleStr = pline.Handle.ToString();

                    // 5. Annotate Centroid with MText
                    if (data.autocad_settings == null || data.autocad_settings.annotate_area)
                    {
                        MText mtext = new MText();
                        mtext.SetDatabaseDefaults();
                        mtext.Layer = labelLayerName;

                        double cx = data.geometry.centroid_cad != null ? data.geometry.centroid_cad.x : 0.0;
                        double cy = data.geometry.centroid_cad != null ? data.geometry.centroid_cad.y : 0.0;
                        mtext.Location = new Point3d(cx, cy, 0);
                        mtext.TextHeight = Math.Max(0.5, data.autocad_settings != null ? data.autocad_settings.text_height : 1.0);
                        mtext.Attachment = AttachmentPoint.MiddleCenter;

                        string unitStr = string.IsNullOrEmpty(data.calibration?.unit) ? "m" : data.calibration.unit;
                        mtext.Contents = string.Format("AREA: {0:F4} {1}²\\PPERIMETER: {2:F4} {1}", cadArea, unitStr, cadPerim);

                        btr.AppendEntity(mtext);
                        tr.AddNewlyCreatedDBObject(mtext, true);
                    }

                    tr.Commit();
                }
            }

            // 6. Zoom Extents / Zoom Window to Geometry
            if (data.autocad_settings == null || data.autocad_settings.auto_zoom)
            {
                try
                {
                    ed.Command("_.ZOOM", "_E");
                }
                catch
                {
                    // Fallback for non-interactive mode
                }
            }

            // 7. Assemble Verification Response
            double appArea = data.geometry.area;
            double absDiff = Math.Abs(appArea - cadArea);
            double pctError = cadArea > 0 ? (absDiff / cadArea) * 100.0 : 0.0;

            VerificationResponse resp = new VerificationResponse
            {
                application = "AutoCAD Planimeter Plugin",
                timestamp = DateTime.Now.ToString("o"),
                status = "SUCCESS",
                app_calculated_area = appArea,
                autocad_polyline_area = cadArea,
                absolute_difference = absDiff,
                percentage_error = pctError,
                autocad_perimeter = cadPerim,
                unit = data.calibration != null ? data.calibration.unit : "m",
                vertex_count = data.geometry.vertex_count,
                boundary_handle = handleStr
            };

            // Write verification JSON next to input JSON
            string respPath = Path.Combine(Path.GetDirectoryName(jsonFilePath), "autocad_verification_result.json");
            File.WriteAllText(respPath, serializer.Serialize(resp), Encoding.UTF8);

            return resp;
        }

        private static void EnsureLayer(Database db, Transaction tr, string layerName, short colorIndex)
        {
            LayerTable lt = tr.GetObject(db.LayerTableId, OpenMode.ForRead) as LayerTable;
            if (!lt.Has(layerName))
            {
                lt.UpgradeOpen();
                LayerTableRecord ltr = new LayerTableRecord();
                ltr.Name = layerName;
                ltr.Color = Color.FromColorIndex(ColorMethod.ByAci, colorIndex);
                lt.Add(ltr);
                tr.AddNewlyCreatedDBObject(ltr, true);
            }
        }
    }
}
