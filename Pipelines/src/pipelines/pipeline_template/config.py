"""Constantes de configuração do pipeline template.

Copie este pacote, renomeie a pasta e ajuste as constantes abaixo.
"""

PIPELINE_NAME = "pipeline_template"

DOMINIO_ITENS = [
    "ITEM_EXEMPLO_1",
    "ITEM_EXEMPLO_2",
]

CHECKPOINT_STAGE_EXTRACT = "extract"
CHECKPOINT_STEP_EXTRACT = "download"

CHECKPOINT_STAGE_TRANSFORM = "transform"
CHECKPOINT_STEP_TRANSFORM_1 = "transform_1"

MAX_TENTATIVAS = 3
SLEEP_RANGE_SECONDS = (5, 20)
