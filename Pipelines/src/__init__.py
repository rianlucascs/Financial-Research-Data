"""Pacote src - contém código principal dos pipelines de extração, transformação e orquestração."""

# Exporta pacotes principais para conveniência
from . import utils
from . import shared
from . import pipelines

__all__ = ['utils', 'shared', 'pipelines']
