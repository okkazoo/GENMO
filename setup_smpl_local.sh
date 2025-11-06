#!/bin/bash
# SMPL Model Extraction and Setup Script
# Run this on your LOCAL machine where you downloaded the SMPL zip files

set -e

echo "========================================"
echo "SMPL Model Setup for GENMO"
echo "========================================"
echo ""

# Find Downloads folder
DOWNLOADS_DIR=""
if [ -d "$HOME/Downloads" ]; then
    DOWNLOADS_DIR="$HOME/Downloads"
elif [ -d "$HOME/downloads" ]; then
    DOWNLOADS_DIR="$HOME/downloads"
else
    echo "Enter path to your Downloads folder:"
    read DOWNLOADS_DIR
fi

echo "Looking for SMPL files in: $DOWNLOADS_DIR"
echo ""

# Create output directory
OUTPUT_DIR="$HOME/GENMO_SMPL_Models"
mkdir -p "$OUTPUT_DIR"

echo "Will organize files in: $OUTPUT_DIR"
echo ""

# Find and extract zip files
echo "Searching for SMPL zip files..."
FOUND_ZIPS=0

cd "$DOWNLOADS_DIR"

for zipfile in *.zip; do
    if [[ -f "$zipfile" ]]; then
        echo "Found: $zipfile"

        # Check if it's SMPL-related
        if [[ "$zipfile" == *"SMPL"* ]] || [[ "$zipfile" == *"smpl"* ]]; then
            echo "  → Extracting $zipfile..."
            unzip -q "$zipfile" -d "$OUTPUT_DIR/extracted_$(basename $zipfile .zip)"
            FOUND_ZIPS=$((FOUND_ZIPS + 1))
        fi
    fi
done

if [ $FOUND_ZIPS -eq 0 ]; then
    echo "❌ No SMPL zip files found in $DOWNLOADS_DIR"
    echo ""
    echo "Please make sure you've downloaded:"
    echo "  - SMPL for Python v1.1.0"
    echo "  - SMPL for Python v1.0.0 (optional)"
    echo ""
    exit 1
fi

echo ""
echo "Extracted $FOUND_ZIPS archive(s)"
echo ""

# Find and copy PKL files
echo "Looking for SMPL .pkl model files..."
echo ""

mkdir -p "$OUTPUT_DIR/models"

# Find all pkl files
find "$OUTPUT_DIR/extracted_"* -name "*.pkl" -type f | while read pkl_file; do
    filename=$(basename "$pkl_file")
    echo "Found: $filename"
    cp "$pkl_file" "$OUTPUT_DIR/models/"
done

echo ""
echo "Renaming files for GENMO compatibility..."

cd "$OUTPUT_DIR/models"

# Rename to GENMO-expected names
for file in *.pkl; do
    if [[ "$file" == *"neutral"* ]] || [[ "$file" == *"NEUTRAL"* ]]; then
        cp "$file" "SMPL_NEUTRAL.pkl"
        echo "  ✓ Created SMPL_NEUTRAL.pkl"
    fi

    if [[ "$file" == *"female"* ]] || [[ "$file" == *"_f_"* ]]; then
        cp "$file" "SMPL_FEMALE.pkl"
        echo "  ✓ Created SMPL_FEMALE.pkl"
    fi

    if [[ "$file" == *"male"* ]] || [[ "$file" == *"_m_"* ]]; then
        if [[ "$file" != *"female"* ]]; then
            cp "$file" "SMPL_MALE.pkl"
            echo "  ✓ Created SMPL_MALE.pkl"
        fi
    fi
done

echo ""
echo "========================================"
echo "✓ Setup Complete!"
echo "========================================"
echo ""
echo "Model files ready at:"
echo "  $OUTPUT_DIR/models/"
echo ""

ls -lh "$OUTPUT_DIR/models/"

echo ""
echo "Next steps:"
echo "1. Deploy to Vast.ai: python deploy_vastai.py --auto"
echo "2. Upload these files to your Vast.ai instance"
echo ""
echo "Upload command (run AFTER deploying to Vast.ai):"
echo "  scp -P <port> $OUTPUT_DIR/models/*.pkl \\"
echo "    root@<host>:/workspace/GENMO/inputs/checkpoints/body_models/"
echo ""
