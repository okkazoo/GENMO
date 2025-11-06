# GENMO Video-to-3D Complete Setup Guide

## Step-by-Step Setup with Vast.ai

Follow these steps in order to get GENMO running on Vast.ai:

---

## 📦 Step 1: Extract SMPL Models (On Your Local Computer)

You've already downloaded the SMPL zip files to your Downloads folder. Now extract them:

### Option A: Automatic (Recommended)

```bash
# Navigate to GENMO directory on your local machine
cd /path/to/GENMO

# Run the setup script
./setup_smpl_local.sh
```

This will:
- Find SMPL zip files in your Downloads folder
- Extract all .pkl model files
- Rename them for GENMO compatibility
- Organize them in `~/GENMO_SMPL_Models/models/`

### Option B: Manual Extraction

```bash
# Create directory for models
mkdir -p ~/GENMO_SMPL_Models/models

# Go to Downloads
cd ~/Downloads

# Extract each zip file
unzip "SMPL_python_v.1.1.0.zip" -d ~/GENMO_SMPL_Models/extracted_v1.1
unzip "SMPL_python_v.1.0.0.zip" -d ~/GENMO_SMPL_Models/extracted_v1.0

# Find and copy the .pkl files
find ~/GENMO_SMPL_Models/extracted_* -name "*.pkl" -exec cp {} ~/GENMO_SMPL_Models/models/ \;

# Rename for GENMO
cd ~/GENMO_SMPL_Models/models/
cp basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl SMPL_NEUTRAL.pkl
cp basicmodel_f_lbs_10_207_0_v1.1.0.pkl SMPL_FEMALE.pkl
cp basicmodel_m_lbs_10_207_0_v1.1.0.pkl SMPL_MALE.pkl
```

### Verify

```bash
ls -lh ~/GENMO_SMPL_Models/models/

# Should show:
# SMPL_NEUTRAL.pkl
# SMPL_FEMALE.pkl
# SMPL_MALE.pkl
# (plus original files)
```

---

## 🚀 Step 2: Deploy to Vast.ai

Now deploy GENMO to a GPU instance:

```bash
# Set your Vast.ai API key
export VASTAI_API_KEY="your_api_key_here"

# Deploy (automatic selection of cheapest GPU)
python deploy_vastai.py --auto

# Or search manually
python deploy_vastai.py --min-gpu-ram 16 --max-price 0.50 --gpu "RTX 4090"
```

**Save the output!** You'll need:
- Instance ID
- SSH Host
- SSH Port
- Web URL

Example output:
```
🎉 DEPLOYMENT SUCCESSFUL!
📊 Instance ID: 1234567
🌐 Web Interface: http://ssh4.vast.ai:5000
🔐 SSH Access: ssh -p 12345 root@ssh4.vast.ai
```

---

## 📤 Step 3: Upload SMPL Models to Vast.ai

### Option A: Automatic (Recommended)

```bash
# Run the upload script
./upload_to_vastai.sh
```

It will ask for:
- SSH Host (e.g., `ssh4.vast.ai`)
- SSH Port (e.g., `12345`)

Then automatically:
- Test connection
- Create directories
- Upload all SMPL models
- Verify setup

### Option B: Manual Upload

```bash
# Upload models
scp -P <SSH_PORT> ~/GENMO_SMPL_Models/models/*.pkl \
  root@<SSH_HOST>:/workspace/GENMO/inputs/checkpoints/body_models/

# Verify
ssh -p <SSH_PORT> root@<SSH_HOST> "cd /workspace/GENMO && ./check_setup.sh"
```

---

## 🎬 Step 4: Start Using GENMO!

### Access the Web Interface

Open in your browser:
```
http://<SSH_HOST>:5000
```

For example: `http://ssh4.vast.ai:5000`

### Upload Your First Video

1. **Drag and drop** a video file (MP4, MOV, etc.)
2. **Select formats**: OBJ + FBX recommended
3. **Click "Upload and Process"**
4. **Wait** 3-5 minutes for processing
5. **Download** your 3D animation files!

### Import to Maya/Blender

**Maya:**
```
File → Import → FBX
Select: animation.fbx
```

**Blender:**
```
File → Import → FBX (.fbx)
Select: animation.fbx
```

---

## 🛠️ Troubleshooting

### Connection Issues

```bash
# Test SSH connection
ssh -p <PORT> root@<HOST> "echo 'Connected!'"

# If fails, check:
# 1. Instance is running (Vast.ai console)
# 2. Port/host are correct
# 3. Firewall not blocking
```

### Upload Fails

```bash
# Check if models exist locally
ls -lh ~/GENMO_SMPL_Models/models/

# Try manual upload with verbose output
scp -v -P <PORT> ~/GENMO_SMPL_Models/models/*.pkl \
  root@<HOST>:/workspace/GENMO/inputs/checkpoints/body_models/
```

### Web App Not Accessible

```bash
# SSH into instance
ssh -p <PORT> root@<HOST>

# Check if web app is running
ps aux | grep app.py

# Check logs
cd /workspace/GENMO/webapp
python app.py --host 0.0.0.0 --port 5000

# Or restart container
docker restart $(docker ps -q)
```

### SMPL Files Not Found Error

```bash
# SSH into instance
ssh -p <PORT> root@<HOST>

# Run setup checker
cd /workspace/GENMO
./check_setup.sh

# Manually check files
ls -lh /workspace/GENMO/inputs/checkpoints/body_models/
```

---

## 💰 Managing Costs

### Stop Instance When Not Using

```bash
# List active instances
python deploy_vastai.py --list

# Stop instance
python deploy_vastai.py --stop <INSTANCE_ID>
```

**Important:** Always stop when finished to avoid charges!

### Cost Monitoring

- Check Vast.ai console: https://console.vast.ai/instances/
- Typical cost: $0.02-0.05 per 30-second video
- RTX 4090: ~$0.40/hour

---

## 📋 Complete Command Reference

### Local Setup
```bash
# 1. Extract SMPL models
./setup_smpl_local.sh

# 2. Verify extraction
ls ~/GENMO_SMPL_Models/models/
```

### Vast.ai Deployment
```bash
# 1. Set API key
export VASTAI_API_KEY="your_key"

# 2. Deploy
python deploy_vastai.py --auto

# 3. Upload models
./upload_to_vastai.sh

# 4. List instances
python deploy_vastai.py --list

# 5. Stop instance
python deploy_vastai.py --stop <ID>
```

### SSH Commands
```bash
# Connect to instance
ssh -p <PORT> root@<HOST>

# Upload files
scp -P <PORT> file.mp4 root@<HOST>:/workspace/

# Download results
scp -P <PORT> root@<HOST>:/workspace/GENMO/webapp/outputs/<job_id>/animation.fbx ./
```

---

## 🎯 Quick Reference

| Step | Command | Time |
|------|---------|------|
| 1. Extract SMPL | `./setup_smpl_local.sh` | 1 min |
| 2. Deploy Vast.ai | `python deploy_vastai.py --auto` | 2-5 min |
| 3. Upload Models | `./upload_to_vastai.sh` | 1 min |
| 4. Process Video | Via web interface | 3-5 min |
| 5. Stop Instance | `python deploy_vastai.py --stop <ID>` | Instant |

**Total setup time:** ~5-10 minutes (first time only)
**Per-video processing:** 3-5 minutes

---

## 📞 Getting Help

- **GENMO Issues:** https://github.com/NVlabs/GENMO/issues
- **Vast.ai Support:** https://vast.ai/faq
- **Setup Script Issues:** Check logs with `bash -x script.sh`

---

## ✅ Checklist

Before processing your first video, verify:

- [ ] SMPL models downloaded from https://smpl.is.tue.mpg.de/
- [ ] Models extracted with `setup_smpl_local.sh`
- [ ] Vast.ai API key configured
- [ ] Instance deployed successfully
- [ ] SMPL models uploaded to instance
- [ ] `check_setup.sh` passes on instance
- [ ] Web interface accessible

Once all checked, you're ready to go! 🚀

---

## 🎬 Example Workflow

```bash
# === FIRST TIME SETUP (10 minutes) ===

# 1. Extract SMPL models
./setup_smpl_local.sh

# 2. Deploy to Vast.ai
export VASTAI_API_KEY="your_key"
python deploy_vastai.py --auto
# Save the SSH host and port!

# 3. Upload models
./upload_to_vastai.sh
# Enter host: ssh4.vast.ai
# Enter port: 12345

# === EVERY TIME YOU WANT TO PROCESS VIDEOS ===

# 4. Open web browser
# Go to: http://ssh4.vast.ai:5000

# 5. Upload video, select OBJ + FBX, process

# 6. Download your 3D files

# 7. Stop instance when done
python deploy_vastai.py --stop 1234567

# === DONE! ===
```

**Your first video processing costs less than $0.05!** 🎉
