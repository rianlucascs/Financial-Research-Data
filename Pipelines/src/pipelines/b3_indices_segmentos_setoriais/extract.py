
from time import sleep
import logging
from selenium.webdriver.common.by import By
from src.utils.selenium_utils import safe_click, create_driver
from src.shared.context import PipelineContext
from src.shared.checkpoint_contract import build_checkpoint_payload
from src.shared.checkpoint_values import (
    STATUS_SUCCESSFUL,
    STATUS_FAILED,
    STATUS_NO_FILE_DETECTED,
    STATUS_DRIVER_ERROR,
    FAILURE_DRIVER_CREATION,
    FAILURE_FILE_DETECTION,
    FAILURE_VALIDATION,
    FAILURE_EXCEPTION,
    FAILURE_DOWNLOAD_BUTTON_NOT_FOUND,
)
import json
from random import randint
from .config import (
    B3_INDICES,
    CHECKPOINT_STAGE_EXTRACT,
    CHECKPOINT_STEP_DOWNLOAD,
    DOWNLOAD_MAX_ATTEMPTS,
    DOWNLOAD_SLEEP_RANGE_SECONDS,
)

class ExtractB3IndicesSegmentosSetoriais:

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def _detectar_arquivo_baixado(self, raw_path):
        """Detecta o arquivo mais recentemente modificado em raw_path.
        
        Retorna: tuple (filename: str, extension: str) ou (None, None) se nenhum arquivo encontrado.
        """
        try:
            files = [f for f in raw_path.iterdir() if f.is_file()]
            if not files:
                self.logger.warning(f"Nenhum arquivo encontrado em {raw_path}")
                return None, None
            
            latest = max(files, key=lambda f: f.stat().st_mtime)
            filename = latest.name
            extension = latest.suffix.lstrip('.')  # remove o ponto
            
            self.logger.info(f"Arquivo detectado: {filename} (extensão: {extension})")
            return filename, extension
        
        except Exception as e:
            self.logger.error(f"Erro ao detectar arquivo em {raw_path}: {e}")
            return None, None

    def _validar_arquivo(self, raw_path, filename, indice):

        """Valida o conteúdo do arquivo baixado (exemplo: verificar se CSV tem colunas esperadas).
        
        Retorna: str "successful" se válido, ou "failed" se inválido.
        """
        try:
            file_path = raw_path / filename

            # validações básicas: arquivo existe, não está vazio, nome contém o índice
            if not file_path.exists():
                self.logger.error(f"Arquivo para validação não encontrado: {file_path}")
                return STATUS_FAILED
            
            # verificar se arquivo está vazio
            if file_path.stat().st_size == 0:
                self.logger.error(f"Arquivo vazio detectado: {file_path}")
                return STATUS_FAILED
            
            # verificar se nome do arquivo contém o índice (pode ser um indicativo simples de que o conteúdo está correto)
            if indice.lower() in filename.lower():
                self.logger.info(f"Arquivo {filename} passou na validação de nome para {indice}")
                return STATUS_SUCCESSFUL
            
            # Verifica no conteúdo do arquivo
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for linha in f:
                    if indice.lower() in linha.lower():
                        self.logger.info(
                            f"Arquivo {filename} contém '{indice}' no conteúdo."
                        )
                        return STATUS_SUCCESSFUL
                
            self.logger.info(f"Arquivo validado com sucesso: {file_path}")
            return STATUS_SUCCESSFUL
        
        except Exception as e:
            self.logger.error(f"Erro ao validar arquivo {filename}: {e}")
            return STATUS_FAILED
        
    def _gravar_checkpoint(self, indice, filename, extension, status, failure_point, attempts, ctx):
        """Grava checkpoint estruturado com informações do download.
        
        failure_point: str ou None
            - None: sucesso
            - "driver_creation": falhou ao criar driver
            - "file_detection": nenhum arquivo detectado
            - "validation": falha na validação do conteúdo
            - "exception": exceção geral
        
        Retorna: bool True se gravado com sucesso, False caso contrário.
        """
        try:
            checkpoint = build_checkpoint_payload(
                pipeline=self.pipeline,
                stage=CHECKPOINT_STAGE_EXTRACT,
                step=CHECKPOINT_STEP_DOWNLOAD,
                status=status,
                run_id=ctx.run_id,
                environment=ctx.env,
                failure_point=failure_point,
                extra={
                    "indice": indice,
                    "downloaded_file": filename,
                    "downloaded_extension": extension,
                    "attempts": attempts,
                },
            )

            ctx.write_checkpoint(self.pipeline, CHECKPOINT_STAGE_EXTRACT, CHECKPOINT_STEP_DOWNLOAD, indice, checkpoint)
            
            self.logger.info(f"Checkpoint gravado para {indice}")
            return True
        except Exception as e:
            self.logger.exception(f"Falha ao gravar checkpoint para {indice}: {e}")
            return False

    def _deve_fazer_download(self, indice, ctx):
        """Verifica checkpoint e decide se deve fazer download novamente.
        
        Retorna: tuple (deve_fazer: bool, motivo: str)
            - (False, "ja_existe_sucesso"): arquivo já foi baixado com sucesso
            - (True, "checkpoint_nao_existe"): nenhum checkpoint anterior
            - (True, "arquivo_nao_encontrado"): checkpoint existe, mas arquivo não está em raw
            - (True, "falha_anterior"): falha em tentativa anterior
            - (True, "validacao_falhou"): conteúdo não estava correto
            - (True, "status_desconhecido"): status/failure_point fora dos padrões esperados
            - (True, "erro_leitura_checkpoint"): falha ao ler/parsing do checkpoint
        """
        try:
            checkpoint_file = ctx.checkpoint_file(self.pipeline, CHECKPOINT_STAGE_EXTRACT, CHECKPOINT_STEP_DOWNLOAD, indice)

            # se não existe checkpoint, fazer download
            if not checkpoint_file.exists():
                self.logger.info(f"Nenhum checkpoint anterior para {indice}")
                return True, "checkpoint_nao_existe"

            # ler checkpoint
            with open(checkpoint_file, "r", encoding="utf-8") as fp:
                checkpoint = json.load(fp)

            # verificar se o checkpoint corresponde ao índice (pode ser que exista um checkpoint para outro índice, mas não para este)
            if not checkpoint.get('indice').lower() in checkpoint.get('downloaded_file').lower():
                return True, "arquivo_nao_encontrado"

            path_file = ctx.path_raw(self.pipeline) / checkpoint.get('downloaded_file')
            
            # se arquivo não existe, precisa fazer download (pode ter sido deletado manualmente ou por limpeza automática)
            if not path_file.exists():
                self.logger.info(f'Nenhum arquivo encontrado para o índice {indice}')
                return True, "arquivo_nao_encontrado"

            status = checkpoint.get("status")
            failure_point = checkpoint.get("failure_point")
            
            # sucesso completo → pular
            if status == STATUS_SUCCESSFUL and failure_point is None:
                self.logger.info(f"Checkpoint anterior bem-sucedido para {indice}. Pulando...")
                return False, "ja_existe_sucesso"
            
            # falhas → fazer novamente
            if status == STATUS_FAILED or status == STATUS_NO_FILE_DETECTED:
                self.logger.info(f"Checkpoint anterior falhou ({failure_point}). Tentando novamente...")
                return True, "falha_anterior"
            
            # validação falhou → pode ser arquivo corrompido, tentar novamente
            if failure_point == FAILURE_VALIDATION:
                self.logger.warning(f"Validação anterior falhou para {indice}. Tentando novamente...")
                return True, "validacao_falhou"
            
            # driver error ou exception → tentar novamente
            if failure_point in [FAILURE_DRIVER_CREATION, FAILURE_EXCEPTION]:
                self.logger.info(f"Erro anterior ({failure_point}). Tentando novamente...")
                return True, "falha_anterior"
            
            # se não se encaixou em nenhum padrão, fazer download por segurança
            self.logger.warning(f"Status desconhecido para {indice}: {status}/{failure_point}. Tentando novamente...")
            return True, "status_desconhecido"
            
        except Exception as e:
            self.logger.error(f"Erro ao ler checkpoint para {indice}: {e}")
            return True, "erro_leitura_checkpoint"

    def _limpar_arquivo_anterior(self, indice, ctx):
        """Remove arquivo anterior de um índice se existir (para refazer download limpo).
        
        Retorna: bool True se arquivo foi deletado ou não existia, False se erro ao deletar.
        """
        try:
            raw_path = ctx.path_raw(self.pipeline)
            checkpoint_file = ctx.checkpoint_file(self.pipeline, CHECKPOINT_STAGE_EXTRACT, CHECKPOINT_STEP_DOWNLOAD, indice)
            
            # ler checkpoint para obter nome do arquivo anterior
            with open(checkpoint_file, "r", encoding="utf-8") as fp:
                checkpoint = json.load(fp)
            
            downloaded_file = checkpoint.get("downloaded_file") 
            
            # tentar deletar arquivo
            arquivo_path = raw_path / downloaded_file
            if arquivo_path.exists():
                try:
                    arquivo_path.unlink()
                    self.logger.info(f"Arquivo anterior deletado: {downloaded_file}")
                    return True
                
                except Exception as e:
                    self.logger.error(f"Erro ao deletar arquivo anterior {downloaded_file}: {e}")
                    return False
                
            else:
                self.logger.debug(f"Arquivo anterior não encontrado: {downloaded_file}")
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao limpar arquivo anterior para {indice}: {e}")
            return False

    def _arquivo_corresponde_indice(self, file_path, indice):
        """Verifica se um arquivo corresponde ao índice pelo nome ou pelo conteúdo."""
        try:
            if indice.lower() in file_path.name.lower():
                return True

            with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
                for linha in fp:
                    if indice.lower() in linha.lower():
                        return True
                    
            return False
        
        except Exception:
            return False

    def _verificacao_final_downloads(self, raw_path):
        """Verifica no fim da execução se todos os índices possuem arquivo correspondente."""
        try:
            files = [f for f in raw_path.iterdir() if f.is_file()]

            if not files:
                self.logger.error("Verificação final: nenhum arquivo encontrado no diretório raw.")
                self.logger.error(f"Índices esperados: {B3_INDICES}")
                return False

            indices_encontrados = []
            indices_faltantes = []

            for indice in B3_INDICES:
                encontrado = any(self._arquivo_corresponde_indice(file_path, indice) for file_path in files)
                if encontrado:
                    indices_encontrados.append(indice)
                else:
                    indices_faltantes.append(indice)

            self.logger.info(
                f"Verificação final concluída: {len(indices_encontrados)}/{len(B3_INDICES)} índices encontrados."
            )

            if indices_faltantes:
                self.logger.warning(f"Índices sem arquivo correspondente: {indices_faltantes}")
                return False

            self.logger.info("Todos os índices de B3_INDICES possuem arquivo correspondente.")
            return True
        except Exception as e:
            self.logger.error(f"Erro na verificação final dos downloads: {e}")
            return False
            
    def main(self, ctx=None):
        
        if ctx is None:
            ctx = PipelineContext()

        # prefira o logger do contexto quando disponível
        self.logger = getattr(ctx, 'logger', self.logger)

        raw_path = ctx.prepare_raw_path(self.pipeline)
        
        for indice in B3_INDICES:
            
            filename = None
            extension = None
            status = STATUS_FAILED
            failure_point = None

            tentativas = 0
            max_tentativas = DOWNLOAD_MAX_ATTEMPTS

            sleep_time = randint(*DOWNLOAD_SLEEP_RANGE_SECONDS)

            while tentativas < max_tentativas:

                # verificar se deve fazer download
                deve_fazer, motivo = self._deve_fazer_download(indice, ctx)
                if not deve_fazer:
                    self.logger.info(f"Pulando {indice}: {motivo}")
                    break # passar para próximo índice
                
                # se vai refazer download, limpar arquivo anterior
                self._limpar_arquivo_anterior(indice, ctx)

                try:
                    self.logger.info(f"Iniciando download para {indice}... (motivo: {motivo})")
                    self.logger.info(f"Caminho de download (raw_path): {raw_path}")
                    
                    self.driver = create_driver(
                        download_path=str(raw_path), 
                        headless="--disable-gpu", # sem abrir janela
                        incognito=False, # anonimo desativado para evitar bloqueios (pode ser testado com True se necessário)
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ) 
                    if self.driver is None:
                        self.logger.error(f"Web driver falhou para {indice}")
                        self._gravar_checkpoint(indice, filename, extension, STATUS_DRIVER_ERROR, FAILURE_DRIVER_CREATION, tentativas + 1, ctx)
                        tentativas += 1 # evita loop infinito em caso de falhas repetidas
                        continue # tentar novamente (pode ser falha temporária na criação do driver)
                    
                    self.logger.info(f"Web driver criado com sucesso.")
                    
                    url = f'https://sistemaswebb3-listados.b3.com.br/indexPage/day/{indice}?language=pt-br'
                    self.logger.info(f"Acessando URL: {url}")
                    self.driver.get(url)

                    sleep(sleep_time)

                    self.logger.info(f"Clicando em download para {indice}...")

                    safe_return = safe_click(self.driver, 'Download', by=By.LINK_TEXT)
                    
                    if safe_return is False:
                        self.logger.error(f"Botão de download não encontrado para {indice}")
                        self._gravar_checkpoint(indice, filename, extension, STATUS_FAILED, FAILURE_DOWNLOAD_BUTTON_NOT_FOUND, tentativas + 1, ctx)
                        self.driver.quit()
                        tentativas += 1 # evita loop infinito em caso de falhas repetidas
                        continue # tentar novamente (pode ser falha temporária de carregamento da página)

                    sleep(sleep_time)

                    self.logger.info(f"Aguardando conclusão do download ({sleep_time}s) para {indice}...")

                    self.driver.close()

                    # detectar arquivo baixado
                    filename, extension = self._detectar_arquivo_baixado(raw_path)
                    
                    if filename is None:
                        self.logger.error(f"Nenhum arquivo detectado após download de {indice}")
                        status = STATUS_NO_FILE_DETECTED
                        failure_point = FAILURE_FILE_DETECTION
                        self._gravar_checkpoint(indice, filename, extension, status, failure_point, tentativas + 1, ctx)
                        tentativas += 1 # evita loop infinito em caso de falhas repetidas
                        continue # tentar novamente (pode ser falha temporária de download ou detecção do arquivo)

                    self.logger.info(f"Download realizado com sucesso: {indice}")

                    # validar conteúdo do arquivo
                    status = self._validar_arquivo(raw_path, filename, indice)
                    failure_point = None if status == STATUS_SUCCESSFUL else FAILURE_VALIDATION

                    # gravar checkpoint com status final
                    self._gravar_checkpoint(indice, filename, extension, status, failure_point, tentativas + 1, ctx)
                    
                    self.logger.info(f"Extração finalizada para {indice} com status: {status}")

                    break # sucesso, sair do loop de tentativas

                except Exception as e:
                    
                    self.logger.error(f"Erro durante download de {indice}: {e}", exc_info=True)
                    tentativas += 1
                    self._gravar_checkpoint(indice, filename, extension, STATUS_FAILED, FAILURE_EXCEPTION, tentativas, ctx)
                    
                    if self.driver:
                        try:
                            self.driver.quit()
                        except:
                            pass

        self._verificacao_final_downloads(raw_path)

