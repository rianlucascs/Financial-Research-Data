
from .extract import ExtractB3IndicesSegmentosSetoriais
from .transform import TransformB3IndicesSegmentosSetoriais
from src.shared.context import PipelineContext

class PipelineB3IndicesSegmentosSetoriais:

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
        # atualmente os steps existentes usam apenas o nome do pipeline.
        # Mantemos compatibilidade chamando as classes existentes.
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
