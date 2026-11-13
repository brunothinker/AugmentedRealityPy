"""Extrator compartilhado de segmentação combinando YOLOv8 e SAM 2.1.

Responsável por detectar a região de interesse (bounding box) e extrair
máscaras binárias pixel a pixel, com suporte a prompts negativos para
preservar cavidades internas e geração de máscaras Ground Truth.
"""

from pathlib import Path
from typing import Any

import cv2
import numpy as np
from tqdm import tqdm
from ultralytics import SAM
from unique_pipeline import YOLOBoxEvaluator


class MaskExtractor:
    """Combina detecção de objetos via YOLO com segmentação fina via SAM."""

    def __init__(
        self,
        yolo_weights_path: Path,
        sam_weights: str = "sam2.1_b.pt",
        conf_threshold: float = 0.15,
    ) -> None:
        """Inicializa os modelos YOLO e SAM em memória.

        Args:
            yolo_weights_path: Caminho para os pesos treinados do YOLO (.pt).
            sam_weights: Identificador ou caminho dos pesos do Segment Anything Model.
            conf_threshold: Limiar mínimo de confiança para aceitar detecções do YOLO.
        """
        self.yolo_evaluator = YOLOBoxEvaluator(weights_path=yolo_weights_path)
        self.sam_model = SAM(sam_weights)
        self.conf_threshold = conf_threshold

    @staticmethod
    def find_hole_centroids(mask: np.ndarray, min_area: int = 500) -> list[list[float]]:
        """Localiza os centroides (x, y) de buracos internos fechados na máscara.

        Utiliza análise de componentes conectados na máscara invertida, ignorando
        regiões que tocam as bordas da imagem (fundo externo) e ruídos menores
        que ``min_area``.

        Args:
            mask: Máscara binária em escala de cinza (0 ou 255).
            min_area: Área mínima em pixels para considerar uma cavidade válida.

        Returns:
            Lista de coordenadas ``[cx, cy]`` para cada buraco interno detectado.
        """
        bin_mask = (mask > 127).astype(np.uint8)
        inverted = 1 - bin_mask
        num_labels, _, stats, centroids = cv2.connectedComponentsWithStats(
            inverted, connectivity=4
        )

        h, w = bin_mask.shape
        hole_points: list[list[float]] = []
        for label_id in range(1, num_labels):
            x, y, bw, bh, area = stats[label_id]
            touches_border = (
                x <= 1 or y <= 1 or (x + bw) >= (w - 1) or (y + bh) >= (h - 1)
            )
            if not touches_border and area >= min_area:
                cx, cy = centroids[label_id]
                hole_points.append([float(cx), float(cy)])

        return hole_points

    def extract_mask(
        self,
        image_bgr: np.ndarray,
        fallback_bbox: list[float] | None = None,
        negative_points: list[list[float]] | None = None,
    ) -> tuple[np.ndarray | None, list[float] | None, float]:
        """Detecta o objeto via YOLO e extrai sua silhueta binária via SAM.

        Caso o detector não encontre o objeto com confiança acima do limiar,
        utiliza ``fallback_bbox`` (geralmente derivada do Ground Truth) como
        prompt espacial para o SAM.

        Args:
            image_bgr: Imagem de entrada no espaço de cores BGR.
            fallback_bbox: Caixa delimitadora ``[x1, y1, x2, y2]`` de reserva.
            negative_points: Pontos ``[x, y]`` marcados como fundo (label=0) para
                forçar a preservação de furos internos.

        Returns:
            Tupla contendo ``(mascara_binaria, bbox_utilizada, confianca_yolo)``.
        """
        results: Any = self.yolo_evaluator.model.predict(
            source=image_bgr, conf=self.conf_threshold, verbose=False
        )

        best_conf = 0.0
        best_bbox: list[float] | None = None
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf > best_conf:
                    best_conf = conf
                    best_bbox = box.xyxy[0].tolist()

        prompt_bbox = best_bbox if best_bbox is not None else fallback_bbox
        if prompt_bbox is None:
            return None, None, 0.0

        predict_kwargs: dict[str, Any] = {
            "source": image_bgr,
            "bboxes": [prompt_bbox],
            "verbose": False,
        }
        if negative_points:
            # Centro da bbox atua como âncora positiva (1) e os furos como negativas (0)
            cx = (prompt_bbox[0] + prompt_bbox[2]) / 2.0
            cy = (prompt_bbox[1] + prompt_bbox[3]) / 2.0
            points = [[cx, cy], *negative_points]
            labels = [1] + [0] * len(negative_points)
            predict_kwargs["points"] = [points]
            predict_kwargs["labels"] = [labels]

        sam_results: Any = self.sam_model.predict(**predict_kwargs)

        for r in sam_results:
            if r.masks is not None and len(r.masks.data) > 0:
                mask_tensor = r.masks.data[0].cpu().numpy()
                binary_mask = (mask_tensor > 0.5).astype(np.uint8) * 255
                return binary_mask, prompt_bbox, best_conf

        return None, prompt_bbox, best_conf

    def generate_ground_truth(
        self, real_dir: Path, out_masks_dir: Path, imread_fn: Any = cv2.imread
    ) -> None:
        """Gera máscaras binárias Ground Truth a partir das fotografias reais.

        Args:
            real_dir: Diretório raiz contendo as imagens reais de referência.
            out_masks_dir: Diretório onde as máscaras PNG serão salvas.
            imread_fn: Função de leitura de imagem (permite suprimir avisos C).
        """
        extensions = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG")
        images: list[Path] = []
        for ext in extensions:
            images.extend(real_dir.rglob(ext))
        images = sorted(set(images))

        out_masks_dir.mkdir(parents=True, exist_ok=True)
        for img_p in tqdm(images, desc="Gerando GT", unit="img", leave=False):
            rel = img_p.relative_to(real_dir)
            orig = imread_fn(img_p)
            if orig is None:
                continue

            mask, _, _ = self.extract_mask(orig)
            if mask is None:
                continue

            mask_out = (out_masks_dir / rel).with_suffix(".png")
            mask_out.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(mask_out), mask)