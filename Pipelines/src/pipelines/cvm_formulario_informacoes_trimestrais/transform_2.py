import logging
from pathlib import Path
from pandas import read_csv
from src.shared.checkpoint_contract import build_checkpoint_payload
from src.shared.checkpoint_values import (
    FAILURE_PROCESSED_EXCEPTION,
    FAILURE_VALIDATION,
    STATUS_FAILED,
    STATUS_SUCCESSFUL,
)
from .config import (
    CARTEIRA_INDICE_BRASIL_IBEP,
    CHECKPOINT_STAGE_PROCESSED,
    CHECKPOINT_STEP_PROCESSED_2,
)


class TransformCVMFormularioInformacoesTrimestraisStep2:
    """Filtro e separação de dados por ticker da carteira IBEP.
    
    Processa arquivos CSV consolidados de informações trimestrais,
    filtrando dados específicos para cada ativo (ticker) da carteira do
    índice Brasil IBEP e salvando os resultados em arquivos separados
    por código de empresa.
    """
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.logger = logging.getLogger(__name__)

    def _gravar_checkpoint(self, step, item_name, status, failure_point, ctx, extra=None):
        extra_payload = {"item_name": item_name}
        if extra:
            extra_payload.update(extra)

        payload = build_checkpoint_payload(
            pipeline=self.pipeline,
            stage=CHECKPOINT_STAGE_PROCESSED,
            step=step,
            status=status,
            run_id=ctx.run_id,
            environment=ctx.env,
            failure_point=failure_point,
            source="CVM",
            extra=extra_payload,
        )
        ctx.write_checkpoint(
            self.pipeline,
            CHECKPOINT_STAGE_PROCESSED,
            step,
            item_name,
            payload,
        )

    def run(self, ctx=None, desenvolviment_mode=False):
        """Processa os arquivos CSV consolidados, filtrando as informações específicas para cada ticker da carteira do índice
        Brasil IBEP e salvando os resultados em arquivos separados por ticker."""

        path_iterim = ctx.path_interim(self.pipeline)
        files_iterim = list(path_iterim.glob("*.csv"))

        path_transform_2 = ctx.path_processed(self.pipeline, CHECKPOINT_STEP_PROCESSED_2)

        for file_path in files_iterim:
            filename = file_path.name.replace(".csv", "")

            filled = []

            try:
                df = read_csv(file_path, sep=",", decimal=",", encoding="iso-8859-1")

                for ticker, info in CARTEIRA_INDICE_BRASIL_IBEP.items():

                    self.logger.info(f"Processando ticker: {ticker} no arquivo '{filename}'.")

                    codigo = ticker.replace(".SA", "")

                    ckeckpoint_key = f"{codigo}_{filename}"
                    dataname = f"{codigo}_{filename}"

                    # Cria o diretório para o código do ticker dentro do transform_2
                    path_transform_2_codigo = path_transform_2 / codigo
                    path_transform_2_codigo.mkdir(parents=True, exist_ok=True)

                
                    checkpoint_step = str(Path(CHECKPOINT_STEP_PROCESSED_2) / codigo)


                    path_transform_2_codigo_dataname = path_transform_2_codigo / f"{dataname}.csv"


                    # Em modo de desenvolvimento, se o arquivo já existir, pula o processamento para evitar sobreescrita e acelerar os testes
                    if desenvolviment_mode:

                        if path_transform_2_codigo_dataname.exists():

                            self.logger.info(f"Arquivo transformado para o ticker '{ticker}' já existe. Pulando processamento para o arquivo '{filename}'.")

                            continue
                    
                    # Antes de processar, garante que não exista um arquivo prévio para evitar sobreescrita de dados 
                    # Queremos sempre que for executado atualizar os dados, mesmo que seja para corrigir um erro anterior.
                    ctx.delete_file(path_transform_2_codigo_dataname)

                    cnpj = info["CNPJ"]
                    denom_cia = info["DENOM_CIA"]
                    cd_cvm = info["CD_CVM"]

                    cnpj_series = df["CNPJ_CIA"].astype(str).str.strip()
                    cnpj_target = str(cnpj).strip()
                    df_filter_cnpj = df.loc[cnpj_series == cnpj_target]

                    # Se não encontrar dados usando o CNPJ, tenta usar a DENOM_CIA como alternativa de filtro
                    if df_filter_cnpj.empty:

                        denom_cia_series = df["DENOM_CIA"].astype(str).str.strip()
                        denom_cia_target = str(denom_cia).strip()
                        df_filter_denom_cia = df.loc[denom_cia_series == denom_cia_target]

                        # Se ainda não encontrar dados usando a DENOM_CIA, tenta usar o CD_CVM como última alternativa de filtro
                        if df_filter_denom_cia.empty:

                            cd_cvm_series = df["CD_CVM"].astype(int)
                            cd_cvm_target = int(cd_cvm)
                            df_filter_cd_cvm = df.loc[cd_cvm_series == cd_cvm_target]

                            # Se não encontrar dados usando CD_CVM, registra falha no checkpoint e segue para o próximo ticker
                            if df_filter_cd_cvm.empty:

                                self.logger.warning(f"Nenhum dado encontrado para o ticker '{ticker}' usando (CNPJ, DENOM_CIA e CD_CVM) no arquivo '{filename}'.")

                                self._gravar_checkpoint(
                                    checkpoint_step,
                                    ckeckpoint_key,
                                    STATUS_FAILED,
                                    FAILURE_VALIDATION,
                                    ctx,
                                    extra={
                                        "filename": filename,
                                        "ticker": ticker,
                                        "CNPJ": cnpj,
                                        "DENOM_CIA": denom_cia,
                                        "CD_CVM": cd_cvm,
                                        "description": "Nenhum dado encontrado para o ticker usando (CNPJ, DENOM_CIA e CD_CVM)",
                                    },
                                )

                                filled.append(codigo)

                                continue

                            # Se encontrar dados usando o CD_CVM, salva o resultado e registra sucesso no checkpoint
                            else:

                                df_filter_cd_cvm.to_csv(path_transform_2_codigo_dataname, index=False, encoding="utf-8", mode="w")

                                self.logger.info(f"Dados encontrados para o ticker '{ticker}' usando CD_CVM no arquivo '{filename}'.")

                                self._gravar_checkpoint(
                                    checkpoint_step,
                                    ckeckpoint_key,
                                    STATUS_SUCCESSFUL,
                                    None,
                                    ctx,
                                    extra={
                                        "filename": filename,
                                        "ticker": ticker,
                                        "CNPJ": cnpj,
                                        "DENOM_CIA": denom_cia,
                                        "CD_CVM": cd_cvm,
                                        "description": "Dados encontrados para o ticker usando CD_CVM",
                                    },
                                )

                                continue
                        
                        # Se encontrar dados usando a DENOM_CIA, salva o resultado e registra sucesso no checkpoint
                        else:

                            df_filter_denom_cia.to_csv(path_transform_2_codigo_dataname, index=False, encoding="utf-8", mode="w")

                            self.logger.info(f"Dados encontrados para o ticker '{ticker}' usando DENOM_CIA no arquivo '{filename}'.")

                            self._gravar_checkpoint( 
                                checkpoint_step,
                                ckeckpoint_key,
                                STATUS_SUCCESSFUL,
                                None,
                                ctx,
                                extra={
                                    "filename": filename,
                                    "ticker": ticker,
                                    "CNPJ": cnpj,
                                    "DENOM_CIA": denom_cia,
                                    "description": "Dados encontrados para o ticker usando DENOM_CIA",
                                },
                            )
                            
                            continue

                    # Se encontrar dados usando o CNPJ, salva o resultado e registra sucesso no checkpoint
                    else:
                        df_filter_cnpj.to_csv(path_transform_2_codigo_dataname, index=False, encoding="utf-8", mode="w")

                        self.logger.info(f"Dados encontrados para o ticker '{ticker}' usando CNPJ no arquivo '{filename}'.")

                        self._gravar_checkpoint(
                            checkpoint_step,
                            ckeckpoint_key,
                            STATUS_SUCCESSFUL,
                            None,
                            ctx,
                            extra={
                                "filename": filename,
                                "ticker": ticker,
                                "CNPJ": cnpj,
                                "description": "Dados encontrados para o ticker usando CNPJ",
                            },
                        )

                        continue

                # EndFor ticker

                self.logger.info(f"Processamento do arquivo '{filename}' concluído. Filled: {filled}.")

                self._gravar_checkpoint(
                    CHECKPOINT_STEP_PROCESSED_2,
                    filename,
                    STATUS_SUCCESSFUL,
                    None,
                    ctx,
                    extra={"filename": filename, "filled": filled},
                )

            except Exception as erro:
                self._gravar_checkpoint(
                    CHECKPOINT_STEP_PROCESSED_2,
                    filename,
                    STATUS_FAILED,
                    FAILURE_PROCESSED_EXCEPTION,
                    ctx,
                    extra={"filename": filename},
                )
                self.logger.error(f"Erro no transform_2 para '{filename}': {erro}", exc_info=True)

        # EndFor file_path

        self.logger.info("Transformação concluída para todos os arquivos iterim.")
