from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import functools
from time import sleep
from pathlib import Path
from selenium.common.exceptions import TimeoutException
from typing import List, Optional, Union, Literal, Any, Callable
from selenium.webdriver.remote.webdriver import WebDriver, WebElement

import logging

logger = logging.getLogger(__name__)

# decoradores

def retry(
    retries: int = 3,
    expect: Literal["not_none", "bool"] = "not_none",
    delay: int = 1,
    backoff: int = 1,
    raise_last: bool = False,
) -> Callable:
    """
    Decorator de retry para funções instáveis (selenium, download, scraping).
    
    Args:
        retries: Número máximo de tentativas
        expect: Tipo de sucesso esperado ('not_none' ou 'bool')
        delay: Delay inicial entre tentativas (segundos)
        backoff: Multiplicador de delay progressivo
        raise_last: Se True, levanta última exceção após todas tentativas
    
    Returns:
        Função decorada com retry automático
    """

    def decorator(func: Callable) -> Callable:

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:

            last_result = None
            last_exception = None
            current_delay = delay

            # executa tentativas
            for attempt in range(1, retries + 1):

                try:

                    # executa função
                    result = func(*args, **kwargs)
                    last_result = result

                    # sucesso se retornar True
                    if expect == "bool" and result is True:
                        return result

                    # sucesso se não for None
                    if expect == "not_none" and result is not None:
                        return result

                except Exception as e:

                    # salva último erro
                    last_exception = e

                    # log tentativa
                    logger.warning(
                        f"{func.__name__} retry {attempt}/{retries} failed: {e}"
                    )

                # delay progressivo
                if attempt < retries:
                    sleep(current_delay)
                    current_delay *= backoff

            # levanta erro final se configurado
            if raise_last and last_exception:
                raise last_exception

            # retorna último resultado
            return last_result

        return wrapper

    return decorator



def chrome_options(
    download_path: str | Path | None = None,
    *,
    headless: bool = True,
    window_size: tuple[int, int] = (1920, 1080),
    start_maximized: bool = False,
    incognito: bool = True,
    disable_notifications: bool = True,
    disable_popups: bool = True,
    disable_sandbox: bool = True,
    disable_dev_shm_usage: bool = True,
    allow_multiple_downloads: bool = True,
    enable_safe_browsing: bool = True,
    user_agent: str | None = None,
) -> Options:
    """
    Configura opções do Chrome WebDriver.
    
    Args:
        download_path: Caminho para pasta de downloads
        headless: Modo headless (sem interface gráfica)
        window_size: Resolução da janela (width, height)
        start_maximized: Iniciar maximizado
        incognito: Modo incógnito/privado
        disable_notifications: Desabilitar notificações
        disable_popups: Permitir popups
        disable_sandbox: Desabilitar sandbox (estabilidade Linux/Docker)
        disable_dev_shm_usage: Evitar erro de memória compartilhada
        allow_multiple_downloads: Permitir múltiplos downloads simultâneos
        enable_safe_browsing: Habilitar proteção contra downloads maliciosos
        user_agent: User agent customizado
    
    Returns:
        Objeto Options configurado para ChromeDriver
    """
    
    options = Options()

    args = [

        # modo headless
        "--headless=new" if headless else None,

        # resolução
        f"--window-size={window_size[0]},{window_size[1]}" if headless else None,

        # maximizado
        "--start-maximized" if start_maximized and not headless else None,

        # modo anônimo
        "--incognito" if incognito else None,

        # desativa notificações
        "--disable-notifications" if disable_notifications else None,

        # permite popups
        "--disable-popup-blocking" if disable_popups else None,

        # estabilidade linux/docker
        "--no-sandbox" if disable_sandbox else None,

        # evita erro memória
        "--disable-dev-shm-usage" if disable_dev_shm_usage else None,

        "--disable-blink-features=AutomationControlled",

        # user agent custom
        f"--user-agent={user_agent}" if user_agent else None,
    ]

    # aplica argumentos válidos
    for arg in filter(None, args):
        options.add_argument(arg)

    # configura download
    if download_path:

        # converte para Path
        path = Path(download_path).expanduser().resolve()

        prefs = {

            # pasta download
            "download.default_directory": str(path),

            # download automático
            "download.prompt_for_download": False,

            # sobrescrever
            "download.directory_upgrade": True,

            # baixar pdf
            "download.open_pdf_in_system_reader": False,

            # evita bloqueio
            "safebrowsing.enabled": enable_safe_browsing,

            # permite popup download
            "profile.default_content_settings.popups": 0,

            # múltiplos downloads
            "profile.content_settings.exceptions.automatic_downloads.*.setting":
                1 if allow_multiple_downloads else 0,
        }

        # aplica prefs
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

    # retorna options
    return options

def find(
    driver: WebDriver,
    xpath: str,
    wait: int = 10,
    all: bool = False,
    visible: bool = True,
    by: By = By.XPATH,
) -> Optional[Union[WebElement, List[WebElement]]]:
    """
    Encontra elementos no DOM com espera explícita.
    
    Args:
        driver: Instância WebDriver
        xpath: XPath ou seletor do elemento(s) a localizar
        wait: Timeout em segundos para aguardar elemento
        all: Se True, retorna todos elementos; se False, apenas um
        visible: Se True, apenas elementos visíveis; se False, qualquer um presente
        by: Tipo de seletor (By.XPATH, By.ID, By.CLASS_NAME, etc)
    
    Returns:
        WebElement, lista de WebElements, ou None/[] se não encontrado
    """
    
    if not xpath:
        logger.warning("XPath vazio fornecido para find()")
        return [] if all else None

    # define tipo de condição
    if all:

        # retorna todos elementos
        condition = ( 
            EC.visibility_of_all_elements_located 
            if visible 
            else EC.presence_of_all_elements_located
        )

    else:

        # retorna apenas um elemento
        condition = (
            EC.visibility_of_element_located
            if visible
            else EC.presence_of_element_located
        )

    try:

        # aguarda elemento(s)
        return WebDriverWait(driver, wait).until(
            condition((by, xpath))
        )

    except TimeoutException:

        # log se não encontrar
        logger.warning(f"Elemento não encontrado após {wait}s: {xpath}")

        # retorna vazio se all=True
        if all:
            return []

        return None
    
    except Exception as e:
        logger.error(f"Erro ao procurar elemento: {e}", exc_info=True)
        return [] if all else None


@retry(retries=3, expect="bool")
def safe_click(
    driver: WebDriver,
    xpath: str,
    wait: int = 10,
    by: By = By.XPATH,
) -> bool:
    """
    Realiza clique robusto com fallback JavaScript.
    
    Tenta clicar no elemento de forma normal, e se falhar, usa JavaScript.
    O decorator @retry garante até 3 tentativas com backoff.
    
    Args:
        driver: Instância WebDriver
        xpath: XPath ou seletor do elemento
        wait: Timeout em segundos para aguardar elemento clicável
        by: Tipo de seletor (By.XPATH, By.ID, By.CLASS_NAME, etc)
    
    Returns:
        True se clique bem-sucedido, False caso contrário
    """

    try:

        element = WebDriverWait(driver, wait).until(
            EC.element_to_be_clickable((by, xpath))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView(true);",
            element
        )

        element.click()
        logger.debug(f"Clique bem-sucedido (normal) em: {xpath}")
        return True

    except Exception as e:

        try:

            element = driver.find_element(by, xpath)

            driver.execute_script(
                "arguments[0].click();",
                element
            )
            logger.debug(f"Clique bem-sucedido (JavaScript) em: {xpath}")
            return True

        except Exception as e2:

            logger.warning(f"Erro ao clicar em {xpath}: {e2}")

            return False


def create_driver(
    download_path: str | Path | None = None,
    *,
    headless: bool = True,
    window_size: tuple[int, int] = (1920, 1080),
    start_maximized: bool = False,
    incognito: bool = True,
    disable_notifications: bool = True,
    disable_popups: bool = True,
    disable_sandbox: bool = True,
    disable_dev_shm_usage: bool = True,
    allow_multiple_downloads: bool = True,
    enable_safe_browsing: bool = True,
    user_agent: str | None = None,
) -> Optional[WebDriver]:
    """
    Cria instância ChromeDriver configurada.
    
    Args:
        download_path: Caminho para pasta de downloads
        headless: Se True, executa sem interface gráfica
        window_size: Resolução da janela (width, height)
        start_maximized: Iniciar maximizado
        incognito: Modo incógnito/privado
        disable_notifications: Desabilitar notificações
        disable_popups: Permitir popups
        disable_sandbox: Desabilitar sandbox (estabilidade Linux/Docker)
        disable_dev_shm_usage: Evitar erro de memória compartilhada
        allow_multiple_downloads: Permitir múltiplos downloads simultâneos
        enable_safe_browsing: Habilitar proteção contra downloads maliciosos
        user_agent: User agent customizado
    
    Returns:
        Instância WebDriver ou None se falhar na criação
    """

    try:

        service = Service(
            ChromeDriverManager().install()
        )

        driver = webdriver.Chrome(
            service=service,
            options=chrome_options(
                download_path=download_path,
                headless=headless, 
                window_size=window_size,
                start_maximized=start_maximized,
                incognito=incognito,
                disable_notifications=disable_notifications,
                disable_popups=disable_popups,
                disable_sandbox=disable_sandbox,
                disable_dev_shm_usage=disable_dev_shm_usage,
                allow_multiple_downloads=allow_multiple_downloads,
                enable_safe_browsing=enable_safe_browsing,
                user_agent=user_agent,
            )
        )
        
        logger.info(f"ChromeDriver criado com sucesso (headless={headless})")
        return driver

    except Exception as e:

        logger.error(f"Erro ao criar ChromeDriver: {e}", exc_info=True)

        return None


def close_window(driver: WebDriver) -> bool:
    """
    Fecha a janela/aba atual do navegador.
    
    Args:
        driver: Instância WebDriver
    
    Returns:
        True se janela fechada com sucesso, False caso contrário
    """
    
    try:
        driver.close()
        logger.debug("Janela fechada com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao fechar janela: {e}")
        return False


def quit(driver: Optional[WebDriver]) -> bool:
    """
    Encerra driver com segurança.
    
    Args:
        driver: Instância WebDriver a encerrar (None é seguro)
    
    Returns:
        True se driver encerrado com sucesso, False se erro (True se None)
    """

    if driver is None:
        return True
    
    try:
        driver.quit()
        logger.info("Driver fechado")
        return True
    except Exception as e:
        logger.error(f"Erro ao encerrar driver: {e}")
        return False