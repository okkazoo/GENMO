# SMPL Model Setup for Windows
# PowerShell script to extract and organize SMPL models

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SMPL Model Setup for GENMO (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find Downloads folder
$DownloadsDir = "$env:USERPROFILE\Downloads"

if (-not (Test-Path $DownloadsDir)) {
    Write-Host "Downloads folder not found at: $DownloadsDir" -ForegroundColor Red
    $DownloadsDir = Read-Host "Enter path to your Downloads folder"
}

Write-Host "Looking for SMPL files in: $DownloadsDir" -ForegroundColor Yellow
Write-Host ""

# Create output directory
$OutputDir = "$env:USERPROFILE\GENMO_SMPL_Models"
New-Item -ItemType Directory -Force -Path "$OutputDir\models" | Out-Null

Write-Host "Will organize files in: $OutputDir" -ForegroundColor Yellow
Write-Host ""

# Find zip files
Write-Host "Searching for SMPL zip files..." -ForegroundColor Cyan
$ZipFiles = Get-ChildItem -Path $DownloadsDir -Filter "*.zip" | Where-Object { $_.Name -like "*SMPL*" -or $_.Name -like "*smpl*" }

if ($ZipFiles.Count -eq 0) {
    Write-Host "No SMPL zip files found in $DownloadsDir" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please make sure you've downloaded:" -ForegroundColor Yellow
    Write-Host "  - SMPL for Python v1.1.0"
    Write-Host "  - SMPL for Python v1.0.0 (optional)"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Extract zip files
foreach ($ZipFile in $ZipFiles) {
    Write-Host "Found: $($ZipFile.Name)" -ForegroundColor Green

    $ExtractPath = "$OutputDir\extracted_$($ZipFile.BaseName)"

    Write-Host "  -> Extracting to $ExtractPath..." -ForegroundColor Gray

    Expand-Archive -Path $ZipFile.FullName -DestinationPath $ExtractPath -Force
}

Write-Host ""
Write-Host "Extracted $($ZipFiles.Count) archive(s)" -ForegroundColor Green
Write-Host ""

# Find and copy PKL files
Write-Host "Looking for SMPL .pkl model files..." -ForegroundColor Cyan
Write-Host ""

$PklFiles = Get-ChildItem -Path "$OutputDir\extracted_*" -Filter "*.pkl" -Recurse

foreach ($PklFile in $PklFiles) {
    Write-Host "Found: $($PklFile.Name)" -ForegroundColor Green
    Copy-Item -Path $PklFile.FullName -Destination "$OutputDir\models\" -Force
}

Write-Host ""
Write-Host "Renaming files for GENMO compatibility..." -ForegroundColor Cyan

# Rename to GENMO-expected names
$ModelsDir = "$OutputDir\models"
$AllPkls = Get-ChildItem -Path $ModelsDir -Filter "*.pkl"

foreach ($PklFile in $AllPkls) {
    $Name = $PklFile.Name

    # Neutral model
    if ($Name -like "*neutral*" -or $Name -like "*NEUTRAL*") {
        Copy-Item -Path $PklFile.FullName -Destination "$ModelsDir\SMPL_NEUTRAL.pkl" -Force
        Write-Host "  ✓ Created SMPL_NEUTRAL.pkl" -ForegroundColor Green
    }

    # Female model
    if ($Name -like "*female*" -or $Name -like "*_f_*") {
        Copy-Item -Path $PklFile.FullName -Destination "$ModelsDir\SMPL_FEMALE.pkl" -Force
        Write-Host "  ✓ Created SMPL_FEMALE.pkl" -ForegroundColor Green
    }

    # Male model (but not female)
    if (($Name -like "*male*" -or $Name -like "*_m_*") -and $Name -notlike "*female*") {
        Copy-Item -Path $PklFile.FullName -Destination "$ModelsDir\SMPL_MALE.pkl" -Force
        Write-Host "  ✓ Created SMPL_MALE.pkl" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Model files ready at:" -ForegroundColor Yellow
Write-Host "  $ModelsDir\" -ForegroundColor White
Write-Host ""

Get-ChildItem -Path $ModelsDir -Filter "*.pkl" | Format-Table Name, @{Label="Size (MB)"; Expression={[math]::Round($_.Length/1MB, 2)}}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Deploy to Vast.ai:" -ForegroundColor Yellow
Write-Host "   `$env:VASTAI_API_KEY = 'your_api_key'" -ForegroundColor White
Write-Host "   python deploy_vastai.py --auto" -ForegroundColor White
Write-Host ""
Write-Host "2. Upload models to Vast.ai instance:" -ForegroundColor Yellow
Write-Host "   Use WinSCP or scp from Git Bash/WSL" -ForegroundColor White
Write-Host ""
Write-Host "Files to upload:" -ForegroundColor Yellow
Write-Host "   From: $ModelsDir\*.pkl" -ForegroundColor White
Write-Host "   To: /workspace/GENMO/inputs/checkpoints/body_models/" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
