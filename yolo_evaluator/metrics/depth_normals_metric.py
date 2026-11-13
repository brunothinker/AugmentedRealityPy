"""Estratégia de avaliação de relevo interno via similaridade de normais 2.5D."""

from typing import ClassVar

import cv2
import numpy as np

from .base import BaseMetric, EvaluationContext


class DepthNormalsMetric(BaseMetric):
    """Mede a coerência da orientação local das superfícies dentro do objeto."""

    name: ClassVar[str] = "depth_normals"

    descriptions: ClassVar[dict[str, tuple[str, str]]] = {
        "normal_cosine_pct": (
            "Relevo: Normais 2.5D (↑ %)",
            "Coerência da inclinação das superfícies internas (detecta amassados).",
        ),
    }

    @staticmethod
    def _estimate_pseudo_normals(image_bgr: np.ndarray) -> np.ndarray:
        """Estima vetores normais unitários (nx, ny, nz) a partir dos gradientes de luminância.

        Args:
            image_bgr: Imagem de entrada em BGR.

        Returns:
            Array float32 ``(H, W, 3)`` contendo vetores normais normalizados.
        """
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        smooth = cv2.GaussianBlur(gray, (5, 5), 1.0)
        gx = cv2.Sobel(smooth, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(smooth, cv2.CV_32F, 0, 1, ksize=3)
        gz = np.ones_like(smooth, dtype=np.float32)

        normals = np.dstack((-gx, -gy, gz))
        norm = np.linalg.norm(normals, axis=2, keepdims=True) + 1e-8
        return normals / norm

    def compute(self, ctx: EvaluationContext) -> dict[str, float]:
        """Calcula a similaridade de cosseno média entre normais reais e projetadas.

        Args:
            ctx: Contexto da vista contendo imagens e máscaras alinhadas.

        Returns:
            Dicionário com ``normal_cosine_pct`` (escala 0 a 100).
        """
        valid = (ctx.mask_gt > 127) & (ctx.mask_pred > 127)
        if valid.sum() < 20:
            return {"normal_cosine_pct": 0.0}

        n_gt = self._estimate_pseudo_normals(ctx.real_bgr)
        n_pred = self._estimate_pseudo_normals(ctx.render_bgr)

        cos_sim = np.sum(n_gt[valid] * n_pred[valid], axis=1)
        cos_sim = np.clip(cos_sim, -1.0, 1.0)
        score = float(np.mean((cos_sim + 1.0) / 2.0)) * 100.0

        return {"normal_cosine_pct": score}