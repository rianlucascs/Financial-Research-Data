from os.path import join
from os import listdir
from pathlib import Path
import logging
from json import load
from pandas import read_csv
from src.shared.context import PipelineContext
from src.shared.checkpoint_contract import build_checkpoint_payload
from src.shared.checkpoint_values import (
    STATUS_SUCCESSFUL,
    STATUS_FAILED,
    FAILURE_TRANSFORM_EXCEPTION,
)
from .config import (
    B3_INDICES,
    CHECKPOINT_STAGE_TRANSFORM,
    CHECKPOINT_STEP_TRANSFORM_1,
)

class TransformB3IndicesSegmentosSetoriais:

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.logger = logging.getLogger(__name__)

    def leitura_dos_dados(self, filename, raw_path):
        try:
            self.logger.info(f"Lendo arquivo: {filename}")
            df = read_csv(join(raw_path, filename), encoding='ISO-8859-1', delimiter=';', 
                          skiprows=1, skipfooter=2, na_values="NaN", on_bad_lines='warn', 
                          engine='python').reset_index()
            df.columns = ['Código', 'Ação', 'Tipo', 'Qtde. Teórica', 'Part. (%)', '']
            df = df.iloc[:, :-1]  # Remove a última coluna
            self.logger.info(f"Arquivo {filename} lido com sucesso. {len(df)} linhas.")
            return df
        except Exception as e:
            self.logger.error(f"Erro ao ler {filename}: {e}", exc_info=True)
            raise

    def _checkpoint_transform(self, ctx, *, step, indice, filename, input_path, output_path,
                              status, failure_point=None, processed_rows=None, extra=None):
        checkpoint = build_checkpoint_payload(
            pipeline=self.pipeline,
            stage=CHECKPOINT_STAGE_TRANSFORM,
            step=step,
            status=status,
            run_id=getattr(ctx, "run_id", None),
            environment=getattr(ctx, "env", None),
            failure_point=failure_point,
            extra={
                "indice": indice,
                "input_file": filename,
                "input_mtime": input_path.stat().st_mtime if input_path.exists() else None,
                "output_file": output_path.name,
                "output_exists": output_path.exists(),
                "processed_rows": processed_rows,
            },
        )
        if extra:
            checkpoint.update(extra)
        return checkpoint

    def _verificacao_final_transform(self, processed_path, step):
        """Verifica no fim da execução se todos os índices possuem arquivo processado."""
        try:
            files = [f for f in processed_path.iterdir() if f.is_file()]

            if not files:
                self.logger.error("Verificação final do transform: nenhum arquivo encontrado no diretório processed.")
                self.logger.error(f"Índices esperados: {B3_INDICES}")
                return False

            indices_encontrados = []
            indices_faltantes = []

            for indice in B3_INDICES:
                expected_file = processed_path / f"{indice}.csv"
                if expected_file.exists():
                    indices_encontrados.append(indice)
                else:
                    indices_faltantes.append(indice)

            self.logger.info(
                f"Verificação final do {step} concluída: {len(indices_encontrados)}/{len(B3_INDICES)} índices processados."
            )

            if indices_faltantes:
                self.logger.warning(f"Índices sem arquivo processado: {indices_faltantes}")
                return False

            self.logger.info("Todos os índices de B3_INDICES possuem arquivo processado.")
            return True
        except Exception as e:
            self.logger.error(f"Erro na verificação final do transform ({step}): {e}")
            return False

    def transform_1(self, ctx=None):

        step = CHECKPOINT_STEP_TRANSFORM_1

        if ctx is None:
            ctx = PipelineContext()

        raw_path, processed_path = ctx.prepare_transform_paths(self.pipeline, step)

        raw_files = listdir(raw_path)
        self.logger.info(f"Encontrados {len(raw_files)} arquivos em {raw_path}")

        for filename in raw_files:

            indice = None

            # identificar índice com base no nome do arquivo
            for indice in B3_INDICES:
                if indice in filename:
                    break

            if indice is None or indice not in filename:
                self.logger.warning(f"Arquivo ignorado (índice não reconhecido): {filename}")
                continue

            input_path = Path(raw_path) / filename
            output_path = Path(processed_path) / f'{indice}.csv'
            ck_file = ctx.checkpoint_file(self.pipeline, CHECKPOINT_STAGE_TRANSFORM, step, filename)

            # verificar checkpoint para esse arquivo
            try:
                if ck_file.exists() and output_path.exists():
                    with open(ck_file, "r", encoding="utf-8") as fp:
                        checkpoint_data = load(fp)

                    if (
                        checkpoint_data.get("status") == STATUS_SUCCESSFUL # verificar status do checkpoint
                        and checkpoint_data.get("input_file") == filename # verificar nome do arquivo
                        and checkpoint_data.get("output_file") == output_path.name # verificar nome do arquivo de saída
                    ):
                        self.logger.info(f"Pular transform_1 para {filename} (checkpoint válido)")
                        continue
            except Exception:
                pass

            try:
                self.logger.info(f"Transformando {filename}...")
                df = self.leitura_dos_dados(filename, raw_path)

                # salvar arquivo transformado
                df.to_csv(
                    output_path,
                    index=False, encoding='utf-8'
                )
                self.logger.info(f"Arquivo transformado salvo em: {output_path}")

                # gravar checkpoint
                try:
                    ctx.write_checkpoint(
                        self.pipeline,
                        CHECKPOINT_STAGE_TRANSFORM,
                        step,
                        filename,
                        self._checkpoint_transform(
                            ctx,
                            step=step,
                            indice=indice,
                            filename=filename,
                            input_path=input_path,
                            output_path=output_path,
                            status=STATUS_SUCCESSFUL,
                            failure_point=None,
                            processed_rows=int(len(df)),
                        ),
                    )

                    self.logger.info(f"Checkpoint gravado para {filename}")
                    
                except Exception as e:
                    self.logger.exception(f"Falha ao gravar checkpoint para {filename}: {e}")
                    
            except Exception as e:
                try:
                    ctx.write_checkpoint(
                        self.pipeline,
                        CHECKPOINT_STAGE_TRANSFORM,
                        step,
                        filename,
                        self._checkpoint_transform(
                            ctx,
                            step=step,
                            indice=indice,
                            filename=filename,
                            input_path=input_path,
                            output_path=output_path,
                            status=STATUS_FAILED,
                            failure_point=FAILURE_TRANSFORM_EXCEPTION,
                            processed_rows=None,
                        ),
                    )
                except Exception:
                    pass
                self.logger.error(f"Erro ao transformar {filename}: {e}", exc_info=True)

        self._verificacao_final_transform(processed_path, step)

    def main(self, ctx=None):
        
        if ctx is None:
            ctx = PipelineContext()

        # prefer context logger when available
        self.logger = getattr(ctx, 'logger', self.logger)
        
        # atualmente só temos um transform, mas mantemos a estrutura para facilitar adição de novos steps no futuro
        self.transform_1(ctx)