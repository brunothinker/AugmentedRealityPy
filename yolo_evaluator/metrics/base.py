"""Contratos base e estruturas de dados compartilhadas entre as métricas."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

import numpy as np


@dataclass(frozen=True)
class EvaluationContext:
    """Pacote imutável com todos os dados alinhados de uma vista para avaliação.

    Attributes:
        view_name: Identificador único da vista (nome base do arquivo sem extensão).
        camera_type: Identificador da lente/câmera (``"1x"`` ou ``"uw"``).
        real_bgr: Imagem fotográfica real (Ground Truth) em BGR.
        render_bgr: Imagem projetada sinteticamente a partir da malha 3D em BGR.
        mask_gt: Máscara binária de referência extraída da foto real.
        mask_pred: Máscara binária extraída da projeção renderizada.
        bbox_gt: Bounding box derivada da máscara real ``[x1, y1, x2, y2]``.
        bbox_pred: Bounding box detectada ou utilizada no render.
        yolo_conf: Confiança da detecção YOLO no render (0.0 a 1.0).
    """

    view_name: str
    camera_type: str
    real_bgr: np.ndarray
    render_bgr: np.ndarray
    mask_gt: np.ndarray
    mask_pred: np.ndarray
    bbox_gt: list[float] | None
    bbox_pred: list[float] | None
    yolo_conf: float


class BaseMetric(ABC):
    """Interface abstrata (Strategy) para estratégias de avaliação geométrica/visual."""

    name: ClassVar[str] = "base"
    descriptions: ClassVar[dict[str, tuple[str, str]]] = {}

    @abstractmethod
    def compute(self, ctx: EvaluationContext) -> dict[str, float]:
        """Executa o cálculo da métrica sobre o contexto de uma vista.

        Args:
            ctx: Contexto contendo imagens, máscaras e metadados da vista.

        Returns:
            Dicionário mapeando ``{nome_submetrica: valor_numerico}``.
        """