from src.shared.context import PipelineContext
from .extract import ExtractCVMFormularioInformacoesTrimestrais
from .transform import TransformCVMFormularioInformacoesTrimestrais


class PipelineCVMFormularioInformacoesTrimestrais:
    """Pipeline completa para informações trimestrais da CVM.
    
    Orquestra o fluxo completo de extração e processamento:
    1. Extract: Download dos arquivos de demonstrações financeiras trimestrais (ITRS)
    2. Transform Step 1: Consolidação de arquivos anuais por tipo de demonstração
    3. Transform Step 2: Filtragem e separação de dados por ticker da carteira IBEP
    
    Gerencia contexto, logging e persistência de checkpoints ao longo do fluxo.
    """

    def __init__(self, env: str = "dev", run_id: str | None = None):

        self.ctx = PipelineContext(env=env, run_id=run_id)

        self.pipeline = "cvm_formulario_informacoes_trimestrais"
        
        # configure per-process logging (creates Logs dir under data)
        try:
            self.ctx.configure_logging(self.pipeline)
        except Exception:
            # fallback: don't crash pipeline creation if logging config fails
            pass

    def run(self):

        extract = ExtractCVMFormularioInformacoesTrimestrais(pipeline=self.pipeline)
        extract.main(ctx=self.ctx) 

        transform = TransformCVMFormularioInformacoesTrimestrais(pipeline=self.pipeline)
        transform.main(ctx=self.ctx)


def main(env: str = "dev", run_id: str | None = None):
    """Entrypoint padrão para execução (local e container)."""
    p = PipelineCVMFormularioInformacoesTrimestrais(env=env, run_id=run_id)
    p.run()

if __name__ == "__main__":
    main()
