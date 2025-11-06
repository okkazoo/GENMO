"""
GENMO Inference Wrapper
Simplified interface for video-to-3D motion generation
"""

import os
import sys
import torch
import numpy as np
from pathlib import Path
from tqdm import tqdm

# Add GENMO root to path
GENMO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(GENMO_ROOT))

from hydra import compose, initialize_config_module
from genmo.utils.pylogger import Log
from genmo.utils.net_utils import to_cuda
from third_party.GVHMR.hmr4d.utils.smplx_utils import make_smplx


def run_genmo_inference(video_path, output_dir, progress_callback=None):
    """
    Run GENMO inference on a video file

    Args:
        video_path: Path to input video
        output_dir: Directory to save outputs
        progress_callback: Optional callback function(progress, message)

    Returns:
        dict with:
            - success: bool
            - smpl_params_path: Path to saved SMPL parameters
            - preview_video: Path to preview video
            - error: Error message if failed
    """
    try:
        if progress_callback:
            progress_callback(10, "Initializing GENMO...")

        # Check if model weights exist
        checkpoint_dir = GENMO_ROOT / "inputs" / "checkpoints"
        if not checkpoint_dir.exists():
            return {
                'success': False,
                'error': 'Model checkpoints not found. Please download GENMO weights first.'
            }

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        if progress_callback:
            progress_callback(20, "Preprocessing video...")

        # Run preprocessing
        result = run_preprocessing(video_path, output_dir, progress_callback)
        if not result['success']:
            return result

        if progress_callback:
            progress_callback(40, "Running GENMO model...")

        # Run GENMO model
        result = run_model(output_dir, progress_callback)
        if not result['success']:
            return result

        if progress_callback:
            progress_callback(60, "Rendering preview...")

        # Render preview video
        result = render_preview(output_dir, progress_callback)
        if not result['success']:
            return result

        if progress_callback:
            progress_callback(70, "Completed inference")

        return {
            'success': True,
            'smpl_params_path': os.path.join(output_dir, 'hmr4d_results.pt'),
            'preview_video': os.path.join(output_dir, 'preview.mp4')
        }

    except Exception as e:
        import traceback
        error_msg = f"GENMO inference failed: {str(e)}\n{traceback.format_exc()}"
        Log.error(error_msg)
        return {
            'success': False,
            'error': error_msg
        }


def run_preprocessing(video_path, output_dir, progress_callback=None):
    """
    Preprocess video: detect people, extract poses and features
    """
    try:
        from third_party.GVHMR.hmr4d.utils.preproc import (
            Extractor, Tracker, VitPoseExtractor
        )
        from genmo.utils.video_io_utils import get_video_lwh, read_video_np

        # Load video
        frames = read_video_np(video_path)
        length, width, height = get_video_lwh(video_path)

        Log.info(f"Video: {length} frames, {width}x{height}")

        # Detect and track people
        if progress_callback:
            progress_callback(25, "Detecting people...")

        tracker = Tracker()
        bbx_xyxy = tracker.track(frames)

        if len(bbx_xyxy) == 0:
            return {
                'success': False,
                'error': 'No people detected in video'
            }

        # Extract 2D poses
        if progress_callback:
            progress_callback(30, "Extracting 2D poses...")

        vitpose = VitPoseExtractor()
        kp2d = vitpose.extract(frames, bbx_xyxy)

        # Extract visual features
        if progress_callback:
            progress_callback(35, "Extracting visual features...")

        extractor = Extractor()
        vit_features = extractor.extract(frames, bbx_xyxy)

        # Save preprocessing results
        torch.save({
            'bbx_xyxy': bbx_xyxy,
            'kp2d': kp2d,
            'vit_features': vit_features,
            'video_path': video_path,
            'width': width,
            'height': height,
            'length': length
        }, os.path.join(output_dir, 'preprocess.pt'))

        return {'success': True}

    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f"Preprocessing failed: {str(e)}\n{traceback.format_exc()}"
        }


def run_model(output_dir, progress_callback=None):
    """
    Run GENMO model to generate 3D motion
    """
    try:
        # Load preprocessing results
        preproc = torch.load(os.path.join(output_dir, 'preprocess.pt'))

        # Initialize Hydra config
        with initialize_config_module(
            version_base="1.3",
            config_module="configs"
        ):
            cfg = compose(config_name="demo")

        # Load GENMO model
        from genmo.genmo import GENMO

        if progress_callback:
            progress_callback(45, "Loading GENMO model...")

        # TODO: Load actual trained model checkpoint
        # For now, we'll use HMR4D as fallback for motion estimation
        from third_party.GVHMR.hmr4d.hmr4d import HMR4D

        model = HMR4D.load_from_checkpoint(
            checkpoint_path=str(GENMO_ROOT / "inputs" / "checkpoints" / "hmr4d" / "model.ckpt")
        ).cuda().eval()

        if progress_callback:
            progress_callback(50, "Running inference...")

        # Run inference
        with torch.no_grad():
            inputs = {
                'vit_features': to_cuda(preproc['vit_features']),
                'kp2d': to_cuda(preproc['kp2d']),
                'bbx_xyxy': to_cuda(preproc['bbx_xyxy'])
            }

            outputs = model(inputs)

        # Extract SMPL parameters
        smpl_params = {
            'body_pose': outputs['pred_smpl_params']['body_pose'].cpu(),
            'betas': outputs['pred_smpl_params']['betas'].cpu(),
            'global_orient': outputs['pred_smpl_params']['global_orient'].cpu(),
            'transl': outputs['pred_smpl_params']['transl'].cpu()
        }

        # Save results
        torch.save({
            'smpl_params_global': smpl_params,
            'smpl_params_incam': smpl_params  # Same for now
        }, os.path.join(output_dir, 'hmr4d_results.pt'))

        return {'success': True}

    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f"Model inference failed: {str(e)}\n{traceback.format_exc()}"
        }


def render_preview(output_dir, progress_callback=None):
    """
    Render a preview video of the 3D motion
    """
    try:
        import cv2
        from genmo.utils.video_io_utils import get_writer
        from genmo.utils.vis.renderer import Renderer, get_global_cameras_static_v2
        from genmo.utils.geo_transform import apply_T_on_points, compute_T_ayfz2ay
        from einops import einsum

        # Load results
        pred = torch.load(os.path.join(output_dir, 'hmr4d_results.pt'))
        preproc = torch.load(os.path.join(output_dir, 'preprocess.pt'))

        # Load SMPL model
        smplx = make_smplx("supermotion").cuda()
        smplx2smpl = torch.load(
            GENMO_ROOT / "inputs/checkpoints/body_models/smplx2smpl_sparse.pt"
        ).cuda()
        faces_smpl = make_smplx("smpl").faces
        J_regressor = torch.load(
            GENMO_ROOT / "inputs/checkpoints/body_models/smpl_neutral_J_regressor.pt"
        ).cuda()

        # Get vertices
        smplx_out = smplx(**to_cuda(pred["smpl_params_global"]))
        pred_verts = torch.stack(
            [torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices]
        )

        # Transform to canonical pose
        def move_to_origin(verts, J_regressor):
            verts = verts.clone()
            offset = einsum(J_regressor, verts[0], "j v, v i -> j i")[0]
            offset[1] = verts[:, :, [1]].min()
            verts = verts - offset
            T_ay2ayfz = compute_T_ayfz2ay(
                einsum(J_regressor, verts[[0]], "j v, l v i -> l j i"),
                inverse=True
            )
            verts = apply_T_on_points(verts, T_ay2ayfz)
            return verts

        verts_glob = move_to_origin(pred_verts, J_regressor)

        # Setup renderer
        width, height = preproc['width'], preproc['height']
        renderer = Renderer(
            width, height,
            device="cuda",
            faces=faces_smpl
        )

        # Get camera parameters
        position, target, up = get_global_cameras_static_v2(
            verts_glob.cpu(),
            beta=3.0,
            cam_height_degree=20,
            target_center_height=1.0
        )

        # Render frames
        preview_path = os.path.join(output_dir, 'preview.mp4')
        writer = get_writer(preview_path, fps=30, crf=23)

        color = torch.ones(3).float().cuda() * 0.8

        for i in tqdm(range(len(verts_glob)), desc="Rendering"):
            img = renderer.render_mesh(
                verts_glob[[i]],
                color[None],
                position[i],
                target[i],
                up[i]
            )
            writer.write_frame(img)

        writer.close()

        return {'success': True}

    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f"Rendering failed: {str(e)}\n{traceback.format_exc()}"
        }


def test_inference(video_path):
    """
    Test inference on a video
    """
    output_dir = "test_output"
    result = run_genmo_inference(
        video_path,
        output_dir,
        progress_callback=lambda p, m: print(f"[{p}%] {m}")
    )

    print(f"\nResult: {result}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_inference(sys.argv[1])
    else:
        print("Usage: python genmo_inference.py <video_path>")
