"""Pacote utils - contém utilitários de automação web (Selenium) e helpers gerais."""

from .selenium_utils import (
    retry,
    create_driver,
    safe_click,
    find,
    chrome_options
)

# Re-exportar create_driver como web_driver para compatibilidade com código existente
web_driver = create_driver
options = chrome_options

__all__ = ['retry', 'web_driver', 'safe_click', 'find', 'options', 'create_driver', 'chrome_options']