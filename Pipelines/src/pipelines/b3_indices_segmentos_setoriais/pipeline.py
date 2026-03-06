
from .extract import ExtractB3IndicesSegmentosSetoriais
from .transform import TransformB3IndicesSegmentosSetoriais
from src.shared.context import PipelineContext

class PipelineB3IndicesSegmentosSetoriais:
    """Pipeline completa para índices segmentais da B3.
    
    Orquestra o fluxo completo de extração e processamento:
    1. Extract: Download via Selenium dos arquivos CSV do site da B3
    2. Transform: Limpeza e padronização dos dados em formato processado
    
    Gerencia contexto, logging e persistência de checkpoints ao longo do fluxo.
    """

    def __init__(self, env: str = "dev", run_id: str | None = None):

        self.ctx = PipelineContext(env=env, run_id=run_id)

        self.pipeline = "b3_indices_segmentos_setoriais"
        
        # configure per-process logging (creates Logs dir under data)
        try:
            self.ctx.configure_logging(self.pipeline)
        except Exception:
            # fallback: don't crash pipeline creation if logging config fails
            pass

    def run(self):

        extract = ExtractB3IndicesSegmentosSetoriais(pipeline=self.pipeline)
        extract.main(ctx=self.ctx)

        transform = TransformB3IndicesSegmentosSetoriais(pipeline=self.pipeline)
        transform.main(ctx=self.ctx)


def main(env: str = "dev", run_id: str | None = None):
    """Entrypoint padrão para execução (local e container)."""
    p = PipelineB3IndicesSegmentosSetoriais(env=env, run_id=run_id)
    p.run()


if __name__ == "__main__":
    main()
