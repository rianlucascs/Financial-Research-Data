import logging
import json
from src.shared.context import PipelineContext
from src.shared.checkpoint_contract import build_checkpoint_payload
from src.shared.checkpoint_values import (
    STATUS_SUCCESSFUL,
    STATUS_FAILED,
    STATUS_NO_FILE_DETECTED,
    FAILURE_EXCEPTION,
    FAILURE_FILE_DETECTION,
)
import wget
from zipfile import ZipFile
from .config import (
    CHECKPOINT_STAGE_EXTRACT,
    CHECKPOINT_STEP_DOWNLOAD_ZIP,
    CHECKPOINT_STAGE_EXTRACT_ZIP,
    DOWNLOAD_MAX_ATTEMPTS,
    URL,
    ARCHIVES_ZIP
)


class ExtractCVMFormularioInformacoesTrimestrais:
    """Download e extração de formulários de informações trimestrais da CVM.
    
    Realiza o download de arquivos ZIP contendo demonstrações financeiras
    trimestrais (ITRS) do site da CVM, extrai os arquivos CSV e organiza
    em estrutura de diretórios intermdiários com gerenciamento de checkpoints.
    """

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def _gravar_checkpoint_download(self, filename, status, failure_point, attempts, ctx):
        try:
            payload = build_checkpoint_payload(
                pipeline=self.pipeline,
                stage=CHECKPOINT_STAGE_EXTRACT,
                step=CHECKPOINT_STEP_DOWNLOAD_ZIP,
                status=status,
                run_id=ctx.run_id,
                environment=ctx.env,
                failure_point=failure_point,
                source="CVM",
                extra={
                    "filename": filename,
                    "attempts": attempts,
                },
            )
            ctx.write_checkpoint(
                self.pipeline,
                CHECKPOINT_STAGE_EXTRACT,
                CHECKPOINT_STEP_DOWNLOAD_ZIP,
                filename,
                payload,
            )
            return True
        except Exception as e:
            self.logger.exception(f"Falha ao gravar checkpoint de download para '{filename}': {e}")
            return False

    def _gravar_checkpoint_extract(self, filename, status, failure_point, attempts, extracted_files, ctx):
        try:
            payload = build_checkpoint_payload(
                pipeline=self.pipeline,
                stage=CHECKPOINT_STAGE_EXTRACT,
                step=CHECKPOINT_STAGE_EXTRACT_ZIP,
                status=status,
                run_id=ctx.run_id,
                environment=ctx.env,
                failure_point=failure_point,
                source="CVM",
                extra={
                    "filename": filename,
                    "attempts": attempts,
                    "extracted_files": extracted_files,
                },
            )
            ctx.write_checkpoint(
                self.pipeline,
                CHECKPOINT_STAGE_EXTRACT,
                CHECKPOINT_STAGE_EXTRACT_ZIP,
                filename,
                payload,
            )
            return True
        except Exception as e:
            self.logger.exception(f"Falha ao gravar checkpoint de extração para '{filename}': {e}")
            return False

    def _deve_fazer_download_zip_file(self, filename, ctx):
        try:
            checkpoint_file = ctx.checkpoint_file(
                self.pipeline,
                CHECKPOINT_STAGE_EXTRACT,
                CHECKPOINT_STEP_DOWNLOAD_ZIP,
                filename,
            )

            path_file = ctx.path_raw(self.pipeline, "zip") / filename

            # se ambos o checkpoint e o arquivo existirem, assumimos que o download foi bem-sucedido anteriormente e pulamos
            if not checkpoint_file.exists() or not path_file.exists():
                return True, "checkpoint_ou_arquivo_nao_existe"

            # Ambos arquivos exitem, vamos ler o checkpoint para entender o status do download

            with open(checkpoint_file, "r", encoding="utf-8") as fp:
                checkpoint = json.load(fp)

            status = checkpoint.get("status")
            failure_point = checkpoint.get("failure_point")

            if status == STATUS_SUCCESSFUL and failure_point is None and path_file.exists():
                self.logger.info(f"Checkpoint anterior bem-sucedido para '{filename}'. Pulando download.")
                return False, "ja_existe_sucesso"

            if status == STATUS_FAILED:
                self.logger.info(f"Checkpoint anterior falhou para '{filename}'. Reprocessando download.")
                return True, "falha_anterior"
            
            if failure_point != None:
                self.logger.info(f"Checkpoint anterior para '{filename}' falhou no ponto '{failure_point}'. Reprocessando download.")
                return True, f"falha_no_ponto_{failure_point}"

            return True, "status_desconhecido"
        
        except Exception as e:
            self.logger.error(f"Erro ao ler checkpoint de '{filename}': {e}")

            return True, "erro_leitura_checkpoint"

    def _download_zip_file(self, filename, raw_path_zip):
        url = f"{URL}{filename}"
        output_path = f"{raw_path_zip}/{filename}"
        try:
            result = wget.download(url, out=output_path, bar=False)
            return result
        
        except Exception as e:
            self.logger.error(f"Erro ao baixar o arquivo '{filename}': {e}")
            return None

    def _deve_fazer_extract_zip_file(self, filename, ctx):
        try:
            raw_path_zip = ctx.path_raw(self.pipeline, "zip")
            raw_path_csv = ctx.path_raw(self.pipeline, "csv")
            zip_file_path = raw_path_zip / filename

            # se o arquivo ZIP não existir, não há o que extrair - precisamos do arquivo para prosseguir, então retornamos que deve fazer (tentando extrair sem o ZIP resultará em erro, mas isso será tratado na função de extração e registrado no checkpoint)
            if not zip_file_path.exists():
                return True, "zip_nao_encontrado"

            with ZipFile(zip_file_path, "r") as zip_ref:
                arquivos_no_zip = [nome for nome in zip_ref.namelist() if nome and not nome.endswith("/")]

            # se o ZIP não contiver arquivos ou todos os arquivos já existirem na pasta de destino, podemos pular a extração
            if arquivos_no_zip:
                arquivos_faltantes = [
                    nome for nome in arquivos_no_zip
                    if not (raw_path_csv / nome).exists()
                ]
                

                if not arquivos_faltantes:
                    self.logger.info(
                        f"Todos os arquivos de '{filename}' já existem em raw/csv. Pulando extração."
                    )
                    return False, "arquivos_ja_extraidos"

            checkpoint_file = ctx.checkpoint_file(
                self.pipeline,
                CHECKPOINT_STAGE_EXTRACT,
                CHECKPOINT_STAGE_EXTRACT_ZIP,
                filename,
            )

            # se o checkpoint não existir, precisamos extrair (assumindo que o arquivo ZIP existe, o que foi verificado anteriormente)
            if not checkpoint_file.exists():
                return True, "checkpoint_nao_existe"

            with open(checkpoint_file, "r", encoding="utf-8") as fp:
                checkpoint = json.load(fp)

            status = checkpoint.get("status")
            failure_point = checkpoint.get("failure_point")

            if status == STATUS_SUCCESSFUL and failure_point is None:
                return False, "ja_existe_sucesso"

            return True, "falha_ou_status_desconhecido"
        
        except Exception as e:
            self.logger.error(f"Erro ao ler checkpoint de extração para '{filename}': {e}")
            return True, "erro_leitura_checkpoint"

    def _limpar_arquivo_anterior_download_zip_file(self, filename, ctx):
        """Remove arquivo ZIP anterior para refazer download limpo.

        Retorna: bool
            - True: arquivo removido ou não existia
            - False: erro ao tentar remover
        """
        try:
            raw_path_zip = ctx.path_raw(self.pipeline, "zip")
            checkpoint_file = ctx.checkpoint_file(
                self.pipeline,
                CHECKPOINT_STAGE_EXTRACT,
                CHECKPOINT_STEP_DOWNLOAD_ZIP,
                filename,
            )

            arquivo_anterior = filename

            if checkpoint_file.exists():
                with open(checkpoint_file, "r", encoding="utf-8") as fp:
                    checkpoint = json.load(fp)
                arquivo_anterior = checkpoint.get("filename") or filename

            arquivo_path = raw_path_zip / arquivo_anterior

            if arquivo_path.exists():
                arquivo_path.unlink()
                self.logger.info(f"Arquivo anterior removido: {arquivo_anterior}")
            else:
                self.logger.debug(f"Arquivo anterior não encontrado para remoção: {arquivo_anterior}")

            return True

        except Exception as e:
            self.logger.error(f"Erro ao limpar arquivo anterior '{filename}': {e}")
            return False

    def _extract_zip_file(self, filename, raw_path_zip, raw_path_csv):
        zip_path = f"{raw_path_zip}/{filename}"
        try:
            with ZipFile(zip_path, 'r') as zip_ref:
                extracted_files = zip_ref.namelist()
                zip_ref.extractall(raw_path_csv)
                self.logger.info(f"Arquivo '{filename}' extraído com sucesso.")
                return True, extracted_files

        except Exception as e:
            self.logger.error(f"Erro ao extrair o arquivo '{filename}': {e}")
            return False, []
        
    def _atualiza_ultimo_download_zip_file(self, filename, ctx):

        # sempre apagar o ultimo arquivo para garantir que estamos baixando a versão mais recente, já que a CVM pode atualizar o arquivo mantendo o mesmo nome
        ultimo = ARCHIVES_ZIP[-1]
        penultimo = ARCHIVES_ZIP[-2]
        position = 'ultimo' if filename == ultimo else 'penultimo' if filename == penultimo else 'desconhecido'

        if (ultimo != filename) and (penultimo != filename):
            return False

        try:
            raw_path_zip = ctx.path_raw(self.pipeline, "zip")
            zip_file_path = raw_path_zip / filename

            if zip_file_path.exists():
                zip_file_path.unlink()
                self.logger.info(f"Arquivo ZIP removido ({position}): {filename}")
                return True

            self.logger.info(f"Arquivo ZIP não encontrado para remoção ({position}): {filename}")
            return False

        except Exception as e:
            self.logger.error(f"Erro ao remover {position} arquivo ZIP '{filename}': {e}")
            return False

    def _atualiza_ultimo_extract_zip_file(self, filename, ctx):

        ultimo = ARCHIVES_ZIP[-1]
        penultimo = ARCHIVES_ZIP[-2]
        position = 'ultimo' if filename == ultimo else 'penultimo' if filename == penultimo else 'desconhecido'

        if (ultimo != filename) and (penultimo != filename):
            return False

        try:
            raw_path_zip = ctx.path_raw(self.pipeline, "zip")
            raw_path_csv = ctx.path_raw(self.pipeline, "csv")
            zip_file_path = raw_path_zip / filename

            if not zip_file_path.exists():
                self.logger.info(f"Arquivo ZIP não encontrado para atualização de extração ({position}): {filename}")
                return True

            with ZipFile(zip_file_path, "r") as zip_ref:
                arquivos_no_zip = [nome for nome in zip_ref.namelist() if nome and not nome.endswith("/")]

            arquivos_removidos = []
            for nome in arquivos_no_zip:
                arquivo_csv_path = raw_path_csv / nome
                if arquivo_csv_path.exists():
                    arquivo_csv_path.unlink()
                    arquivos_removidos.append(nome)

            if arquivos_removidos:
                self.logger.info(
                    f"Arquivos CSV removidos para atualização do {position} ZIP '{filename}': {arquivos_removidos}"
                )
                return True

            self.logger.info(f"Nenhum arquivo CSV anterior para remover do {position} ZIP '{filename}'.")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao atualizar extração do {position} arquivo ZIP '{filename}': {e}")
            return False

    # == ETAPA PRINCIPAL DO PIPELINE ==

    def _run_download_zip_file(self, ctx=None):

        if ctx is None:
            ctx = PipelineContext()

        # prefira o logger do contexto quando disponível
        self.logger = getattr(ctx, 'logger', self.logger)

        raw_path_zip = ctx.prepare_raw_path(self.pipeline, 'zip')
        
        # faça o download
        for filename in ARCHIVES_ZIP:

            self._atualiza_ultimo_download_zip_file(filename, ctx)

            deve_fazer, motivo = self._deve_fazer_download_zip_file(filename, ctx)
            if not deve_fazer:
                self.logger.info(f"Pulando '{filename}': {motivo}")
                continue

            self._limpar_arquivo_anterior_download_zip_file(filename, ctx)
            
            tentativas = 0
            max_tentativas = DOWNLOAD_MAX_ATTEMPTS

            while tentativas < max_tentativas:
                
                # tente baixar o arquivo ZIP
                result_download = self._download_zip_file(filename, raw_path_zip)

                # se o download falhar, incremente as tentativas e tente novamente
                if not result_download:
                    tentativas += 1
                    self.logger.warning(f"Tentativa {tentativas} de {max_tentativas} para baixar '{filename}'")
                    continue # tente novamente
                
                else:
                    break # se o download for bem-sucedido, saia do loop de tentativas
            
            # se o download falhou após o número máximo de tentativas, registre um erro e continue para o próximo arquivo
            if not result_download:
                self.logger.error(f"Falha ao baixar '{filename}' após {max_tentativas} tentativas. Pulando para o próximo arquivo.")
                self._gravar_checkpoint_download(
                    filename=filename,
                    status=STATUS_FAILED,
                    failure_point=FAILURE_EXCEPTION,
                    attempts=tentativas,
                    ctx=ctx,
                )
                continue

            else:
                # se o download for bem-sucedido, salve o checkpoint
                self._gravar_checkpoint_download(
                    filename=filename,
                    status=STATUS_SUCCESSFUL,
                    failure_point=None,
                    attempts=tentativas + 1,
                    ctx=ctx,
                )

            self.logger.info(f"Download do arquivo '{filename}' concluído com sucesso em {tentativas + 1} tentativas.")

    def _run_extract_zip_file(self, ctx=None):

        if ctx is None:
            ctx = PipelineContext()

        self.logger = getattr(ctx, 'logger', self.logger)

        raw_path_zip = ctx.path_raw(self.pipeline, "zip")
        raw_path_csv = ctx.prepare_raw_path(self.pipeline, "csv")

        for filename in ARCHIVES_ZIP:

            # atualiza o arquivo ZIP mais recente, removendo o arquivo CSV extraído anteriormente para garantir que a extração 
            # seja refeita do zero, já que a CVM pode atualizar o arquivo mantendo o mesmo nome

            result_atualiza_ultimo = self._atualiza_ultimo_extract_zip_file(filename, ctx)

            deve_fazer, motivo = self._deve_fazer_extract_zip_file(filename, ctx)
            
            # Aqui eu faço de qualquer forma, eu atualizar, pois são o ultimo e o penultimo
            if not result_atualiza_ultimo:

                # Realmente verifico se deve fazer
                if not deve_fazer:
                    self.logger.info(f"Pulando extração de '{filename}': {motivo}")
                    continue
                
                # Se não encontrado eu não extraio 
                if motivo == "zip_nao_encontrado":
                    self.logger.warning(f"Arquivo ZIP '{filename}' não encontrado para extração. Verifique se o download foi concluído com sucesso.")
                    self._gravar_checkpoint_extract(
                        filename=filename,
                        status=STATUS_NO_FILE_DETECTED,
                        failure_point=FAILURE_FILE_DETECTION,
                        attempts=1,
                        extracted_files=[],
                        ctx=ctx,
                    )
                    continue

            zip_file_path = raw_path_zip / filename

            if zip_file_path.exists():
                sucesso, extracted_files = self._extract_zip_file(filename, raw_path_zip, raw_path_csv)
                if sucesso:
                    self._gravar_checkpoint_extract(
                        filename=filename,
                        status=STATUS_SUCCESSFUL,
                        failure_point=None,
                        attempts=1,
                        extracted_files=extracted_files,
                        ctx=ctx,
                    )

                else:
                    self._gravar_checkpoint_extract(
                        filename=filename,
                        status=STATUS_FAILED,
                        failure_point=FAILURE_EXCEPTION,
                        attempts=1,
                        extracted_files=extracted_files,
                        ctx=ctx,
                    )

            else:
                self.logger.warning(f"Arquivo ZIP '{filename}' não encontrado para extração. Verifique se o download foi concluído com sucesso.")
                self._gravar_checkpoint_extract(
                    filename=filename,
                    status=STATUS_NO_FILE_DETECTED,
                    failure_point=FAILURE_FILE_DETECTION,
                    attempts=1,
                    extracted_files=[],
                    ctx=ctx,
                )

    def main(self, ctx=None):
        if ctx is None:
            ctx = PipelineContext()

        self._run_download_zip_file(ctx)
        self._run_extract_zip_file(ctx) 