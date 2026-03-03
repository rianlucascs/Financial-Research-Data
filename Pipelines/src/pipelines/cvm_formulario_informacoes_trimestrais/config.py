

from datetime import date


URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"

ARCHIVES_ZIP = [f'itr_cia_aberta_{year_now}.zip' for year_now in range(2011, date.today().year + 1)]

CHECKPOINT_STAGE_EXTRACT = "extract"
CHECKPOINT_STEP_DOWNLOAD_ZIP = "download_zip"
CHECKPOINT_STAGE_EXTRACT_ZIP = "extract_zip"

DOWNLOAD_MAX_ATTEMPTS = 3
