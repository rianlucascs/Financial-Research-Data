import logging
from src.shared.context import PipelineContext
from src.shared.checkpoint_contract import build_checkpoint_payload
from src.shared.checkpoint_values import STATUS_SUCCESSFUL, STATUS_FAILED
from .config import (
    PIPELINE_NAME,
    DOMINIO_ITENS,
    CHECKPOINT_STAGE_PROCESSED,
    CHECKPOINT_STEP_PROCESSED_1,
)


class TransformPipelineTemplate:
    def __init__(self, pipeline: str = PIPELINE_NAME):
        self.pipeline = pipeline
        self.logger = logging.getLogger(__name__)

    def _gravar_checkpoint(self, item: str, status: str, failure_point: str | None, ctx: PipelineContext):
        payload = build_checkpoint_payload(
            pipeline=self.pipeline,
            stage=CHECKPOINT_STAGE_PROCESSED,
            step=CHECKPOINT_STEP_PROCESSED_1,
            status=status,
            run_id=ctx.run_id,
            environment=ctx.env,
            failure_point=failure_point,
            extra={"item": item},
        )
        ctx.write_checkpoint(self.pipeline, CHECKPOINT_STAGE_PROCESSED, CHECKPOINT_STEP_PROCESSED_1, item, payload)

    def transform_1(self, ctx=None):
        if ctx is None:
            ctx = PipelineContext()

        self.logger = getattr(ctx, "logger", self.logger)
        _, processed_path = ctx.prepare_processed_paths(self.pipeline, CHECKPOINT_STEP_PROCESSED_1)

        for item in DOMINIO_ITENS:
            try:
                self.logger.info(f"[template] Transformando item: {item}")
                output_file = processed_path / f"{item}.txt"
                output_file.write_text(f"resultado de {item}\n", encoding="utf-8")
                self._gravar_checkpoint(item, STATUS_SUCCESSFUL, None, ctx)
            except Exception:
                self._gravar_checkpoint(item, STATUS_FAILED, "transform_exception", ctx)
                self.logger.exception(f"[template] Falha no transform para {item}")

    def main(self, ctx=None):
        self.transform_1(ctx)
