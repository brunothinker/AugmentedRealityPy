from pathlib import Path
from typing import Callable, Dict
import flet as ft

# Home e Hub Genérico Polimórfico
from ui.pages.hub_page import create_generic_hub_page
from ui.pages.home_page import create_home_page

# Páginas de Módulos (Aplanadas)
from ui.pages.acquisition_page import create_extract_frames_page
from ui.pages.calibration_page import create_mono_calibration_page, create_stereo_calibration_page
from ui.pages.post_processing_page import create_clahe_page, create_resize_page
from ui.pages.projection_page import create_projection_page
from ui.pages.reconstruction_page import create_mono_reconstruction_page, create_stereo_reconstruction_page
from ui.pages.visualization_page import create_visualization_page


# --- FACTORIES DOS HUBS SUB-MODULARES ---

def build_calibration_hub(page: ft.Page, selected_paths: Dict[str, Path], on_navigate: Callable[[str], None]) -> ft.Container:
    return create_generic_hub_page(
        page=page,
        selected_paths=selected_paths,
        on_navigate=on_navigate,
        main_icon=ft.icons.TUNE,
        title="Calibração de Câmeras",
        subtitle="Estime parâmetros intrínsecos e extrínsecos dos sensores",
        options=[
            {
                "title": "Calibração Monocular",
                "description": "Calibre distorções e matriz K de uma única câmera.",
                "icon": ft.icons.CAMERA_ALT,
                "route_key": "mono_calibration",
            },
            {
                "title": "Calibração Estéreo",
                "description": "Calibre o par estéreo e matrizes R/T do rig.",
                "icon": ft.icons.CAMERA,
                "route_key": "stereo_calibration",
            },
        ],
    )


def build_reconstruction_hub(page: ft.Page, selected_paths: Dict[str, Path], on_navigate: Callable[[str], None]) -> ft.Container:
    return create_generic_hub_page(
        page=page,
        selected_paths=selected_paths,
        on_navigate=on_navigate,
        main_icon=ft.icons.LAYERS,
        title="Reconstrução 3D",
        subtitle="Gere nuvens de pontos e malhas a partir de imagens",
        options=[
            {
                "title": "Reconstrução Monocular",
                "description": "Pipeline SfM COLMAP para câmera única em movimento.",
                "icon": ft.icons.IMAGE_SEARCH,
                "route_key": "mono_reconstruction",
            },
            {
                "title": "Reconstrução Estéreo",
                "description": "Reconstrução densa utilizando par estéreo calibrado.",
                "icon": ft.icons.LAYERS,
                "route_key": "stereo_reconstruction",
            },
        ],
    )


def build_post_processing_hub(page: ft.Page, selected_paths: Dict[str, Path], on_navigate: Callable[[str], None]) -> ft.Container:
    return create_generic_hub_page(
        page=page,
        selected_paths=selected_paths,
        on_navigate=on_navigate,
        main_icon=ft.icons.TUNE,
        title="Pós-Processamento de Imagens",
        subtitle="Otimize o conjunto de imagens antes da reconstrução",
        options=[
            {
                "title": "Equalização CLAHE",
                "description": "Realce o contraste local de iluminação nas imagens.",
                "icon": ft.icons.IMAGE_SEARCH,
                "route_key": "clahe_processing",
            },
            {
                "title": "Redimensionamento",
                "description": "Padronize a resolução das imagens em lote.",
                "icon": ft.icons.ASPECT_RATIO,
                "route_key": "resize_processing",
            },
        ],
    )


# --- REGISTRO CENTRAL DE ROTAS ---

ROUTE_REGISTRY = {
    # Home Principal
    "home": {
        "title": "Módulos",
        "builder": create_home_page,
        "is_hub": True,
    },

    # Hubs Sub-Modulares
    "calibration": {
        "title": "Calibração de Câmeras",
        "builder": build_calibration_hub,
        "is_hub": True,
    },
    "reconstruction": {
        "title": "Reconstrução 3D",
        "builder": build_reconstruction_hub,
        "is_hub": True,
    },
    "post_processing": {
        "title": "Pós-Processamento",
        "builder": build_post_processing_hub,
        "is_hub": True,
    },

    # Calibração
    "mono_calibration": {
        "title": "Calibração Monocular",
        "builder": create_mono_calibration_page,
        "is_hub": False,
    },
    "stereo_calibration": {
        "title": "Calibração Estéreo",
        "builder": create_stereo_calibration_page,
        "is_hub": False,
    },

    # Reconstrução
    "mono_reconstruction": {
        "title": "Reconstrução Monocular",
        "builder": create_mono_reconstruction_page,
        "is_hub": False,
    },
    "stereo_reconstruction": {
        "title": "Reconstrução Estéreo",
        "builder": create_stereo_reconstruction_page,
        "is_hub": False,
    },

    # Pós-Processamento
    "clahe_processing": {
        "title": "Equalização CLAHE",
        "builder": create_clahe_page,
        "is_hub": False,
    },
    "resize_processing": {
        "title": "Redimensionamento",
        "builder": create_resize_page,
        "is_hub": False,
    },

    # Módulos Diretos
    "acquisition": {
        "title": "Aquisição de Imagens",
        "builder": create_extract_frames_page,
        "is_hub": False,
    },
    "projection": {
        "title": "Projeção 3D",
        "builder": create_projection_page,
        "is_hub": False,
    },
    "visualization": {
        "title": "Visualizador 3D",
        "builder": create_visualization_page,
        "is_hub": False,
    },
}


def build_page_view(
    route_key: str,
    page: ft.Page,
    selected_paths: Dict[str, Path],
    on_navigate: Callable[[str], None],
) -> ft.Control:
    """Constrói a View Flet correspondente à rota informada."""
    route_info = ROUTE_REGISTRY.get(route_key)
    if not route_info:
        return ft.Container(
            content=ft.Text(f"Rota '{route_key}' não encontrada!", color="red", size=18),
            alignment=ft.alignment.center,
        )

    builder = route_info["builder"]

    if route_info.get("is_hub", False):
        return builder(page, selected_paths, on_navigate=on_navigate)

    return builder(page, selected_paths)