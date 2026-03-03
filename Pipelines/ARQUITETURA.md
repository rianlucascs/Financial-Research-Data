# Arquitetura Multi-Pipeline com Docker

## Fluxo de Execução

```
                    ┌─────────────────────────────────────────────┐
                    │         Docker Container                    │
                    │  (Uma imagem para TODOS os pipelines)      │
                    └─────────────────────────────────────────────┘
                                        ↓
                        ┌───────────────────────────────┐
                        │  Entrypoint Script (entrypoint.sh) │
                        │  Lê: PIPELINE_NAME, PIPELINE_ENV    │
                        └───────────────────────────────┘
                                        ↓
                ┌───────────────────────┬───────────────────────┐
                ↓                       ↓                       ↓
        ┌────────────────┐    ┌─────────────────┐    ┌────────────────┐
        │ B3 Indices     │    │ Outro Pipeline  │    │ Novo Pipeline  │
        │ pipeline.main()│    │ pipeline.main() │    │ pipeline.main()│
        └────────────────┘    └─────────────────┘    └────────────────┘
                ↓
    ┌─────────────────────────────┐
    │ Extract + Transform         │
    │ (usa módulos compartilhados)│
    └─────────────────────────────┘
                ↓
    ┌─────────────────────────────────────────────┐
    │ Salva em volumes compartilhados             │
    │ - /Pipelines/data (downloads)              │
    │ - /Pipelines/logs (logs)                   │
    │ - /Pipelines/state (checkpoints)           │
    └─────────────────────────────────────────────┘
```

## Módulos Compartilhados (Shared)

```
Shared/
├── context.py
│   └── PipelineContext
│       ├── configure_logging()
│       ├── path_raw()
│       ├── checkpoint_path
│       └── run_id
│
└── utils/
    └── selenium_utils.py
        ├── retry()
        ├── chrome_options()
        ├── create_driver()
        ├── safe_click()
        ├── find()
        ├── quit()
        └── close_window()
```

## Exemplo de Novo Pipeline

```
novo_pipeline/
├── pipeline.py
│   └── class PipelineNovoPipeline
│       └── def main(env, run_id)
│
├── extract.py
│   └── class ExtractNovoPipeline
│       └── def main(ctx)
│
└── transform.py
    └── class TransformNovoPipeline
        └── def main(ctx)
```

## Execução Paralela de Pipelines

Com Docker Compose, você pode rodar múltiplos pipelines em paralelo:

```powershell
# Executa ambos simultaneamente
docker-compose up --build

# Parar tudo
docker-compose down
```

Cada pipeline terá seu próprio container, mas compartilham os mesmos volumes de dados.

## Vantagens da Arquitetura

| Aspecto | Benefício |
|--------|-----------|
| **Imagem única** | Todos os pipelines usam Python 3.11 + Chrome |
| **Código compartilhado** | selenium_utils, PipelineContext reutilizáveis |
| **Modularidade** | Fácil adicionar/remover pipelines |
| **Volume único** | Todos os dados em um lugar |
| **Escalabilidade** | Pode rodar dezenas de pipelines |
| **Consistência** | Mesmo ambiente para todos |
