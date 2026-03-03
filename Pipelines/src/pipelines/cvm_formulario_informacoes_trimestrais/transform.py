 
import logging

from pandas import DataFrame, concat, read_csv
from datetime import date

from src.shared.context import PipelineContext
from src.shared.checkpoint_contract import build_checkpoint_payload
from src.shared.checkpoint_values import STATUS_SUCCESSFUL, STATUS_FAILED, FAILURE_PROCESSED_EXCEPTION
from .config import (
    ITRS,
    CHECKPOINT_STAGE_PROCESSED,
    CHECKPOINT_STEP_PROCESSED_1
)

class TransformCVMFormularioInformacoesTrimestrais:

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.logger = logging.getLogger(__name__)

    def _gravar_checkpoint(self, itr_name, status, failure_point, ctx):
        payload = build_checkpoint_payload(
            pipeline=self.pipeline,
            stage=CHECKPOINT_STAGE_PROCESSED,
            step=CHECKPOINT_STEP_PROCESSED_1,
            status=status,
            run_id=ctx.run_id,
            environment=ctx.env,
            failure_point=failure_point,
            source="CVM",
            extra={"itr_name": itr_name},
        )
        ctx.write_checkpoint(
            self.pipeline,
            CHECKPOINT_STAGE_PROCESSED,
            CHECKPOINT_STEP_PROCESSED_1,
            itr_name,
            payload,
        )

    def _transform_1(self, ctx=None):
        """Concatena os arquivos CSV anuais de cada demonstração e salva um arquivo consolidado."""

        year_now = date.today().year

        for itr_name in ITRS:
            try:
                df = DataFrame()

                filename = f'itr_cia_aberta_{itr_name}_2011-{year_now}.csv'
                raw_path, interim_path = ctx.prepare_interim_path(self.pipeline)
                path_iterim_csv = interim_path / filename

                if not path_iterim_csv.exists():
                    for for_year in range(2011, year_now + 1):

                        try:

                            name_raw_csv = f'itr_cia_aberta_{itr_name}_{for_year}.csv'
                            path_raw_csv = raw_path / 'csv' / name_raw_csv

                            df_raw_csv = read_csv(path_raw_csv, sep=";", decimal=",", encoding="iso-8859-1")

                        except Exception as erro:
                            self.logger.error(f"Erro ao abrir o arquivo '{name_raw_csv}': {erro}", exc_info=True)
                            
                            continue

                        df = concat([df, df_raw_csv])

                    df.to_csv(path_iterim_csv, index=False, encoding='utf-8', mode='w')

                    self.logger.info(f"Arquivo '{filename}' criado e salvo com sucesso.")

                else:
                    self.logger.info(f"Arquivo '{filename}' já existe. Nenhuma ação necessária.")

                self._gravar_checkpoint(
                    itr_name, 
                    STATUS_SUCCESSFUL, 
                    None, 
                    ctx)
                
                self.logger.info(f'Sucesso no transform_1 para {itr_name}')

            except Exception as erro:
                self._gravar_checkpoint(
                    itr_name, 
                    STATUS_FAILED, 
                    FAILURE_PROCESSED_EXCEPTION, 
                    ctx
                )
                self.logger.error(f"Erro no transform_1 para '{itr_name}': {erro}", exc_info=True)

    def _transform_2(self, ctx=None):
        

    def main(self, ctx=None):
        
        if ctx is None:
            ctx = PipelineContext()

        self.logger = getattr(ctx, 'logger', self.logger)

        self._transform_1(ctx)