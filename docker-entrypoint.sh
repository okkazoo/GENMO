#!/bin/bash
set -e

echo "========================================="
echo "GENMO Video-to-3D Web Application"
echo "========================================="

# Check if CUDA is available
if command -v nvidia-smi &> /dev/null; then
    echo "✓ GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "⚠ WARNING: No GPU detected! GENMO requires a CUDA-capable GPU."
fi

# Check if model checkpoints exist
CHECKPOINT_DIR="/workspace/GENMO/inputs/checkpoints"
if [ ! -d "$CHECKPOINT_DIR/body_models" ]; then
    echo ""
    echo "⚠ WARNING: SMPL body models not found at $CHECKPOINT_DIR/body_models"
    echo "Please download the required files:"
    echo "  1. SMPL models from https://smpl.is.tue.mpg.de/"
    echo "  2. Place them in: $CHECKPOINT_DIR/body_models/"
    echo ""
fi

# Download models if not present (optional - would need credentials)
# This section could be expanded to auto-download from authorized sources

echo ""
echo "Starting GENMO web server..."
echo "Access the application at: http://0.0.0.0:5000"
echo ""

# Start the Flask web application
cd /workspace/GENMO/webapp
python3 app.py --host 0.0.0.0 --port 5000
