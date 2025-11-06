#!/bin/bash
# Upload SMPL Models to Vast.ai Instance
# Run this AFTER deploying with deploy_vastai.py

set -e

echo "========================================"
echo "Upload SMPL Models to Vast.ai"
echo "========================================"
echo ""

# Check if models directory exists
MODELS_DIR="$HOME/GENMO_SMPL_Models/models"

if [ ! -d "$MODELS_DIR" ]; then
    echo "❌ SMPL models directory not found!"
    echo ""
    echo "Please run setup_smpl_local.sh first to extract SMPL models"
    echo ""
    exit 1
fi

# Check for pkl files
PKL_COUNT=$(find "$MODELS_DIR" -name "*.pkl" | wc -l)

if [ $PKL_COUNT -eq 0 ]; then
    echo "❌ No .pkl files found in $MODELS_DIR"
    echo ""
    echo "Please run setup_smpl_local.sh first"
    exit 1
fi

echo "Found $PKL_COUNT SMPL model file(s)"
echo ""

# Get Vast.ai instance details
echo "Enter your Vast.ai instance details:"
echo "(You can find these after running deploy_vastai.py)"
echo ""

read -p "SSH Host (e.g., ssh4.vast.ai): " SSH_HOST
read -p "SSH Port (e.g., 12345): " SSH_PORT

echo ""
echo "Testing connection to $SSH_HOST:$SSH_PORT..."

if ! ssh -p "$SSH_PORT" -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@"$SSH_HOST" "echo 'Connection successful'" 2>/dev/null; then
    echo "❌ Cannot connect to Vast.ai instance"
    echo ""
    echo "Please check:"
    echo "  1. Instance is running (check Vast.ai console)"
    echo "  2. Host and port are correct"
    echo "  3. SSH keys are configured"
    echo ""
    exit 1
fi

echo "✓ Connection successful"
echo ""

# Create remote directory
echo "Creating remote directory..."
ssh -p "$SSH_PORT" root@"$SSH_HOST" "mkdir -p /workspace/GENMO/inputs/checkpoints/body_models"

# Upload files
echo ""
echo "Uploading SMPL model files..."
echo ""

scp -P "$SSH_PORT" "$MODELS_DIR"/*.pkl root@"$SSH_HOST":/workspace/GENMO/inputs/checkpoints/body_models/

echo ""
echo "✓ Upload complete!"
echo ""

# Verify uploaded files
echo "Verifying uploaded files..."
echo ""

ssh -p "$SSH_PORT" root@"$SSH_HOST" "ls -lh /workspace/GENMO/inputs/checkpoints/body_models/"

echo ""
echo "Running setup checker on remote instance..."
echo ""

ssh -p "$SSH_PORT" root@"$SSH_HOST" "cd /workspace/GENMO && ./check_setup.sh"

echo ""
echo "========================================"
echo "✓ All Done!"
echo "========================================"
echo ""
echo "Your Vast.ai instance is ready to use!"
echo ""
echo "Access the web app at:"
echo "  http://$SSH_HOST:5000"
echo ""
echo "Or SSH into the instance:"
echo "  ssh -p $SSH_PORT root@$SSH_HOST"
echo ""
