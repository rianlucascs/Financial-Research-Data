import logging

from src.shared.context import PipelineContext
from .transform_1 import TransformCVMFormularioInformacoesTrimestraisStep1
from .transform_2 import TransformCVMFormularioInformacoesTrimestraisStep2

class TransformCVMFormularioInformacoesTrimestrais:
    """Orquestração de transformações de informações trimestrais da CVM.
    
    Coordena dois estágios de processamento:
    - Step 1: Consolidação de arquivos anuais por tipo de demonstração
    - Step 2: Filtragem e separação de dados por ticker da carteira IBEP
    """

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.logger = logging.getLogger(__name__)

        self.transform_1_runner = TransformCVMFormularioInformacoesTrimestraisStep1(pipeline=pipeline)
        self.transform_2_runner = TransformCVMFormularioInformacoesTrimestraisStep2(pipeline=pipeline)

    def _transform_1(self, ctx=None):
        self.transform_1_runner.run(ctx=ctx)

    def _transform_2(self, ctx=None, desenvolviment_mode=False):
        self.transform_2_runner.run(ctx=ctx, desenvolviment_mode=desenvolviment_mode)

    def main(self, ctx=None):
        
        if ctx is None:
            ctx = PipelineContext()

        self.logger = getattr(ctx, 'logger', self.logger)

        self._transform_1(ctx)
        
        # desenvolviment_mode=True pula arquivos já processados para acelerar testes durante desenvolvimento.
        self._transform_2(ctx, desenvolviment_mode=False)