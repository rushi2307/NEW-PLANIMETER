// ==============================================================================
// New Planimeter AutoCAD .NET Plugin - JSON Data Contracts
// Deserializes plot geometry, calibration parameters, and AutoCAD configuration.
// ==============================================================================

using System;
using System.Collections.Generic;

namespace PlanimeterAutoCADPlugin
{
    [Serializable]
    public class PlanimeterPayload
    {
        public MetadataDto metadata { get; set; }
        public CalibrationDto calibration { get; set; }
        public GeometryDto geometry { get; set; }
        public AutoCADSettingsDto autocad_settings { get; set; }
    }

    [Serializable]
    public class MetadataDto
    {
        public string application { get; set; }
        public string version { get; set; }
        public string export_timestamp { get; set; }
        public string source_image { get; set; }
        public int image_width_px { get; set; }
        public int image_height_px { get; set; }
    }

    [Serializable]
    public class CalibrationDto
    {
        public double scale_factor { get; set; }
        public string unit { get; set; }
        public bool is_calibrated { get; set; }
        public string calibration_type { get; set; }
        public double known_distance { get; set; }
        public double pixel_distance { get; set; }
        public double pixels_per_unit { get; set; }
    }

    [Serializable]
    public class GeometryDto
    {
        public int vertex_count { get; set; }
        public double area { get; set; }
        public string area_unit { get; set; }
        public double perimeter { get; set; }
        public string perimeter_unit { get; set; }
        public PointDto centroid_cad { get; set; }
        public PointDto centroid_px { get; set; }
        public List<PointDto> cad_vertices { get; set; }
        public List<PointDto> image_vertices_px { get; set; }
    }

    [Serializable]
    public class PointDto
    {
        public double x { get; set; }
        public double y { get; set; }
    }

    [Serializable]
    public class AutoCADSettingsDto
    {
        public string boundary_layer { get; set; }
        public short boundary_color_index { get; set; }
        public string label_layer { get; set; }
        public short label_color_index { get; set; }
        public double text_height { get; set; }
        public bool auto_zoom { get; set; }
        public bool create_closed_polyline { get; set; }
        public bool annotate_area { get; set; }
    }

    [Serializable]
    public class VerificationResponse
    {
        public string application { get; set; }
        public string timestamp { get; set; }
        public string status { get; set; }
        public double app_calculated_area { get; set; }
        public double autocad_polyline_area { get; set; }
        public double absolute_difference { get; set; }
        public double percentage_error { get; set; }
        public double autocad_perimeter { get; set; }
        public string unit { get; set; }
        public int vertex_count { get; set; }
        public string boundary_handle { get; set; }
    }
}
