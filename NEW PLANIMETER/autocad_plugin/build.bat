@echo off
setlocal enabledelayedexpansion
echo ========================================================
echo   Building New Planimeter AutoCAD .NET Plugin
echo ========================================================

:: Check for standard AutoCAD installation paths
set ACAD_PATH=
if exist "C:\Program Files\Autodesk\AutoCAD 2026\accoremgd.dll" set ACAD_PATH=C:\Program Files\Autodesk\AutoCAD 2026
if exist "C:\Program Files\Autodesk\AutoCAD 2025\accoremgd.dll" set ACAD_PATH=C:\Program Files\Autodesk\AutoCAD 2025
if exist "C:\Program Files\Autodesk\AutoCAD 2024\accoremgd.dll" set ACAD_PATH=C:\Program Files\Autodesk\AutoCAD 2024
if exist "C:\Program Files\Autodesk\AutoCAD 2023\accoremgd.dll" set ACAD_PATH=C:\Program Files\Autodesk\AutoCAD 2023
if exist "C:\Program Files\Autodesk\AutoCAD 2022\accoremgd.dll" set ACAD_PATH=C:\Program Files\Autodesk\AutoCAD 2022
if exist "C:\Program Files\Autodesk\AutoCAD 2021\accoremgd.dll" set ACAD_PATH=C:\Program Files\Autodesk\AutoCAD 2021

if "%ACAD_PATH%"=="" (
    echo [INFO] No standard AutoCAD installation detected in Program Files.
    echo [INFO] Plugin source code is ready. To compile when AutoCAD is installed:
    echo        MSBuild PlanimeterPlugin.csproj /p:AutoCADPath="C:\Program Files\Autodesk\AutoCAD [Year]"
) else (
    echo [INFO] Detected AutoCAD at: %ACAD_PATH%
    echo Compiling with MSBuild / csc...
    C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /target:library /out:bin\Release\NewPlanimeterPlugin.dll /r:"%ACAD_PATH%\accoremgd.dll","%ACAD_PATH%\acdbmgd.dll","%ACAD_PATH%\acmgd.dll",System.Web.Extensions.dll JsonDataModel.cs PolylineImporter.cs PlanimeterCommands.cs
)

echo Build script finished.
