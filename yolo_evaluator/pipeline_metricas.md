# Pipeline Modular de Avaliação Quantitativa de Reconstruções 3D (`yolo_evaluator`)

Este módulo implementa um framework automatizado e extensível para avaliar a qualidade geométrica, topológica e visual de reconstruções 3D projetadas em vistas 2D, comparando renderizações sintéticas diretamente contra fotografias reais (*Ground Truth*) capturadas por múltiplas câmeras (padrão `1x` e grande-angular `uw`).

---

## 1. Arquitetura do Módulo

O sistema utiliza o padrão **Strategy + Registry** desacoplado, permitindo adicionar novas métricas isoladas sem alterar o núcleo de extração ou o orquestrador:

```text
yolo_evaluator/
├── run_metrics.py                 # Orquestrador CLI, consolidador estatístico e exportador CSV
├── unique_pipeline.py             # Treinamento YOLOv8, geração de labels e detector base
├── core/
│   ├── __init__.py
│   └── extractor.py               # Extrator compartilhado YOLO + SAM 2.1 (com prompts negativos)
├── metrics/                       # Estratégias de avaliação (descoberta automática via *_metric.py)
│   ├── __init__.py                # Registry dinâmico de classes BaseMetric
│   ├── base.py                    # Contrato BaseMetric e dataclass imutável EvaluationContext
│   ├── silhouette_metric.py       # Estratégia 1: IoU Global e Boundary F1-Score
│   ├── topology_metric.py         # Estratégia 2: Característica de Euler e IoU de Cavidades
│   ├── depth_normals_metric.py    # Estratégia 3: Coerência de Normais 2.5D (relevo interno)
│   ├── internal_edges_metric.py   # Estratégia 4: Distância de Chamfer 2D e F1 de Arestas Internas
│   └── texture_metric.py          # Estratégia 5: SSIM Mascarado e Correlação de Cor HSV
├── sam_gt/                        # Máscaras binárias Ground Truth extraídas das fotos reais
└── results_metrics.csv            # Relatório quantitativo completo por vista, câmera e modelo
```

### Fluxo de Execução
1. **Detecção e Segmentação Compartilhada (`core/extractor.py`):** Para cada vista, o modelo **YOLOv8** localiza a *bounding box* do objeto e a fornece como prompt espacial ao **SAM 2.1**, extraindo uma máscara binária precisa. Caso o Ground Truth possua cavidades internas fechadas, seus centroides são injetados como **prompts negativos (`label=0`)** para evitar o preenchimento artificial de buracos.
2. **Contexto Imutável (`EvaluationContext`):** As imagens alinhadas, máscaras binárias, *bounding boxes* e metadados de câmera são encapsulados em um objeto único em memória.
3. **Despacho para Estratégias (`metrics/*_metric.py`):** O orquestrador descobre automaticamente todas as subclasses de `BaseMetric`, executa cada estratégia sobre o contexto e agrega os resultados por **Geral**, **Câmera 1x** e **Câmera Ultrawide (UW)**.

---

## 2. Estratégias e Formulação Matemática

### 2.1. Silhueta Externa (`silhouette_metric.py`)
Avalia a fidelidade global da forma projetada e a nitidez do contorno externo:
* **IoU de Área ($\uparrow$ %):** Mede a sobreposição espacial entre a máscara real ($M_{\text{GT}}$) e a máscara renderizada ($M_{\text{pred}}$):
  $$\text{IoU} = \frac{|M_{\text{GT}} \cap M_{\text{pred}}|}{|M_{\text{GT}} \cup M_{\text{pred}}|} \times 100$$
* **Boundary F1-Score ($\uparrow$ %):** Extrai os contornos externos de 1 pixel ($B_{\text{GT}}$ e $B_{\text{pred}}$) via gradiente morfológico e calcula a média harmônica entre Precisão e Revocação dentro de um raio de tolerância $\tau = 3\text{ px}$:
  $$\text{BF1} = \frac{2 \cdot P_\tau \cdot R_\tau}{P_\tau + R_\tau} \times 100$$
  *Sensível ao arredondamento de quinas vivas causado por algoritmos de suavização de superfície (ex.: Poisson Surface Reconstruction).*

### 2.2. Topologia e Cavidades Internas (`topology_metric.py`)
Verifica se buracos vazados e componentes conectados foram preservados ou fechados indevidamente:
* **Característica de Euler ($\chi$):** Calcula $\chi = C - H$, onde $C$ é o número de componentes conectados do objeto e $H$ é o número de buracos internos isolados das bordas da imagem (com área $\ge 500\text{ px}$).
* **Erro Absoluto de Euler ($\downarrow$):** $E_\chi = |\chi_{\text{GT}} - \chi_{\text{pred}}|$ ($0.00$ indica topologia idêntica).
* **IoU de Cavidades ($\uparrow$ %):** Calcula a interseção sobre união exclusivamente sobre as máscaras de furos internos ($H_{\text{GT}}$ e $H_{\text{pred}}$).

### 2.3. Relevo Interno via Normais 2.5D (`depth_normals_metric.py`)
Detecta deformações internas, amassados ou afundamento de faces planas dentro da silhueta:
* Estima campos de vetores normais unitários $\mathbf{n} = \frac{(-G_x, -G_y, 1)}{\|(-G_x, -G_y, 1)\|}$ a partir dos gradientes de Sobel sobre a luminância suavizada.
* **Similaridade de Normais ($\uparrow$ %):** Mede o alinhamento angular médio apenas na interseção válida ($M_{\text{GT}} \cap M_{\text{pred}}$):
  $$S_{\text{norm}} = \frac{1}{|V|} \sum_{p \in V} \frac{\mathbf{n}_{\text{GT}}(p) \cdot \mathbf{n}_{\text{pred}}(p) + 1}{2} \times 100$$

### 2.4. Arestas Internas e Vincos (`internal_edges_metric.py`)
Avalia o alinhamento de dobras, vincos e detalhes internos sem interferência da borda externa:
* Aplica erosão morfológica ($9 \times 9$) na máscara antes de extrair arestas internas de Canny ($E_{\text{GT}}, E_{\text{pred}}$).
* **Distância de Chamfer 2D ($\downarrow$ px):** Média simétrica das distâncias euclidianas (via *Distance Transform*) entre os pixels de aresta:
  $$d_{\text{Chamfer}} = \frac{1}{2} \left( \frac{1}{|E_{\text{pred}}|} \sum_{p \in E_{\text{pred}}} D_{\text{GT}}(p) + \frac{1}{|E_{\text{GT}}|} \sum_{q \in E_{\text{GT}}} D_{\text{pred}}(q) \right)$$
* **Internal Edge F1 ($\uparrow$ %):** Taxa de acerto das arestas internas dentro de uma tolerância de $4\text{ px}$.

### 2.5. Aparência e Textura Mascarada (`texture_metric.py`)
Isola a qualidade da textura projetada da geometria e do fundo:
* **SSIM Interno ($\uparrow$ %):** Índice de Similaridade Estrutural calculado localmente e ponderado estritamente nos pixels da interseção $M_{\text{GT}} \cap M_{\text{pred}}$.
* **Correlação Cromática HSV ($\uparrow$ %):** Correlação normalizada entre os histogramas bidimensionais de Matiz e Saturação ($H \times S$) dentro do objeto.

---

## 3. Guia de Uso (CLI)

### Executar Avaliação Completa (Todas as Estratégias)
```bash
python yolo_evaluator/run_metrics.py \
  --real-dir ~/Pictures/Caixa \
  --proj-root ~/Pictures/Projection
```

### Executar Apenas Estratégias Específicas
```bash
python yolo_evaluator/run_metrics.py \
  --real-dir ~/Pictures/Caixa \
  --proj-root ~/Pictures/Projection \
  --only silhouette internal_edges
```

### Modo Objeto Maciço (Sem Busca por Furos Internos)
Ideal para objetos sólidos fechados onde reflexos ou adesivos na superfície não devem ser tratados como cavidades:
```bash
python yolo_evaluator/run_metrics.py \
  --real-dir ~/Pictures/Caixa \
  --proj-root ~/Pictures/Projection \
  --solid-object
```

### Gerar Máscaras Ground Truth a Partir das Fotos Reais
```bash
python yolo_evaluator/run_metrics.py \
  --real-dir ~/Pictures/Caixa \
  --generate-gt
```

---

## 4. Como Adicionar uma Nova Estratégia de Métrica

1. Crie um novo arquivo terminado em `_metric.py` dentro de `yolo_evaluator/metrics/` (ex.: `metrics/lpips_metric.py`).
2. Herde de `BaseMetric`, defina `name`, `descriptions` (usando `ClassVar`) e implemente `compute(self, ctx: EvaluationContext) -> dict[str, float]`.
3. O orquestrador `run_metrics.py` detectará, executará, tabulará e exportará a nova métrica automaticamente no CSV final.