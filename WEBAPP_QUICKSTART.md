# GENMO Video-to-3D Web App - Quick Start Guide

## For Vast.ai Users

### Step 1: Get Your API Key

1. Go to https://console.vast.ai/account/
2. Copy your API key
3. Add credits to your account (minimum $10 recommended)

### Step 2: Deploy GENMO

```bash
# Clone this repository (if not already done)
git clone https://github.com/NVlabs/GENMO.git
cd GENMO

# Set your API key
export VASTAI_API_KEY="your_key_here"

# Deploy automatically
python deploy_vastai.py --auto
```

**This will**:
- Search for the cheapest GPU instance (typically $0.20-0.50/hour)
- Deploy GENMO web app
- Provide you with a web URL

### Step 3: Access the Web Interface

After deployment completes, you'll see:

```
🎉 DEPLOYMENT SUCCESSFUL!
🌐 Web Interface: http://123.45.67.89:5000
```

Open that URL in your browser!

### Step 4: Upload and Process Video

1. **Drag and drop** your video file (or click to browse)
2. **Select export formats** (OBJ and FBX are recommended)
3. **Click "Upload and Process"**
4. **Wait** 2-5 minutes for processing
5. **Download** your 3D files!

### Step 5: Stop Instance (Important!)

When finished, **stop the instance to avoid charges**:

```bash
python deploy_vastai.py --stop <instance_id>
```

Or via web: https://console.vast.ai/instances/

---

## Cost Estimate

| Video Length | Processing Time | Cost (RTX 4090 @ $0.40/hr) |
|--------------|-----------------|----------------------------|
| 10 seconds   | ~3 minutes      | $0.02                      |
| 30 seconds   | ~5 minutes      | $0.03                      |
| 1 minute     | ~8 minutes      | $0.05                      |
| 5 minutes    | ~20 minutes     | $0.13                      |

**Tip**: Process multiple videos in one session to maximize efficiency!

---

## Importing to Maya/Blender

### Maya

**Method 1: FBX Import**
```
File → Import → FBX
Select: animation.fbx
```

**Method 2: OBJ Sequence**
```
File → Import → OBJ
Select all frame_*.obj files
Use blend shapes for animation
```

### Blender

**Method 1: FBX Import**
```
File → Import → FBX
Select: animation.fbx
```

**Method 2: Use Import Script**
```
In Blender Python Console:
exec(open("import_to_blender.py").read())
```

**Method 3: USD Import** (Blender 3.0+)
```
File → Import → USD
Select: animation.usdc
```

---

## Troubleshooting

### "No GPU detected"
- You deployed to Vast.ai correctly - check the instance logs
- Restart the instance if needed

### "Model checkpoints not found"
- First-time setup requires downloading SMPL models
- See full README for instructions

### "Upload failed"
- Check video format (MP4, MOV, AVI, MKV supported)
- Ensure file is under 500MB
- Try a shorter video clip

### "Processing stuck"
- Check the progress bar - some steps take longer
- Video length affects processing time
- If stuck >10 minutes, refresh page and try again

---

## Advanced Options

### Custom Search

Search for specific GPU:
```bash
python deploy_vastai.py --gpu "RTX 4090" --max-price 0.60
```

### List Active Instances

```bash
python deploy_vastai.py --list
```

### Manual Selection

For manual instance selection (no --auto):
```bash
python deploy_vastai.py --min-gpu-ram 24 --max-price 0.50
```

Then select from the displayed options.

---

## Tips for Best Results

### Video Quality
- **Lighting**: Good, even lighting works best
- **Background**: Simple backgrounds help tracking
- **Subject**: Clear visibility of the person
- **Movement**: Natural, continuous motion
- **Duration**: 5-30 seconds optimal

### What Works Best
✅ Dancing videos
✅ Sports activities
✅ Walking/running
✅ Exercise movements
✅ Performance arts

### What Might Not Work Well
❌ Very dark videos
❌ Heavy occlusions
❌ Multiple overlapping people
❌ Very fast/blurry motion
❌ Extreme camera angles

---

## FAQ

**Q: Do I need to install anything?**
A: Just Python 3 and the `requests` library for deployment. Everything else runs on Vast.ai.

**Q: How long does processing take?**
A: Typically 2-5 minutes for a 30-second video. Scales with video length.

**Q: Can I process multiple videos?**
A: Yes! Keep the instance running and process as many as you need, then stop it.

**Q: What video formats are supported?**
A: MP4, MOV, AVI, MKV

**Q: What's the maximum video length?**
A: Depends on GPU memory. 24GB VRAM typically handles 5+ minutes.

**Q: Can I use this commercially?**
A: Check GENMO and SMPL licenses. Currently designed for research/academic use.

**Q: Is my video data private?**
A: Videos are processed on your rented Vast.ai instance. Not stored permanently unless you save them.

---

## Next Steps

- Read the full README: `webapp/README.md`
- Check GENMO documentation: https://research.nvidia.com/labs/dair/genmo/
- Learn about Vast.ai: https://vast.ai/docs/

## Support

- GENMO: https://github.com/NVlabs/GENMO
- Vast.ai: https://vast.ai/faq
- Issues: Create an issue in the repository

---

**Happy motion capturing! 🎬 → 🎭**
