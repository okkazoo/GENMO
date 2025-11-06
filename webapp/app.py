"""
GENMO Video-to-3D Web Application
Flask backend for video upload, processing, and 3D export
"""

import os
import uuid
import json
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from werkzeug.utils import secure_filename
import threading
import time

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'mkv'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Job status tracking
jobs = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """
    Upload video endpoint
    Returns a job_id for tracking processing status
    """
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    file = request.files['video']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: mp4, mov, avi, mkv'}), 400

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file
    filename = secure_filename(file.filename)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], job_id)
    os.makedirs(upload_path, exist_ok=True)

    video_path = os.path.join(upload_path, filename)
    file.save(video_path)

    # Get export format preferences
    export_formats = request.form.get('formats', 'obj,fbx').split(',')

    # Initialize job status
    jobs[job_id] = {
        'status': 'uploaded',
        'progress': 0,
        'video_path': video_path,
        'filename': filename,
        'export_formats': export_formats,
        'created_at': time.time(),
        'message': 'Video uploaded successfully'
    }

    # Start processing in background thread
    thread = threading.Thread(target=process_video, args=(job_id,))
    thread.daemon = True
    thread.start()

    return jsonify({
        'job_id': job_id,
        'message': 'Video uploaded successfully. Processing started.',
        'status': 'uploaded'
    })


def process_video(job_id):
    """
    Background task to process video through GENMO
    """
    try:
        from utils.genmo_inference import run_genmo_inference
        from utils.export_3d import export_motion_to_formats

        job = jobs[job_id]

        # Update status
        jobs[job_id]['status'] = 'processing'
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = 'Running GENMO inference...'

        # Run GENMO inference
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
        os.makedirs(output_dir, exist_ok=True)

        result = run_genmo_inference(
            video_path=job['video_path'],
            output_dir=output_dir,
            progress_callback=lambda p, msg: update_progress(job_id, p, msg)
        )

        if not result['success']:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['message'] = result.get('error', 'Processing failed')
            return

        # Update progress
        jobs[job_id]['progress'] = 70
        jobs[job_id]['message'] = 'Exporting 3D files...'

        # Export to requested formats
        export_result = export_motion_to_formats(
            smpl_params_path=result['smpl_params_path'],
            output_dir=output_dir,
            formats=job['export_formats']
        )

        if not export_result['success']:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['message'] = export_result.get('error', 'Export failed')
            return

        # Update job with results
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['message'] = 'Processing completed successfully'
        jobs[job_id]['results'] = {
            'preview_video': result.get('preview_video'),
            'exported_files': export_result['files'],
            'smpl_params': result.get('smpl_params_path')
        }

    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['message'] = f'Error: {str(e)}'
        import traceback
        jobs[job_id]['error_details'] = traceback.format_exc()


def update_progress(job_id, progress, message):
    """Helper to update job progress"""
    if job_id in jobs:
        jobs[job_id]['progress'] = progress
        jobs[job_id]['message'] = message


@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """
    Get processing status for a job
    """
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    response = {
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'message': job['message']
    }

    if job['status'] == 'completed' and 'results' in job:
        response['results'] = job['results']

    if job['status'] == 'error' and 'error_details' in job:
        response['error_details'] = job['error_details']

    return jsonify(response)


@app.route('/api/download/<job_id>/<filename>', methods=['GET'])
def download_file(job_id, filename):
    """
    Download exported files or preview videos
    """
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed yet'}), 400

    output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
    file_path = os.path.join(output_dir, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(file_path, as_attachment=True)


@app.route('/api/preview/<job_id>', methods=['GET'])
def preview_video(job_id):
    """
    Stream preview video
    """
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = jobs[job_id]
    if job['status'] != 'completed' or 'results' not in job:
        return jsonify({'error': 'Preview not available'}), 400

    preview_path = job['results'].get('preview_video')
    if not preview_path or not os.path.exists(preview_path):
        return jsonify({'error': 'Preview video not found'}), 404

    return send_file(preview_path, mimetype='video/mp4')


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """
    List all jobs (for debugging/management)
    """
    job_list = []
    for job_id, job in jobs.items():
        job_list.append({
            'job_id': job_id,
            'status': job['status'],
            'filename': job['filename'],
            'created_at': job['created_at'],
            'progress': job['progress']
        })

    return jsonify({'jobs': job_list})


@app.route('/api/cleanup/<job_id>', methods=['DELETE'])
def cleanup_job(job_id):
    """
    Clean up job files to free space
    """
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    # Remove files
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], job_id)
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], job_id)

    if os.path.exists(upload_path):
        shutil.rmtree(upload_path)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)

    # Remove job from tracking
    del jobs[job_id]

    return jsonify({'message': 'Job cleaned up successfully'})


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring
    """
    return jsonify({
        'status': 'healthy',
        'jobs_count': len(jobs),
        'active_jobs': len([j for j in jobs.values() if j['status'] == 'processing'])
    })


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='GENMO Video-to-3D Web App')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print(f"""
    ╔═══════════════════════════════════════════╗
    ║  GENMO Video-to-3D Web Application       ║
    ╚═══════════════════════════════════════════╝

    Server starting on http://{args.host}:{args.port}

    Upload videos and export 3D animations for Maya/Blender!
    """)

    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
