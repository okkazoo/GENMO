# GENMO Video-to-3D Web Application
# Docker image for deployment on Vast.ai or other GPU cloud providers

FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libegl1-mesa \
    libgles2-mesa \
    vim \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace/GENMO

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir torch==2.3.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install GENMO dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Install web app dependencies
RUN pip3 install --no-cache-dir \
    flask==3.0.0 \
    werkzeug==3.0.0 \
    trimesh==4.0.5 \
    usd-core==23.11

# Install PyTorch3D (may take a while)
RUN pip3 install --no-cache-dir \
    "git+https://github.com/facebookresearch/pytorch3d.git@stable"

# Copy GENMO codebase
COPY . .

# Initialize submodules
RUN git submodule update --init --recursive || echo "No submodules or already initialized"

# Create necessary directories
RUN mkdir -p /workspace/GENMO/inputs/checkpoints/body_models \
    && mkdir -p /workspace/GENMO/webapp/uploads \
    && mkdir -p /workspace/GENMO/webapp/outputs

# Expose port for web app
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Entry point script
COPY docker-entrypoint.sh /workspace/docker-entrypoint.sh
RUN chmod +x /workspace/docker-entrypoint.sh

# Default command
CMD ["/workspace/docker-entrypoint.sh"]
