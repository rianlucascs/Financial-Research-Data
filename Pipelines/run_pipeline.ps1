param(
    [string]$PipelineName = "b3_indices_segmentos_setoriais",
    [string]$PipelineEnv = "dev"
)

Write-Host "🚀 Executando pipeline: $PipelineName (env: $PipelineEnv)" -ForegroundColor Green

# Resolve caminhos baseado na pasta deste script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Build primeira vez
Write-Host "📦 Building Docker image..." -ForegroundColor Yellow
docker build -f "$scriptDir/Dockerfile" -t financial-research-pipeline "$projectRoot"

# Executa o container
Write-Host "▶️  Iniciando container..." -ForegroundColor Yellow
$basePath = $scriptDir
docker run -it `
  -e PIPELINE_NAME=$PipelineName `
  -e PIPELINE_ENV=$PipelineEnv `
  -v "$basePath/data:/app/Pipelines/data" `
  -v "$basePath/logs:/app/Pipelines/logs" `
  -v "$basePath/state:/app/Pipelines/state" `
  financial-research-pipeline

Write-Host "✅ Pipeline $PipelineName finalizado" -ForegroundColor Green

