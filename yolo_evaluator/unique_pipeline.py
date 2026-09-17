import argparse
from pathlib import Path
from typing import Any, Dict, List, Tuple
import yaml
from ultralytics import YOLO


# -----------------------------------------------------------------------------
# 1. Utilidades para Anotação e Dataset
# -----------------------------------------------------------------------------
def create_yolo_label(
        output_txt_path: Path,
        img_width: int,
        img_height: int,
        bbox_pixels: Tuple[float, float, float, float],
        class_id: int = 0,
) -> Path:
    """Converte coordenadas em pixels (x_min, y_min, x_max, y_max) para o formato
    normalizado do YOLO (0.0 a 1.0) e escreve o arquivo .txt correspondente.
    """
    x_min, y_min, x_max, y_max = bbox_pixels

    box_w = x_max - x_min
    box_h = y_max - y_min
    x_center = x_min + (box_w / 2.0)
    y_center = y_min + (box_h / 2.0)

    x_center_norm = x_center / img_width
    y_center_norm = y_center / img_height
    box_w_norm = box_w / img_width
    box_h_norm = box_h / img_height

    output_txt_path = Path(output_txt_path).resolve()
    output_txt_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(
            f"{class_id} {x_center_norm:.6f} {y_center_norm:.6f} {box_w_norm:.6f} {box_h_norm:.6f}\n"
        )

    return output_txt_path


def setup_dataset_yaml(base_dir: Path) -> Path:
    """Gera/sobrescreve o arquivo data.yaml apontando para os caminhos absolutos exatos."""
    dataset_dir = (base_dir / "dataset").resolve()
    yaml_path = dataset_dir / "data.yaml"

    data = {
        "path": str(dataset_dir),
        "train": "images/train",
        "val": "images/val",
        "names": {0: "caixa"},
    }

    dataset_dir.mkdir(parents=True, exist_ok=True)
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)

    return yaml_path


# -----------------------------------------------------------------------------
# 2. Classe de Avaliação de Projeção 2D
# -----------------------------------------------------------------------------
class YOLOBoxEvaluator:
    """Carrega os pesos do YOLO treinado e avalia a qualidade da projeção 2D."""

    def __init__(self, weights_path: Path):
        self.weights_path = Path(weights_path).resolve()
        if not self.weights_path.exists():
            raise FileNotFoundError(
                f"Arquivo de pesos não encontrado: {self.weights_path}"
            )
        self.model = YOLO(str(self.weights_path))

    def evaluate_projection(
            self, image_path: Path, conf_threshold: float = 0.10
    ) -> Dict[str, Any]:
        """Avalia uma imagem de projeção 2D e retorna a métrica de confiança da detecção."""
        img_path = Path(image_path).resolve()
        if not img_path.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {img_path}")

        results = self.model.predict(
            source=str(img_path), conf=conf_threshold, verbose=False
        )

        detections: List[Dict[str, Any]] = []
        max_confidence = 0.0

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                xyxy = box.xyxy[0].tolist()

                if conf > max_confidence:
                    max_confidence = conf

                detections.append(
                    {"class_id": cls_id, "confidence": conf, "bbox_xyxy": xyxy}
                )

        return {
            "image_name": img_path.name,
            "relative_path": str(img_path),
            "object_detected": len(detections) > 0,
            "quality_score": max_confidence,
            "all_detections": detections,
        }

    def evaluate_directory(
            self, dir_path: Path, conf_threshold: float = 0.10
    ) -> List[Dict[str, Any]]:
        """Avalia todas as imagens (.jpg, .jpeg, .png) dentro de um diretório e suas subpastas."""
        dir_path = Path(dir_path).resolve()
        if not dir_path.exists():
            raise FileNotFoundError(f"Diretório não encontrado: {dir_path}")

        extensions = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG")
        image_files: List[Path] = []

        # Busca recursiva em todas as subpastas (ex: esquerda, direita)
        for ext in extensions:
            image_files.extend(dir_path.rglob(ext))

        image_files = sorted(list(set(image_files)))

        if not image_files:
            print(f"[!] Nenhuma imagem encontrada em: {dir_path}")
            return []

        results = []
        for img_p in image_files:
            res = self.evaluate_projection(img_p, conf_threshold=conf_threshold)
            # Salva o caminho relativo à pasta informada para exibição limpa
            try:
                res["relative_path"] = str(img_p.relative_to(dir_path))
            except ValueError:
                res["relative_path"] = img_p.name
            results.append(res)

        return results


# -----------------------------------------------------------------------------
# 3. Execução de Treinamento
# -----------------------------------------------------------------------------
def run_training(
        base_dir: Path,
        base_model: str = "yolov8n.pt",
        epochs: int = 50,
        imgsz: int = 640,
        batch: int = 16,
) -> Path:
    """Executa o treinamento do YOLO e grava os artefatos em yolo_evaluator/."""
    yaml_path = setup_dataset_yaml(base_dir)

    print(f"\n[+] Configuração do dataset atualizada em: {yaml_path}")

    base_model_path = base_dir / base_model
    model = YOLO(str(base_model_path) if base_model_path.exists() else base_model)

    runs_dir = base_dir / "runs"
    model.train(
        data=str(yaml_path),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=str(runs_dir),
        name="caixa_model",
        exist_ok=True,
    )

    best_weights = runs_dir / "caixa_model" / "weights" / "best.pt"
    if not best_weights.exists():
        raise RuntimeError("Treinamento concluído, mas best.pt não foi gerado.")

    print(f"\n[+] Treinamento concluído! Pesos salvos em: {best_weights}")
    return best_weights


# -----------------------------------------------------------------------------
# 4. CLI / Teste Integrado
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script Standalone do Avaliador YOLO para Projeção 3D."
    )
    parser.add_argument(
        "--train",
        action="store_true",
        help="Executa a etapa de treinamento.",
    )
    parser.add_argument(
        "--predict",
        type=str,
        help="Caminho para uma única imagem de projeção 2D para avaliar.",
    )
    parser.add_argument(
        "--predict-dir",
        type=str,
        help="Caminho para o diretório contendo imagens de projeção 2D.",
    )
    parser.add_argument(
        "--epochs", type=int, default=50, help="Número de épocas de treino."
    )

    args = parser.parse_args()

    working_dir = Path(__file__).resolve().parent
    weights_file = working_dir / "runs" / "caixa_model" / "weights" / "best.pt"

    if args.train:
        print(f"=== Iniciando Treinamento em: {working_dir} ===")
        weights_file = run_training(base_dir=working_dir, epochs=args.epochs)

    evaluator = None
    if args.predict or args.predict_dir:
        evaluator = YOLOBoxEvaluator(weights_path=weights_file)

    if args.predict:
        print("\n=== Executando Avaliação de Imagem Única ===")
        resultado = evaluator.evaluate_projection(Path(args.predict))
        print(f"Imagem: {resultado['image_name']}")
        print(f"Caixa Detectada: {resultado['object_detected']}")
        print(f"Score de Semelhança: {resultado['quality_score'] * 100:.2f}%\n")

    if args.predict_dir:
        print(f"\n=== Avaliando Projeções em: {args.predict_dir} ===")
        resultados = evaluator.evaluate_directory(Path(args.predict_dir))

        if resultados:
            print(f"\n{'Imagem (Caminho Relativo)':<55} | {'Caixa Detectada?':<18} | {'Score (% Caixa)':<15}")
            print("-" * 94)

            scores = []
            for r in resultados:
                score_pct = r['quality_score'] * 100
                scores.append(score_pct)
                status = "SIM" if r['object_detected'] else "NÃO"
                print(f"{r['relative_path']:<55} | {status:<18} | {score_pct:>13.2f}%")

            avg_score = sum(scores) / len(scores)
            print("-" * 94)
            print(f"Média Geral da Reconstrução: {avg_score:.2f}% de semelhança com uma caixa.\n")

    if not args.train and not args.predict and not args.predict_dir:
        parser.print_help()