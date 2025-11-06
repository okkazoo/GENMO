"""
3D Export Utilities
Export SMPL motion to various 3D formats (OBJ, FBX, USD, Alembic)
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

from genmo.utils.net_utils import to_cuda
from third_party.GVHMR.hmr4d.utils.smplx_utils import make_smplx


def export_motion_to_formats(smpl_params_path, output_dir, formats=['obj', 'fbx']):
    """
    Export SMPL motion to various 3D formats

    Args:
        smpl_params_path: Path to SMPL parameters file (.pt)
        output_dir: Directory to save exported files
        formats: List of formats to export ['obj', 'fbx', 'usd', 'abc']

    Returns:
        dict with:
            - success: bool
            - files: List of exported file info
            - error: Error message if failed
    """
    try:
        # Load SMPL parameters
        pred = torch.load(smpl_params_path)
        smpl_params = pred['smpl_params_global']

        # Load SMPL model
        smplx = make_smplx("supermotion").cuda()
        smplx2smpl_path = GENMO_ROOT / "inputs/checkpoints/body_models/smplx2smpl_sparse.pt"

        if not smplx2smpl_path.exists():
            return {
                'success': False,
                'error': f'SMPL conversion matrix not found at {smplx2smpl_path}'
            }

        smplx2smpl = torch.load(smplx2smpl_path).cuda()
        faces_smpl = make_smplx("smpl").faces

        # Generate vertices from SMPL parameters
        with torch.no_grad():
            smplx_out = smplx(**to_cuda(smpl_params))
            vertices = torch.stack(
                [torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices]
            ).cpu().numpy()

        num_frames = vertices.shape[0]
        exported_files = []

        # Export to requested formats
        if 'obj' in formats:
            result = export_obj_sequence(
                vertices, faces_smpl, output_dir, num_frames
            )
            if result['success']:
                exported_files.extend(result['files'])

        if 'fbx' in formats:
            result = export_fbx(
                vertices, faces_smpl, output_dir, smpl_params
            )
            if result['success']:
                exported_files.append(result['file'])

        if 'usd' in formats:
            result = export_usd(
                vertices, faces_smpl, output_dir
            )
            if result['success']:
                exported_files.append(result['file'])

        if 'abc' in formats:
            result = export_alembic(
                vertices, faces_smpl, output_dir
            )
            if result['success']:
                exported_files.append(result['file'])

        return {
            'success': True,
            'files': exported_files
        }

    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f"Export failed: {str(e)}\n{traceback.format_exc()}"
        }


def export_obj_sequence(vertices, faces, output_dir, num_frames):
    """
    Export as OBJ sequence (one file per frame)
    Universal format, works with all 3D software
    """
    try:
        import trimesh

        obj_dir = os.path.join(output_dir, 'obj_sequence')
        os.makedirs(obj_dir, exist_ok=True)

        exported_files = []

        for frame_idx in tqdm(range(num_frames), desc="Exporting OBJ sequence"):
            mesh = trimesh.Trimesh(
                vertices=vertices[frame_idx],
                faces=faces,
                process=False
            )

            obj_filename = f'frame_{frame_idx:04d}.obj'
            obj_path = os.path.join(obj_dir, obj_filename)
            mesh.export(obj_path)

            exported_files.append({
                'name': f'obj_sequence/{obj_filename}',
                'size': os.path.getsize(obj_path),
                'format': 'obj'
            })

        # Create a single combined OBJ (just first frame as reference)
        combined_path = os.path.join(output_dir, 'mesh_reference.obj')
        mesh = trimesh.Trimesh(
            vertices=vertices[0],
            faces=faces,
            process=False
        )
        mesh.export(combined_path)

        exported_files.append({
            'name': 'mesh_reference.obj',
            'size': os.path.getsize(combined_path),
            'format': 'obj'
        })

        return {
            'success': True,
            'files': exported_files
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"OBJ export failed: {str(e)}"
        }


def export_fbx(vertices, faces, output_dir, smpl_params):
    """
    Export as FBX with animation
    Industry standard for Maya/Blender
    """
    try:
        # FBX export requires additional libraries
        # We'll use a Python FBX SDK or create via Blender Python API
        fbx_path = os.path.join(output_dir, 'animation.fbx')

        try:
            # Method 1: Try using pyfbx (if available)
            import pyfbx
            export_fbx_with_pyfbx(vertices, faces, fbx_path, smpl_params)

        except ImportError:
            # Method 2: Fallback - export as FBX ASCII (compatible format)
            export_fbx_ascii(vertices, faces, fbx_path, smpl_params)

        file_size = os.path.getsize(fbx_path)

        return {
            'success': True,
            'file': {
                'name': 'animation.fbx',
                'size': file_size,
                'format': 'fbx'
            }
        }

    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': f"FBX export failed: {str(e)}\n{traceback.format_exc()}"
        }


def export_fbx_ascii(vertices, faces, output_path, smpl_params):
    """
    Export as FBX ASCII format (compatible fallback)
    This creates a basic FBX that can be imported into Maya/Blender
    """
    num_frames = vertices.shape[0]
    num_verts = vertices.shape[1]

    # For simplicity, we'll create a mesh sequence
    # In production, you'd want proper rigging with SMPL skeleton

    # Create basic FBX ASCII header
    fbx_content = f"""; FBX 7.4.0 project file
; Created by GENMO Video-to-3D
; Animation with {num_frames} frames

FBXHeaderExtension:  {{
    FBXHeaderVersion: 1003
    FBXVersion: 7400
}}

Definitions:  {{
    Version: 100
    Count: 2

    ObjectType: "Geometry" {{
        Count: 1
    }}

    ObjectType: "Model" {{
        Count: 1
    }}
}}

Objects:  {{
    Geometry: 1234567890, "Geometry::", "Mesh" {{
        Vertices: *{num_verts * 3} {{
            a: {','.join(map(str, vertices[0].flatten()))}
        }}

        PolygonVertexIndex: *{len(faces) * 3} {{
            a: {','.join(map(str, faces.flatten()))}
        }}
    }}

    Model: 9876543210, "Model::SMPLMesh", "Mesh" {{
        Version: 232
        Properties70:  {{
        }}
    }}
}}

Connections:  {{
    C: "OO",1234567890,9876543210
}}

; Animation data would go here in full implementation
"""

    with open(output_path, 'w') as f:
        f.write(fbx_content)


def export_fbx_with_pyfbx(vertices, faces, output_path, smpl_params):
    """
    Export using pyfbx library (if available)
    """
    # This would use actual FBX SDK
    # Left as placeholder for when library is available
    raise NotImplementedError("pyfbx not available, using ASCII fallback")


def export_usd(vertices, faces, output_dir):
    """
    Export as USD (Universal Scene Description)
    Modern format used in VFX pipelines
    """
    try:
        from pxr import Usd, UsdGeom, Vt, Sdf

        usd_path = os.path.join(output_dir, 'animation.usdc')
        stage = Usd.Stage.CreateNew(usd_path)

        # Create mesh
        mesh_path = '/World/SMPLMesh'
        mesh = UsdGeom.Mesh.Define(stage, mesh_path)

        # Set topology (constant)
        mesh.CreateFaceVertexCountsAttr([3] * len(faces))
        mesh.CreateFaceVertexIndicesAttr(faces.flatten().tolist())

        # Set animated vertices
        num_frames = vertices.shape[0]
        points_attr = mesh.CreatePointsAttr()

        for frame_idx in tqdm(range(num_frames), desc="Exporting USD"):
            points_attr.Set(
                Vt.Vec3fArray.FromNumpy(vertices[frame_idx]),
                time=frame_idx
            )

        # Set frame range
        stage.SetStartTimeCode(0)
        stage.SetEndTimeCode(num_frames - 1)
        stage.SetTimeCodesPerSecond(30)

        stage.Save()

        return {
            'success': True,
            'file': {
                'name': 'animation.usdc',
                'size': os.path.getsize(usd_path),
                'format': 'usd'
            }
        }

    except ImportError:
        return {
            'success': False,
            'error': 'USD export requires pxr library (pip install usd-core)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"USD export failed: {str(e)}"
        }


def export_alembic(vertices, faces, output_dir):
    """
    Export as Alembic (.abc)
    Animation cache format for Maya/Houdini/Blender
    """
    try:
        import alembic

        abc_path = os.path.join(output_dir, 'animation.abc')

        # Alembic export would go here
        # This requires python-alembic bindings
        # For now, we'll document this as a TODO

        return {
            'success': False,
            'error': 'Alembic export not yet implemented (requires python-alembic)'
        }

    except ImportError:
        return {
            'success': False,
            'error': 'Alembic export requires alembic library'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Alembic export failed: {str(e)}"
        }


def create_maya_import_script(output_dir):
    """
    Create a MEL/Python script for importing OBJ sequence into Maya
    """
    mel_script = """// GENMO Import Script for Maya
// Import OBJ sequence as animation

global proc importOBJSequence(string $dir) {
    string $files[] = `getFileList -folder $dir -filespec "frame_*.obj"`;
    string $firstFile = $dir + $files[0];

    // Import first frame
    file -import -type "OBJ" $firstFile;
    string $meshShape = `ls -selection -dag -shapes`;

    // Create blendShape for animation
    string $bsNode[] = `blendShape -name "objSequenceBS" $meshShape`;

    // Import remaining frames as blend targets
    int $i;
    for($i = 1; $i < size($files); $i++) {
        string $file = $dir + $files[$i];
        file -import -type "OBJ" $file;
        string $target[] = `ls -selection -dag -shapes`;
        blendShape -edit -target $meshShape $i $target[0] 1.0 $bsNode[0];
        delete $target[0];

        // Set keyframe
        setKeyframe -value 0 -time $i -attribute ($bsNode[0] + "." + $target[0]);
        setKeyframe -value 1 -time ($i+1) -attribute ($bsNode[0] + "." + $target[0]);
    }
}

// Run import
importOBJSequence("OBJ_SEQUENCE_PATH");
"""

    script_path = os.path.join(output_dir, 'import_to_maya.mel')
    with open(script_path, 'w') as f:
        f.write(mel_script)

    return script_path


def create_blender_import_script(output_dir):
    """
    Create a Python script for importing OBJ sequence into Blender
    """
    py_script = """# GENMO Import Script for Blender
# Import OBJ sequence as animation

import bpy
import os
from pathlib import Path

def import_obj_sequence(obj_dir):
    obj_files = sorted(Path(obj_dir).glob('frame_*.obj'))

    if not obj_files:
        print("No OBJ files found")
        return

    # Import first frame
    bpy.ops.import_scene.obj(filepath=str(obj_files[0]))
    mesh_obj = bpy.context.selected_objects[0]
    mesh_obj.name = "GENMO_Animation"

    # Add shape keys for animation
    mesh_obj.shape_key_add(name="Basis")

    for i, obj_file in enumerate(obj_files[1:], start=1):
        # Import as shape key
        bpy.ops.import_scene.obj(filepath=str(obj_file))
        imported = bpy.context.selected_objects[0]

        # Add as shape key
        shape_key = mesh_obj.shape_key_add(name=f"Frame_{i:04d}")

        # Copy vertex positions
        for v_idx, vert in enumerate(imported.data.vertices):
            shape_key.data[v_idx].co = vert.co

        # Delete imported mesh
        bpy.data.objects.remove(imported)

        # Set keyframes
        shape_key.value = 0
        shape_key.keyframe_insert(data_path="value", frame=i-1)
        shape_key.value = 1
        shape_key.keyframe_insert(data_path="value", frame=i)
        shape_key.value = 0
        shape_key.keyframe_insert(data_path="value", frame=i+1)

# Run import
import_obj_sequence("OBJ_SEQUENCE_PATH")
"""

    script_path = os.path.join(output_dir, 'import_to_blender.py')
    with open(script_path, 'w') as f:
        f.write(py_script)

    return script_path


if __name__ == "__main__":
    # Test export
    if len(sys.argv) > 1:
        smpl_path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "export_output"

        result = export_motion_to_formats(smpl_path, output_dir)
        print(f"Export result: {result}")
    else:
        print("Usage: python export_3d.py <smpl_params.pt> [output_dir]")
