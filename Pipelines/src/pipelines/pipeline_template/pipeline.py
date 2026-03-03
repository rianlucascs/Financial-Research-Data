from src.shared.context import PipelineContext
from .config import PIPELINE_NAME
from .extract import ExtractPipelineTemplate
from .transform import TransformPipelineTemplate


class PipelineTemplate:
    def __init__(self, env: str = "dev", run_id: str | None = None):
        self.ctx = PipelineContext(env=env, run_id=run_id)
        self.pipeline = PIPELINE_NAME

        try:
            self.ctx.configure_logging(self.pipeline)
        except Exception:
            pass

    def run(self):
        extract = ExtractPipelineTemplate(pipeline=self.pipeline)
        extract.main(ctx=self.ctx)

        transform = TransformPipelineTemplate(pipeline=self.pipeline)
        transform.main(ctx=self.ctx)


def main(env: str = "dev", run_id: str | None = None):
    p = PipelineTemplate(env=env, run_id=run_id)
    p.run()


if __name__ == "__main__":
    main()
