import logging
from src.shared.context import PipelineContext
from src.shared.checkpoint_contract import build_checkpoint_payload
from src.shared.checkpoint_values import STATUS_SUCCESSFUL, STATUS_FAILED
from .config import (
    PIPELINE_NAME,
    DOMINIO_ITENS,
    CHECKPOINT_STAGE_EXTRACT,
    CHECKPOINT_STEP_EXTRACT,
)


class ExtractPipelineTemplate:
    def __init__(self, pipeline: str = PIPELINE_NAME):
        self.pipeline = pipeline
        self.logger = logging.getLogger(__name__)

    def _gravar_checkpoint(self, item: str, status: str, failure_point: str | None, ctx: PipelineContext):
        payload = build_checkpoint_payload(
            pipeline=self.pipeline,
            stage=CHECKPOINT_STAGE_EXTRACT,
            step=CHECKPOINT_STEP_EXTRACT,
            status=status,
            run_id=ctx.run_id,
            environment=ctx.env,
            failure_point=failure_point,
            extra={"item": item},
        )
        ctx.write_checkpoint(self.pipeline, CHECKPOINT_STAGE_EXTRACT, CHECKPOINT_STEP_EXTRACT, item, payload)

    def main(self, ctx=None):
        if ctx is None:
            ctx = PipelineContext()

        self.logger = getattr(ctx, "logger", self.logger)

        raw_path = ctx.path_raw(self.pipeline)
        raw_path.mkdir(parents=True, exist_ok=True)

        for item in DOMINIO_ITENS:
            try:
                self.logger.info(f"[template] Extraindo item: {item}")
                self._gravar_checkpoint(item, STATUS_SUCCESSFUL, None, ctx)
            except Exception:
                self._gravar_checkpoint(item, STATUS_FAILED, "extract_exception", ctx)
                self.logger.exception(f"[template] Falha no extract para {item}")
