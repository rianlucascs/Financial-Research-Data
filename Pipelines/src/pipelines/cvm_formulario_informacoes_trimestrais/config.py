

from datetime import date


URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/"

ARCHIVES_ZIP = [f'itr_cia_aberta_{year_now}.zip' for year_now in range(2011, date.today().year + 1)]

ITRS = ['BPA_con', 'BPA_ind', 'BPP_con', 'BPP_ind', 
        'DFC_MD_con', 'DFC_MD_ind', 'DFC_MI_con', 
        'DFC_MI_ind', 'DMPL_con', 'DMPL_ind', 'DRA_con', 
        'DRA_ind', 'DRE_con', 'DRE_ind', 'DVA_con', 'DVA_ind']


CHECKPOINT_STAGE_EXTRACT = "extract"
CHECKPOINT_STEP_DOWNLOAD_ZIP = "download_zip"
CHECKPOINT_STAGE_EXTRACT_ZIP = "extract_zip"

CHECKPOINT_STAGE_PROCESSED = "processed"
CHECKPOINT_STEP_PROCESSED_1 = "transform_1"

DOWNLOAD_MAX_ATTEMPTS = 3
