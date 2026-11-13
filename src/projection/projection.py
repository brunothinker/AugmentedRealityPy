import math
import os
from pathlib import Path

import numpy as np
import pyvista as pv

from src.projection.projecton_utils import (
    read_cameras_binary,
    read_images_binary,
    resolve_colmap_bin_dir,
)


def render_synthetic_views(colmap_dir, mesh_path, output_dir):
    """
    Loads the 3D model and renders photos maintaining colors/textures
    from the poses in the COLMAP binary files.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Resolve and load binary data automatically
    resolved_bin_dir = resolve_colmap_bin_dir(colmap_dir)
    print(f"Reading COLMAP binaries from: {resolved_bin_dir}")

    cameras = read_cameras_binary(os.path.join(resolved_bin_dir, "cameras.bin"))
    images = read_images_binary(os.path.join(resolved_bin_dir, "images.bin"))

    # 2. Load the 3D object Mesh
    mesh_file = Path(mesh_path).expanduser().resolve()
    if not mesh_file.exists():
        raise FileNotFoundError(f"Malha 3D não encontrada: {mesh_file}")

    print(f"Loading 3D object: {mesh_file}")
    mesh = pv.read(str(mesh_file))

    # Prepare the plotter with adjusted lighting
    plotter = pv.Plotter(off_screen=True)
    plotter.enable_eye_dome_lighting()  # type: ignore[call-arg]

    # Dynamic color / texture configuration
    if mesh.active_scalars_name is not None or "RGB" in mesh.point_data or "Colors" in mesh.point_data:
        plotter.add_mesh(mesh, rgb=True, smooth_shading=True)
        print(" [i] Rendering with per-vertex colors extracted from the PLY.")
    elif hasattr(mesh, "textures") and len(mesh.textures) > 0:
        plotter.add_mesh(mesh, texture=list(mesh.textures.values())[0], smooth_shading=True)
        print(" [i] Rendering with texture map.")
    else:
        plotter.add_mesh(mesh, color="white", smooth_shading=True)
        print(" [!] Warning: No color/texture found on the mesh. Using neutral color.")

    print(f"Starting projection of {len(images)} views...")

    for img_id, img_data in images.items():
        cam_data = cameras[img_data["camera_id"]]

        # --- EXTRINSICS ---
        R = img_data["R"]
        T = img_data["tvec"]

        # Camera Position in World Space: C = -R^T * T
        R_inv = R.T
        camera_pos = -np.dot(R_inv, T)

        # Camera viewing direction (+Z axis in COLMAP)
        focal_point = camera_pos + np.dot(R_inv, np.array([0, 0, 1]))

        # Camera Up Vector (In COLMAP Y points down -> -Y in PyVista)
        up_vector = np.dot(R_inv, np.array([0, -1, 0]))

        # --- INTRINSICS ---
        width = cam_data["width"]
        height = cam_data["height"]
        focal_length = cam_data["params"][0]

        # Calculation of Vertical FOV in Degrees
        fov_v_rad = 2 * math.atan(height / (2 * focal_length))
        fov_v_deg = math.degrees(fov_v_rad)

        # --- CAMERA CONFIGURATION IN PYVISTA ---
        plotter.camera.position = camera_pos.tolist()
        plotter.camera.focal_point = focal_point.tolist()
        plotter.camera.up = up_vector.tolist()
        plotter.camera.view_angle = fov_v_deg
        plotter.window_size = [width, height]

        # Saves the projected render keeping correlation with the original image
        out_filename = f"synth_{os.path.basename(img_data['name'])}"
        out_path = os.path.join(output_dir, out_filename)

        plotter.screenshot(out_path)
        print(f" [✓] Generated: {out_filename}")

    plotter.close()
    print("Projection process completed successfully!")