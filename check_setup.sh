#!/bin/bash
# GENMO Setup Checker
# Validates that all required model files are present

set -e

CHECKPOINT_DIR="/workspace/GENMO/inputs/checkpoints"
BODY_MODEL_DIR="${CHECKPOINT_DIR}/body_models"

echo "========================================"
echo "GENMO Model Files Setup Checker"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} Found: $description"
        echo "  Location: $file"
        return 0
    else
        echo -e "${RED}✗${NC} Missing: $description"
        echo "  Expected at: $file"
        return 1
    fi
}

missing_count=0

echo "Checking SMPL Body Models..."
echo "----------------------------"

# Check for SMPL models (multiple naming conventions)
smpl_found=false
for name in "SMPL_NEUTRAL.pkl" "basicModel_neutral_lbs_10_207_0_v1.0.0.pkl" "SMPL_MALE.pkl" "SMPL_FEMALE.pkl"; do
    if [ -f "${BODY_MODEL_DIR}/${name}" ]; then
        echo -e "${GREEN}✓${NC} Found: ${name}"
        smpl_found=true
    fi
done

if [ "$smpl_found" = false ]; then
    echo -e "${RED}✗${NC} No SMPL model files found"
    echo ""
    echo "  Download from: https://smpl.is.tue.mpg.de/download.php"
    echo "  Required: SMPL for Python (v1.0.0)"
    echo ""
    echo "  After downloading, place files in:"
    echo "  ${BODY_MODEL_DIR}/"
    echo ""
    ((missing_count++))
fi

echo ""
echo "Checking SMPL Conversion Files..."
echo "---------------------------------"

check_file "${BODY_MODEL_DIR}/smplx2smpl_sparse.pt" "SMPL-X to SMPL conversion matrix" || ((missing_count++))
check_file "${BODY_MODEL_DIR}/smpl_neutral_J_regressor.pt" "SMPL joint regressor" || ((missing_count++))

echo ""
echo "Checking GENMO Model Weights..."
echo "-------------------------------"

check_file "${CHECKPOINT_DIR}/genmo/model.ckpt" "GENMO pretrained model" || {
    echo -e "${YELLOW}Note:${NC} GENMO weights may not be publicly released yet"
    echo "  Check: https://research.nvidia.com/labs/dair/genmo/"
    ((missing_count++))
}

echo ""
echo "========================================"

if [ $missing_count -eq 0 ]; then
    echo -e "${GREEN}✓ All required files found!${NC}"
    echo ""
    echo "You're ready to run GENMO!"
    echo ""
    echo "Start the web app with:"
    echo "  cd /workspace/GENMO/webapp"
    echo "  python app.py"
    exit 0
else
    echo -e "${RED}✗ Missing $missing_count required file(s)${NC}"
    echo ""
    echo "Setup Instructions:"
    echo ""
    echo "1. SMPL Body Models (register & download):"
    echo "   https://smpl.is.tue.mpg.de/download.php"
    echo ""
    echo "2. Upload to Vast.ai instance:"
    echo "   scp -P <port> SMPL_*.pkl root@<host>:${BODY_MODEL_DIR}/"
    echo ""
    echo "3. GENMO weights (coming soon from NVIDIA):"
    echo "   Check project page for release"
    echo ""
    exit 1
fi
