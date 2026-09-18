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
    """Orquestra o pipeline de renderização de projeções e vistas sintéticas 3D.

    Realiza a validação estrita dos ficheiros binários do COLMAP e da malha 3D (.ply/.obj),
    cria o diretório de destino estruturado, dispara a renderização off-screen e
    organiza as imagens resultantes por subpastas de câmera.

    Args:
        selected_paths: Dicionário contendo os caminhos selecionados na UI ('colmap_dir', 'mesh_file', 'projection_out').
        output_folder_name: Nome do projeto/subpasta para armazenar as vistas renderizadas em formato string.
        show_toast_callback: Callback para exibição de notificações toast na UI (mensagem, is_error).
        set_ui_state_callback: Callback para definir o estado da UI (is_running, status_message).
    """
    # 1. Validação da pasta esparsa do COLMAP e verificação dos ficheiros binários obrigatórios
    colmap_dir: Optional[Path] = selected_paths.get("colmap_dir")
    if not colmap_dir or not colmap_dir.exists():
        show_toast_callback("Selecione um diretório COLMAP válido (com cameras.bin e images.bin)!", is_error=True)
        return

    if not (colmap_dir / "cameras.bin").exists() or not (colmap_dir / "images.bin").exists():
        show_toast_callback("O diretório COLMAP selecionado não possui 'cameras.bin' e 'images.bin'!", is_error=True)
        return

    # 2. Validação da existência do ficheiro de malha 3D (Mesh)
    mesh_path: Optional[Path] = selected_paths.get("mesh_file")
    if not mesh_path or not mesh_path.exists():
        show_toast_callback("Selecione um arquivo de Mesh (.ply/.obj) válido!", is_error=True)
        return

    # 3. Validação do nome do projeto/subpasta
    folder_name_clean = output_folder_name.strip()
    if not folder_name_clean:
        show_toast_callback("Preencha o nome do projeto!", is_error=True)
        return

    # 4. Resolução do diretório de saída (com fallback para ~/IC_Output/projection)
    base_out: Optional[Path] = selected_paths.get("projection_out")
    if not base_out:
        base_out = Path(get_user_home_dir()) / "IC_Output" / "projection"

    output_dir = base_out / folder_name_clean
    output_dir.mkdir(parents=True, exist_ok=True)

    # 5. Execução do pipeline de renderização sintética e organização de saída
    set_ui_state_callback(True, "Renderizando vistas sintéticas...")

    try:
        # Renderização das projeções sintéticas utilizando PyVista/VTK
        render_synthetic_views(
            colmap_dir=str(colmap_dir),
            mesh_path=str(mesh_path),
            output_dir=str(output_dir)
        )

        set_ui_state_callback(True, "Organizando subpastas por câmera...")

        # Organização dos ficheiros gerados por categorias de câmera (_1x, _uw, etc.)
        organize_output_by_camera(str(output_dir))

        show_toast_callback("✅ Projeções geradas e organizadas com sucesso!", is_error=False)

    except Exception as e:
        show_toast_callback(f"Erro no processo de projeção: {e}", is_error=True)
    finally:
        # Restaura o estado da interface gráfica
        set_ui_state_callback(False, "")