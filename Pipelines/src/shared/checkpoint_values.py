"""Valores padronizados para checkpoints.

Define constantes de `status` e `failure_point` para evitar strings soltas,
facilitar manutenção e manter consistência entre extract/transform.
"""

# Versão do contrato de checkpoint
SCHEMA_VERSION = "v2"

# Stages padrão
STAGE_EXTRACT = "extract"
STAGE_PROCESSED = "processed"
STAGE_LOAD = "load"
STAGE_QUALITY = "quality"
STAGE_PUBLISH = "publish"

STATUS_SUCCESSFUL = "successful"
STATUS_FAILED = "failed"
STATUS_NO_FILE_DETECTED = "no_file_detected"
STATUS_DRIVER_ERROR = "driver_error"

# Status adicionais (padrão de mercado)
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_PARTIAL_SUCCESS = "partial_success"
STATUS_SKIPPED = "skipped"
STATUS_RETRYING = "retrying"
STATUS_TIMEOUT = "timeout"
STATUS_CANCELLED = "cancelled"

FAILURE_DRIVER_CREATION = "driver_creation"
FAILURE_FILE_DETECTION = "file_detection"
FAILURE_VALIDATION = "validation"
FAILURE_EXCEPTION = "exception"
FAILURE_DOWNLOAD_BUTTON_NOT_FOUND = "download_button_not_found"
FAILURE_PROCESSED_EXCEPTION = "transform_exception"

# Failure points técnicos adicionais (padrão de mercado)
FAILURE_NETWORK_ERROR = "network_error"
FAILURE_AUTH_ERROR = "auth_error"
FAILURE_SCHEMA_ERROR = "schema_error"
FAILURE_PARSE_ERROR = "parse_error"
FAILURE_IO_ERROR = "io_error"
FAILURE_TIMEOUT_ERROR = "timeout_error"
FAILURE_DEPENDENCY_ERROR = "dependency_error"
FAILURE_UNEXPECTED_ERROR = "unexpected_error"

# Reason codes de negócio
REASON_ALREADY_PROCESSED = "already_processed"
REASON_NO_NEW_DATA = "no_new_data"
REASON_SOURCE_UNAVAILABLE = "source_unavailable"
REASON_RATE_LIMITED = "rate_limited"
REASON_CHECKPOINT_CORRUPTED = "checkpoint_corrupted"

# Severidade para observabilidade
SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"
SEVERITY_CRITICAL = "critical"
