from pathlib import Path
from typing import Callable, Dict, Optional

from src.projection.projection import render_synthetic_views
from src.projection.projecton_utils import organize_output_by_camera
from ui.ui_utils import get_user_home_dir


def handle_render_projection(
    selected_paths: Dict[str, Path],
    output_folder_name: str,
    show_toast_callback: Callable[[str, bool], None],
    set_ui_state_callback: Callable[[bool, str], None],
) -> None:
    """
    Controller para a renderização de projeções sintéticas 3D.
    Valida as entradas da UI, resolve o diretório de saída e dispara a execução.
    """
    # 1. Validação da Pasta do COLMAP (contendo os binários)
    colmap_dir: Optional[Path] = selected_paths.get("colmap_dir")
    if not colmap_dir or not colmap_dir.exists():
        show_toast_callback("Selecione um diretório COLMAP válido (com cameras.bin e images.bin)!", is_error=True)
        return

    if not (colmap_dir / "cameras.bin").exists() or not (colmap_dir / "images.bin").exists():
        show_toast_callback("O diretório COLMAP selecionado não possui 'cameras.bin' e 'images.bin'!", is_error=True)
        return

    # 2. Validação do arquivo de Mesh
    mesh_path: Optional[Path] = selected_paths.get("mesh_file")
    if not mesh_path or not mesh_path.exists():
        show_toast_callback("Selecione um arquivo de Mesh (.ply/.obj) válido!", is_error=True)
        return

    # 3. Validação do Nome do Projeto
    folder_name_clean = output_folder_name.strip()
    if not folder_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    # 4. Definição do Diretório de Saída Escolhido ou Fallback para ~/IC_Output/projection
    base_out: Optional[Path] = selected_paths.get("projection_out")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output" / "projection"

    output_dir = base_out / folder_name_clean
    output_dir.mkdir(parents=True, exist_ok=True)

    # 5. Início do Processamento
    set_ui_state_callback(True, "Renderizando vistas sintéticas...")

    try:
        # Renderiza as projeções usando PyVista
        render_synthetic_views(
            colmap_dir=str(colmap_dir),
            mesh_path=str(mesh_path),
            output_dir=str(output_dir)
        )

        set_ui_state_callback(True, "Organizando subpastas por câmera...")

        # Organiza a saída dividindo por subpastas de câmera (_1x, _uw, etc.)
        organize_output_by_camera(str(output_dir))

        show_toast_callback("✅ Projeções geradas e organizadas com sucesso!", is_error=False)

    except Exception as e:
        show_toast_callback(f"Erro no processo de projeção: {e}", is_error=True)
    finally:
        set_ui_state_callback(False, "")