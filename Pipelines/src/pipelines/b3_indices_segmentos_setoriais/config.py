"""Constantes de configuração do pipeline b3_indices_segmentos_setoriais.

Centraliza listas de domínio (índices), nomes de estágio/step de checkpoint
e parâmetros operacionais (tentativas e intervalo de espera).
"""

B3_INDICES = [
    "IDIV", "MLCX", "SMLL", "IVBX", "AGFS", "IFNC", "IBEP", "IBEE", "IBHB", "IFIX",
    "IBLV", "IMOB", "UTIL", "ICON", "IEEX", "IFIL", "IMAT", "INDX", "IBSD", "BDRX",
]

CHECKPOINT_STAGE_EXTRACT = "extract"
CHECKPOINT_STEP_DOWNLOAD = "download"

CHECKPOINT_STAGE_PROCESSED = "processed"
CHECKPOINT_STEP_PROCESSED_1 = "transform_1"

DOWNLOAD_MAX_ATTEMPTS = 3
DOWNLOAD_SLEEP_RANGE_SECONDS = (5, 20)
