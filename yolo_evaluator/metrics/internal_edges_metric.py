"""Estratégia de avaliação de arestas internas e dobras via Distância de Chamfer 2D."""

from typing import ClassVar

import cv2
import numpy as np

from .base import BaseMetric, EvaluationContext


class InternalEdgesMetric(BaseMetric):
    """Mede o alinhamento de vincos, dobras e detalhes internos dentro da silhueta."""

    name: ClassVar[str] = "internal_edges"

    descriptions: ClassVar[dict[str, tuple[str, str]]] = {
        "internal_chamfer_px": (
            "Interno: Erro Chamfer (↓ px)",
            "Distância média entre dobras internas reais e projetadas (0 = perfeito).",
        ),
        "internal_edge_f1_pct": (
            "Interno: Arestas F1 (↑ %)",
            "Taxa de acerto dos vincos/detalhes internos dentro de 4px.",
        ),
    }

    @staticmethod
    def _extract_internal_edges(image_bgr: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Extrai bordas de Canny estritamente no interior erodido da máscara.

        Args:
            image_bgr: Imagem de entrada em BGR.
            mask: Máscara binária do objeto.

        Returns:
            Máscara booleana das arestas internas sem contaminação do contorno externo.
        """
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        interior = cv2.erode((mask > 127).astype(np.uint8), kernel) > 0

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 150) > 0
        return np.logical_and(edges, interior)

    def compute(self, ctx: EvaluationContext) -> dict[str, float]:
        """Calcula a Distância de Chamfer simétrica (px) e o F1 das arestas internas.

        Args:
            ctx: Contexto da vista contendo imagens e máscaras.

        Returns:
            Dicionário com ``internal_chamfer_px`` (menor é melhor) e
            ``internal_edge_f1_pct`` (maior é melhor).
        """
        edges_gt = self._extract_internal_edges(ctx.real_bgr, ctx.mask_gt)
        edges_pred = self._extract_internal_edges(ctx.render_bgr, ctx.mask_pred)

        if not edges_gt.any() or not edges_pred.any():
            return {"internal_chamfer_px": 999.0, "internal_edge_f1_pct": 0.0}

        dt_gt = cv2.distanceTransform((~edges_gt).astype(np.uint8), cv2.DIST_L2, 5)
        dt_pred = cv2.distanceTransform((~edges_pred).astype(np.uint8), cv2.DIST_L2, 5)

        d_pred_to_gt = float(dt_gt[edges_pred].mean())
        d_gt_to_pred = float(dt_pred[edges_gt].mean())
        chamfer = (d_pred_to_gt + d_gt_to_pred) / 2.0

        tol = 4.0
        precision = float((dt_gt[edges_pred] <= tol).mean())
        recall = float((dt_pred[edges_gt] <= tol).mean())
        edge_f1 = (
            (2 * precision * recall / (precision + recall)) * 100.0
            if (precision + recall) > 0
            else 0.0
        )

        return {
            "internal_chamfer_px": chamfer,
            "internal_edge_f1_pct": edge_f1,
        }