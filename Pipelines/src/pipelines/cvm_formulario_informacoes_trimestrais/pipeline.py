
from src.shared.context import PipelineContext
from .extract import ExtractCVMFormularioInformacoesTrimestrais


class PipelineCVMFormularioInformacoesTrimestrais:

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
        # atualmente os steps existentes usam apenas o nome do pipeline.
        # Mantemos compatibilidade chamando as classes existentes.
        extract = ExtractCVMFormularioInformacoesTrimestrais(pipeline=self.pipeline)
        extract.main(ctx=self.ctx)


def main(env: str = "dev", run_id: str | None = None):
    """Entrypoint padrão para execução (local e container)."""
    p = PipelineCVMFormularioInformacoesTrimestrais(env=env, run_id=run_id)
    p.run()

if __name__ == "__main__":
    main()
