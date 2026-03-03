from dataclasses import dataclass
from pathlib import Path
import uuid
import logging
from json import dump
from logging.handlers import RotatingFileHandler


@dataclass
class PipelineContext:
    env: str = "dev"
    run_id: str | None = None

    def __post_init__(self):
        if self.run_id is None:
            self.run_id = uuid.uuid4().hex
            
        # base paths (assume repo root is two levels up from src)
        self.repo_root = Path(__file__).resolve().parents[3]
        self.base_data = self.repo_root / "Pipelines" / "data"
        self.checkpoint_path = self.repo_root / "Pipelines" / "state" / "checkpoints"

    def path_raw(self, pipeline: str, type_file: str = None) -> Path:
        """Retorna o caminho dos dados brutos de um pipeline (ex.: 'csv')."""
        if type_file:
            return self.base_data / pipeline / "raw" / type_file
        return self.base_data / pipeline / "raw"

    def path_interim(self, pipeline: str) -> Path:
        """Retorna o caminho dos dados intermediários de um pipeline."""
        return self.base_data / pipeline / "interim"

    def path_processed(self, pipeline: str, process: str) -> Path:
        """Retorna o caminho dos dados processados de um pipeline (ex.: 'transform_1')."""
        return self.base_data / pipeline / "processed" / process

    def prepare_raw_path(self, pipeline: str, type_file: str = None) -> Path:
        """Retorna o caminho raw e garante que ele exista."""
        raw_path = self.path_raw(pipeline, type_file)
        raw_path.mkdir(parents=True, exist_ok=True)
        return raw_path

    def prepare_transform_paths(self, pipeline: str, process: str) -> tuple[Path, Path]:
        """Retorna caminhos raw/processed para um transform e garante que processed exista."""
        raw_path = self.path_raw(pipeline)
        processed_path = self.path_processed(pipeline, process)
        processed_path.mkdir(parents=True, exist_ok=True)
        return raw_path, processed_path

    def checkpoint_dir(self, pipeline: str, stage: str, step: str) -> Path:
        """Retorna (e cria) o diretório de checkpoint de um estágio/step do pipeline."""
        path = self.checkpoint_path / pipeline / stage / step
        path.mkdir(parents=True, exist_ok=True)
        return path

    def checkpoint_file(self, pipeline: str, stage: str, step: str, key: str) -> Path:
        """Retorna o caminho do arquivo de checkpoint para uma determinada chave."""
        return self.checkpoint_dir(pipeline, stage, step) / f"{key}.json"

    def write_checkpoint(self, pipeline: str, stage: str, step: str, key: str, data: dict):
        """Persiste o payload do checkpoint de forma atômica para evitar gravações parciais."""
        ck_file = self.checkpoint_file(pipeline, stage, step, key)
        tmp_file = ck_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as fp:
            dump(data, fp, ensure_ascii=False, indent=4)
        tmp_file.replace(ck_file)

    def log_path(self, pipeline: str) -> Path:
        """Retorna (e cria) o caminho dos logs do pipeline para este run_id."""
        path = self.repo_root / "Pipelines" / "logs" / pipeline / self.run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def configure_logging(self, pipeline: str, level: int = logging.INFO,
                          max_bytes: int = 5 * 1024 * 1024, backup_count: int = 5):
        """Configura um logger por processo salvo no diretório data/logs.

        Define `self.logger` com o logger configurado e o retorna.
        """
        logger_name = f"pipeline.{pipeline}.{self.run_id}"
        logger = logging.getLogger(logger_name)

        # avoid re-configuring the same logger
        if getattr(logger, "_configured", False):
            self.logger = logger
            return logger

        logger.setLevel(level)

        log_dir = self.log_path(pipeline)
        file_path = log_dir / f"{pipeline}.{self.run_id}.log"

        fh = RotatingFileHandler(filename=str(file_path), maxBytes=max_bytes,
                                 backupCount=backup_count, encoding="utf-8")
        
        fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)

        logger.propagate = False
        logger._configured = True

        self.logger = logger
        return logger
