# Docker no Windows (PowerShell)

## 1) Ir para a pasta do projeto

```powershell
Set-Location "E:\Financial Research Data\Pipelines"
```

## 2) Criar a imagem

```powershell
docker build -f .\Dockerfile -t financial-research-pipeline ..
```

## 3) Executar o container

```powershell
$basePath = (Get-Location).Path
docker run --rm -it `
  -e PIPELINE_NAME=b3_indices_segmentos_setoriais `
  -e PIPELINE_ENV=dev `
  -v "$basePath/data:/app/Pipelines/data" `
  -v "$basePath/logs:/app/Pipelines/logs" `
  -v "$basePath/state:/app/Pipelines/state" `
  financial-research-pipeline
```

```powershell
$basePath = (Get-Location).Path
docker run --rm -it `
  -e PIPELINE_NAME=cvm_formulario_informacoes_trimestrais `
  -e PIPELINE_ENV=dev `
  -v "$basePath/data:/app/Pipelines/data" `
  -v "$basePath/logs:/app/Pipelines/logs" `
  -v "$basePath/state:/app/Pipelines/state" `
  financial-research-pipeline
```


## 4) Executar com Docker Compose (PowerShell)

```powershell
Set-Location "E:\Financial Research Data\Pipelines"
docker compose up b3-indices-pipeline --build
```

## 5) Comandos úteis do Compose (PowerShell)

```powershell
# Rodar em segundo plano
docker compose up -d b3-indices-pipeline --build

# Ver logs em tempo real
docker compose logs -f b3-indices-pipeline

# Parar e remover containers/rede do compose
docker compose down
```

## 6) Se atualizar os scripts

```powershell
# Recriar a imagem com as alterações de código
docker build -f .\Dockerfile -t financial-research-pipeline ..
```
