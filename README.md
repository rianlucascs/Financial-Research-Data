# Financial Research Data

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Pipelines](https://img.shields.io/badge/ETL-Pipelines-0A66C2)
![Research](https://img.shields.io/badge/Notebook-Research-F37626)

Repositório com dois projetos complementares para coleta, processamento e análise de dados financeiros.

## Projetos

### 1) Pipelines
Automação de extração e transformação de dados (ETL), com execução local e via Docker.

- Coleta dados de fontes externas (ex.: B3)
- Aplica transformações e padronização
- Gera checkpoints para controle de execução
- Mantém logs por execução

Pasta: [Pipelines](Pipelines)

### 2) Research
Ambiente de pesquisa e exploração analítica em notebooks.

- Estudos de preço, retorno e correlação
- Análises por universos (Brasil, globais, emergentes)
- Experimentação para hipóteses e estratégias

Pasta: [Research](Research)

## Tecnologias utilizadas

- **Python** (ETL, análises e automações)
- **Pandas / NumPy / SciPy / scikit-learn** (tratamento e modelagem de dados)
- **Jupyter Notebook** (pesquisa e análise exploratória)
- **Selenium + Chrome** (coleta automatizada web)
- **Docker / Docker Compose** (execução padronizada dos pipelines)
- **Plotly / Matplotlib / Seaborn** (visualização de dados)

## Estrutura resumida

```text
Financial Research Data/
├── Pipelines/   # ETL, jobs, docker, logs/checkpoints
├── Research/    # notebooks e estudos analíticos
├── requirements.txt
└── .gitignore
```

## Como começar

### Pipelines (Docker)
1. Acesse a pasta `Pipelines`
2. Faça build da imagem
3. Execute com variáveis `PIPELINE_NAME` e `PIPELINE_ENV`

Guia detalhado: [Pipelines/README.Docker.md](Pipelines/README.Docker.md)

### Research
- Abra os notebooks da pasta [Research](Research) no VS Code/Jupyter
- Use o mesmo ambiente Python do projeto para consistência dos resultados

## Observações

- Dados gerados em runtime (`Pipelines/data`, `Pipelines/logs`, `Pipelines/state`) são mantidos fora do versionamento por padrão.
- A estrutura foi preparada para escalar novos pipelines com padrão de configuração e contrato de checkpoint compartilhado.

## Roadmap

- Adicionar novos pipelines seguindo o template padrão (`extract`, `transform`, `pipeline`, `config`)
- Expandir validações automáticas de contrato de checkpoint
- Melhorar observabilidade com métricas por execução (tempo, volume, falhas)
- Consolidar documentação operacional de execução local e Docker
