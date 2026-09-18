from pathlib import Path
from typing import Dict, Callable, Optional

from src.reconstruction.stereo_reconstruction import run_stereo_reconstruction
from ui.ui_utils import get_user_home_dir


def handle_stereo_reconstruction(
    selected_paths: Dict[str, Path],
    baseline_str: str,
    show_toast_callback: Callable[[str, bool], None],
    update_progress_callback: Callable[[float, str], None],
    set_ui_state_callback: Callable[[bool, str], None],
) -> None:
    """
    Controller for 3D Stereo Reconstruction (Automatic COLMAP Rig).
    Validates selected camera directories, baseline value, and triggers the reconstruction pipeline.
    """
    # Retrieve left and right camera directory paths from selected_paths
    cam_left_dir: Optional[Path] = selected_paths.get("stereo_rec_left")
    cam_right_dir: Optional[Path] = selected_paths.get("stereo_rec_right")

    # Ensure both camera directories have been selected and exist on the filesystem
    if not cam_left_dir or not cam_left_dir.exists() or not cam_right_dir or not cam_right_dir.exists():
        show_toast_callback("Select both camera folders (Left and Right)!", is_error=True)
        return

    # Extract parent directory containing both camera subdirectories (e.g., .../frames)
    images_dir: Path = cam_left_dir.parent

    # Validate and parse the baseline numerical value
    try:
        baseline = float(baseline_str.replace(",", "."))
        if baseline <= 0:
            raise ValueError
    except ValueError:
        show_toast_callback("Enter a positive numeric value for the baseline (meters)!", is_error=True)
        return

    # Set default output directory if not explicitly selected by the user
    out_dir: Optional[Path] = selected_paths.get("stereo_rec_out")
    if not out_dir:
        out_dir = Path(get_user_home_dir()) / "IC_Output" / "reconstrucoes" / f"{images_dir.name}_stereo_3d"

    set_ui_state_callback(True, "Starting stereo reconstruction pipeline...")

    try:
        # Pass the parent images folder and parameters expected by run_stereo_reconstruction
        success = run_stereo_reconstruction(
            pasta_frames=images_dir,
            pasta_projeto_saida=out_dir,
            baseline_metros=baseline,
            progress_callback=update_progress_callback
        )
        show_toast_callback(
            "Stereo reconstruction completed successfully!" if success else "Stereo reconstruction failed.",
            is_error=not success
        )
    except Exception as e:
        show_toast_callback(f"Unexpected error: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")