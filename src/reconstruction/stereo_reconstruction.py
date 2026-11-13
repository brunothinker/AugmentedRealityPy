import logging
import time
from pathlib import Path

import yaml
from tqdm import tqdm

from src.reconstruction.reconstruction_utils import (
    ColmapCommandBuilder,
    copiar_configs_resources,
    limpar_arquivos_intermediarios,
    run_command,
    setup_logger,
    setup_rig,
)


def run_stereo_reconstruction(pasta_frames: Path, pasta_projeto_saida: Path, baseline_metros: float, progress_callback=None) -> bool:
    """Pipeline COLMAP Estéreo utilizando parâmetros do colmap_config.yaml."""

    pasta_projeto_saida.mkdir(parents=True, exist_ok=True)
    arquivo_log = setup_logger(pasta_projeto_saida)

    # Copia o colmap_config.yaml para a pasta do projeto e obtém o caminho de destino
    caminho_yaml_copiado = copiar_configs_resources(pasta_projeto_saida)

    # Carrega os parâmetros do YAML registrado
    config_yaml = {}
    if caminho_yaml_copiado and caminho_yaml_copiado.exists():
        with open(caminho_yaml_copiado, "r", encoding="utf-8") as f:
            config_yaml = yaml.safe_load(f) or {}

    # Definição dos caminhos
    db_path = pasta_projeto_saida / "database.db"
    pasta_esparsa = pasta_projeto_saida / "sparse"
    pasta_esparsa_rigged_init = pasta_esparsa / "0_rigged"
    pasta_esparsa_rig_final = pasta_esparsa / "rig"
    pasta_densa = pasta_projeto_saida / "dense"
    arquivo_rig = pasta_projeto_saida / "rig_config.json"

    pasta_esparsa.mkdir(exist_ok=True)
    pasta_esparsa_rigged_init.mkdir(exist_ok=True)
    pasta_esparsa_rig_final.mkdir(exist_ok=True)
    pasta_densa.mkdir(exist_ok=True)

    constructor = ColmapCommandBuilder()

    # Gera o arquivo JSON do rig
    setup_rig(arquivo_rig, baseline_metros)

    # --- DEFINIÇÃO DAS ETAPAS UNIFICANDO YAML + SOBREPOSIÇÕES ESTÉREO ---
    etapas = [
        # Etapa 1: Feature Extractor (sobrescreve flags específicas do rig)
        (constructor.build("feature_extractor", {
            **config_yaml.get("feature_extractor", {}),
            "database_path": db_path,
            "image_path": pasta_frames,
            "ImageReader.single_camera_per_folder": True,
            "ImageReader.camera_model": "OPENCV"
        }), "Extração de Features (Estéreo)"),

        # Etapa 2: Matcher
        (constructor.build("sequential_matcher", {
            **config_yaml.get("sequential_matcher", {}),
            "database_path": db_path
        }), "Matcher Sequencial"),

        # Etapa 3: Mapper
        (constructor.build("mapper", {
            **config_yaml.get("mapper", {}),
            "database_path": db_path,
            "image_path": pasta_frames,
            "output_path": pasta_esparsa
        }), "Reconstrução Esparsa (Inicial)"),

        # Etapa 4a: Rig Configurator
        (constructor.build("rig_configurator", {
            "database_path": db_path,
            "input_path": pasta_esparsa / "0",
            "rig_config_path": arquivo_rig,
            "output_path": pasta_esparsa_rigged_init
        }), "Configuração do Rig"),

        # Etapa 4b: Bundle Adjuster
        (constructor.build("bundle_adjuster", {
            "input_path": pasta_esparsa_rigged_init,
            "output_path": pasta_esparsa_rig_final,
            "BundleAdjustment.refine_rig_from_world": False,
            "BundleAdjustment.refine_sensor_from_rig": False
        }), "Ajuste de Bundle (Escala Real)"),

        # Etapa 5: Undistorter
        (constructor.build("image_undistorter", {
            **config_yaml.get("image_undistorter", {}),
            "image_path": pasta_frames,
            "input_path": pasta_esparsa_rig_final,
            "output_path": pasta_densa,
            "output_type": "COLMAP"
        }), "Retificação de Imagens"),

        # Etapa 6: Patch Match
        (constructor.build("patch_match_stereo", {
            **config_yaml.get("patch_match_stereo", {}),
            "workspace_path": pasta_densa
        }), "Estéreo Patch Match"),

        # Etapa 7: Fusion
        (constructor.build("stereo_fusion", {
            **config_yaml.get("stereo_fusion", {}),
            "workspace_path": pasta_densa,
            "output_path": pasta_densa / "modelo_fusionado.ply"
        }), "Fusão (Point Cloud)"),

        # Etapa 8: Poisson Mesher
        (constructor.build("poisson_mesher", {
            **config_yaml.get("poisson_mesher", {}),
            "input_path": pasta_densa / "modelo_fusionado.ply",
            "output_path": pasta_densa / "malha_final.ply"
        }), "Geração de Malha (Poisson)")
    ]

    etapas = etapas[8:] #Travando etapa de teste

    print(f"\n[RECONSTRUÇÃO ESTÉREO] Iniciando pipeline para: {pasta_projeto_saida.name}")
    print(f"[INFO] Baseline: {baseline_metros}m")
    print(f"[LOG] Acompanhe os detalhes técnicos em: {arquivo_log.name}\n")

    total_etapas = len(etapas)
    try:
        with tqdm(total=len(etapas), desc="Progresso Estéreo", unit="etapa", ncols=80) as barra:
            for indice, (comando, descricao) in enumerate(etapas, 1):
                barra.set_postfix_str(descricao)
                logging.info(f"--- EXECUTANDO: {comando} ---")

                if progress_callback:
                    progresso_calculado = (indice - 1) / total_etapas
                    progress_callback(progresso_calculado, f"Etapa {indice}/{total_etapas}: {descricao}")

                inicio_etapa = time.time()
                run_command(comando, progress_callback, f"Etapa {indice}/{total_etapas}: {descricao}")
                tempo_decorrido = time.time() - inicio_etapa

                tqdm.write(f"[TIMER] '{descricao}' concluída em {tempo_decorrido:.2f} segundos.")
                logging.info(f"--- TEMPO '{descricao}': {tempo_decorrido:.2f}s ---")

                if "Reconstrução Esparsa" in descricao and not (pasta_esparsa / "0").exists():
                    raise Exception("Falha no Mapper: Câmeras não conectaram.")

                if "Ajuste de Bundle" in descricao and not (pasta_esparsa_rig_final / "cameras.bin").exists():
                    raise Exception("Falha na otimização do Rig: Modelo final não gerado.")

                barra.update(1)

        limpar_arquivos_intermediarios(pasta_projeto_saida)

        if progress_callback:
            progress_callback(1.0, "Reconstrução Estéreo concluída!")
        print("\n[SUCESSO] Reconstrução Estéreo finalizada na escala real!")
        return True

    except Exception as erro:
        print(f"\n[ERRO FATAL] O pipeline estéreo falhou: {erro}")
        print(f"[INFO] Verifique o arquivo {arquivo_log.name} para mais detalhes.")
        logging.error(f"Erro fatal no pipeline estéreo: {erro}")
        return False