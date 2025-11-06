# GENMO Video-to-3D Web Application

A web-based interface for converting videos to 3D human animations using GENMO, with export to Maya/Blender formats.

## Features

- **Easy Video Upload**: Drag-and-drop interface for video files
- **AI-Powered Motion Extraction**: Uses GENMO to extract 3D human motion from video
- **Multiple Export Formats**:
  - OBJ sequence (universal)
  - FBX (Maya/Blender standard)
  - USD (modern VFX pipeline)
  - Alembic (animation cache)
- **Preview Rendering**: See your 3D motion before downloading
- **Remote GPU Support**: Optimized for Vast.ai deployment

## Quick Start

### Option 1: Deploy to Vast.ai (Recommended)

Since GENMO requires a GPU, deploying to Vast.ai is the easiest option:

```bash
# Set your Vast.ai API key
export VASTAI_API_KEY="your_api_key_here"

# Deploy automatically (selects cheapest GPU)
python deploy_vastai.py --auto

# Or search and select manually
python deploy_vastai.py --min-gpu-ram 16 --max-price 0.50
```

The script will:
1. Search for available GPU instances
2. Deploy the GENMO web app
3. Provide you with the web interface URL

**Access the app at**: `http://<instance-ip>:5000`

### Option 2: Run Locally (Requires GPU)

If you have a local CUDA-capable GPU:

```bash
# Install dependencies
pip install -r requirements.txt
pip install flask werkzeug trimesh usd-core

# Download SMPL models (required)
# Place in: inputs/checkpoints/body_models/

# Start the web server
cd webapp
python app.py --host 0.0.0.0 --port 5000
```

Access at: `http://localhost:5000`

### Option 3: Docker

```bash
# Build Docker image
docker build -t genmo-webapp .

# Run container (requires nvidia-docker)
docker run --gpus all -p 5000:5000 -v $(pwd)/inputs:/workspace/GENMO/inputs genmo-webapp
```

## Prerequisites

### Required Files

You need to download SMPL body models (free for research):

1. Visit https://smpl.is.tue.mpg.de/
2. Register and download SMPL models
3. Place files in `inputs/checkpoints/body_models/`:
   - `SMPL_NEUTRAL.pkl`
   - `smplx2smpl_sparse.pt`
   - `smpl_neutral_J_regressor.pt`

### GENMO Model Weights

Download GENMO pretrained weights:
- Coming soon from official NVIDIA GENMO repository
- Place in `inputs/checkpoints/genmo/`

## Usage Guide

### 1. Upload Video

- Drag and drop a video file (MP4, MOV, AVI, MKV)
- Or click to browse and select
- Maximum file size: 500MB

### 2. Select Export Formats

Choose which 3D formats you want:
- **OBJ Sequence**: One .obj file per frame (universal compatibility)
- **FBX**: Single animated file (best for Maya/Blender)
- **USD**: Modern format for VFX pipelines
- **Alembic**: Animation cache format

### 3. Process

Click "Upload and Process" and wait:
1. Video uploads (5-10 seconds)
2. GENMO processes motion (1-3 minutes depending on video length)
3. 3D files are exported (30 seconds - 1 minute)

### 4. Download Results

- **Preview Video**: See the extracted 3D motion
- **3D Files**: Download your selected formats
- Import into Maya/Blender using the provided scripts

## Importing to Maya/Blender

### Maya Import

Use the generated MEL script:

```mel
// In Maya Script Editor
source "import_to_maya.mel";
```

Or manually:
1. File → Import → Select OBJ sequence
2. Use the blendShape method for animation

### Blender Import

Use the generated Python script:

```python
# In Blender Python Console
exec(open("import_to_blender.py").read())
```

Or use the FBX:
1. File → Import → FBX
2. Select `animation.fbx`

## API Reference

### Upload Video

```bash
POST /api/upload
Content-Type: multipart/form-data

Fields:
  - video: video file
  - formats: comma-separated list (obj,fbx,usd,abc)

Response:
{
  "job_id": "uuid",
  "status": "uploaded",
  "message": "Processing started"
}
```

### Check Status

```bash
GET /api/status/<job_id>

Response:
{
  "job_id": "uuid",
  "status": "processing|completed|error",
  "progress": 0-100,
  "message": "Current step",
  "results": {
    "preview_video": "path",
    "exported_files": [...]
  }
}
```

### Download File

```bash
GET /api/download/<job_id>/<filename>
```

### Preview Video

```bash
GET /api/preview/<job_id>
```

## Vast.ai Management

### List Running Instances

```bash
python deploy_vastai.py --list
```

### Stop Instance

```bash
python deploy_vastai.py --stop <instance_id>
```

**Important**: Always stop instances when done to avoid charges!

### Monitor Costs

Typical costs on Vast.ai:
- RTX 4090: $0.30-0.50/hour
- RTX 3090: $0.20-0.35/hour
- A6000: $0.40-0.60/hour

Processing a 30-second video takes ~5 minutes, costing less than $0.05.

## Troubleshooting

### "No GPU detected" Error

- Make sure you're running on a machine with NVIDIA GPU
- Check CUDA installation: `nvidia-smi`
- On Vast.ai, ensure you selected a GPU instance

### "Model checkpoints not found"

- Download SMPL models (see Prerequisites)
- Place files in correct directory
- Check file permissions

### "Out of memory" Error

- Video is too long - try shorter clips
- Reduce video resolution
- Use a GPU with more VRAM (24GB+ recommended)

### Slow Processing

- Normal for first run (model loading)
- Subsequent runs are faster
- Processing time scales with video length

## Architecture

```
webapp/
├── app.py                      # Flask server
├── templates/
│   └── index.html             # Web interface
├── utils/
│   ├── genmo_inference.py     # GENMO integration
│   └── export_3d.py           # 3D format exporters
├── uploads/                   # Temporary uploads
└── outputs/                   # Processing results
```

## Development

### Running in Debug Mode

```bash
python app.py --debug
```

### Testing Inference

```bash
python utils/genmo_inference.py path/to/video.mp4
```

### Testing Export

```bash
python utils/export_3d.py path/to/smpl_params.pt output_dir
```

## Security Notes

- The web app is designed for personal/research use
- No authentication by default - add if exposing publicly
- File uploads are size-limited to 500MB
- Temporary files are stored locally (clean up with `/api/cleanup`)

## Performance Tips

1. **Video Preparation**:
   - Keep videos short (10-30 seconds optimal)
   - Ensure good lighting and clear subject visibility
   - 720p-1080p resolution is sufficient

2. **GPU Selection**:
   - Minimum 16GB VRAM (RTX 3090/4090 or better)
   - CUDA 12.1+ required
   - More VRAM = longer videos supported

3. **Cost Optimization**:
   - Process multiple videos in one session
   - Stop instance immediately after downloading
   - Use spot instances on Vast.ai for lower prices

## Support

- **GENMO Issues**: https://github.com/NVlabs/GENMO/issues
- **Web App Issues**: Create issue in your fork
- **Vast.ai Support**: https://vast.ai/faq

## License

This web application is provided as-is for research purposes.
- GENMO code: See main repository license
- SMPL models: Requires academic license
- Web app code: MIT License

## Citation

If you use GENMO in your research, please cite:

```bibtex
@inproceedings{genmo2025,
  title     = {GENMO: A GENeralist Model for Human MOtion},
  author    = {Li, Jiefeng and Cao, Jinkun and Zhang, Haotian and Rempe, Davis and Kautz, Jan and Iqbal, Umar and Yuan, Ye},
  booktitle = {ICCV},
  year      = {2025}
}
```

## Roadmap

- [ ] Add batch processing support
- [ ] Implement user authentication
- [ ] Add job queue for multiple users
- [ ] Support for multiple people in video
- [ ] Real-time preview during processing
- [ ] Direct Blender addon integration
- [ ] Cloud storage integration (S3, GCS)

## Contributing

Contributions welcome! Areas for improvement:
- Better error handling
- Additional export formats
- UI/UX enhancements
- Performance optimizations
- Documentation improvements
