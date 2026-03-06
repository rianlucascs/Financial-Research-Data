# Financial Research Data

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Pipelines](https://img.shields.io/badge/ETL-Pipelines-0A66C2)
![Research](https://img.shields.io/badge/Notebook-Research-F37626)

Repositório com dois projetos complementares para coleta, processamento e análise de dados financeiros.

## Projetos

### 1) Pipelines
Automação de extração e transformação de dados (ETL), com execução local e via Docker.

**Pipelines Implementadas:**

- **B3 Índices Segmentais** (`b3_indices_segmentos_setoriais`)
  - Extrai índices segmentados por setor via Selenium
  - Processa e padroniza estrutura de dados
  - Salva em CSV com validação de conteúdo

- **CVM Formulários Trimestrais** (`cvm_formulario_informacoes_trimestrais`)
  - Download de demonstrações financeiras trimestrais (ITRS) em ZIP
  - Consolidação de arquivos anuais (2011 em diante)
  - Filtragem por ticker e separação em arquivos por empresa

**Características:**
- Checkpoint de progresso: recovery automático em caso de falha
- Logs estruturados por data/run_id
- Suporte a modo desenvolvimento (skip de reprocessamento)
- Validação de dados em cada etapa

Pasta: [Pipelines](Pipelines) | Detalhes: [Pipelines/ARQUITETURA.md](Pipelines/ARQUITETURA.md)

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
├── Pipelines/
│   ├── jobs/                          # jobs paramétricos
│   ├── src/
│   │   ├── pipelines/
│   │   │   ├── b3_indices_segmentos_setoriais/   # pipeline B3
│   │   │   │   ├── extract.py         # download via Selenium
│   │   │   │   ├── transform.py       # limpeza e padronização
│   │   │   │   ├── pipeline.py        # orquestração
│   │   │   │   └── config.py
│   │   │   ├── cvm_formulario_informacoes_trimestrais/  # pipeline CVM
│   │   │   │   ├── extract.py         # download de ZIP
│   │   │   │   ├── transform_1.py     # consolidação anual
│   │   │   │   ├── transform_2.py     # filtragem por ticker
│   │   │   │   ├── transform.py       # orquestração
│   │   │   │   ├── pipeline.py        # execução end-to-end
│   │   │   │   └── config.py
│   │   │   └── pipeline_template/     # template para novos pipelines
│   │   │       ├── extract.py
│   │   │       ├── transform.py
│   │   │       ├── pipeline.py
│   │   │       └── config.py
│   │   ├── shared/
│   │   │   ├── context.py             # gerenciamento de paths e I/O
│   │   │   ├── checkpoint_contract.py # estrutura de checkpoints
│   │   │   └── checkpoint_values.py   # constants de status
│   │   └── utils/                     # utilities compartilhadas
│   ├── data/
│   │   ├── b3_indices_segmentos_setoriais/
│   │   │   ├── raw/                   # dados brutos
│   │   │   └── processed/             # dados transformados
│   │   └── cvm_formulario_informacoes_trimestrais/
│   │       ├── raw/                   # arquivos ZIP
│   │       ├── interim/               # CSVs consolidados
│   │       └── processed/             # CSVs por ticker
│   ├── state/
│   │   └── checkpoints/               # progresso de execução (JSON)
│   ├── logs/                          # logs por pipeline e run_id
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── README.Docker.md
├── Research/
│   ├── Universos/                     # definições de universos de ativos
│   ├── Ativos Individuais/            # análises específicas
│   └── *.ipynb                        # notebooks de pesquisa
├── requirements.txt
└── README.md
```

## Como começar

### Pipelines (Local)
```bash
# Ativar ambiente
.\.venv\Scripts\Activate.ps1

# Executar pipeline específica
python -m Pipelines.jobs.b3_indices_segmentos_setoriais
python -m Pipelines.jobs.cvm_formulario_informacoes_trimestrais
```

### Pipelines (Docker)
```bash
cd Pipelines
docker-compose up --build -e PIPELINE_NAME=b3_indices_segmentos_setoriais
```

Detalhes completos: [Pipelines/README.Docker.md](Pipelines/README.Docker.md)

### Checkpoints e Recovery
Cada pipeline gera **checkpoints em JSON** em `Pipelines/state/checkpoints/{pipeline}/{stage}/{step}/{key}.json`.

Isso permite:
- **Recovery automático**: se falhar, continua do ponto de parada
- **Auditoria**: rastreia status, timestamps e detalhes de cada etapa
- **Modo desenvolvimento**: pula etapas já processadas com sucesso

### Logs
Logs estruturados por execução em `Pipelines/logs/{pipeline}/{run_id}/{pipeline}.{run_id}.log`

**Opções de monitoramento:**
- Ver logs locais durante/após execução
- Verificar checkpoints JSON para status detalhado
- Usar `desenvolviment_mode=True` para acelerar testes (reprocessa apenas falhas)

### Research
Explore dados processados nos notebooks:
- Abra notebooks da pasta [Research](Research) no VS Code/Jupyter
- Use o mesmo ambiente Python para consistência
- Universos: Brasil, Globais, Emergentes
- Ativos Individuais: análises detalhadas

Pasta: [Research](Research)

## Observações

- Dados gerados em runtime (`Pipelines/data`, `Pipelines/logs`, `Pipelines/state`) são mantidos fora do versionamento por padrão.
- A estrutura foi preparada para escalar novos pipelines seguindo o **padrão**: `extract.py`, `transform.py`, `pipeline.py`, `config.py`
- Checkpoints são essenciais para **recovery**: não deleting manualmente arquivos de checkpoint sem entender o impacto
- Docstrings em classes facilitam manutenção e compreensão do fluxo

## Troubleshooting

**Pipeline falhou?**
1. Checar log em `Pipelines/logs/{pipeline}/{run_id}`
2. Revisar checkpoint JSON em `Pipelines/state/checkpoints/{pipeline}` para entender o ponto de falha
3. Corrigir o erro e executar novamente (recovery automático)

**Erro de path no Windows/Docker?**
- Use `pathlib.Path` para composição agnóstica: `Path(dir_a) / dir_b`
- Evite concatenação com strings ou barras fixas (`\`, `/`)

## Roadmap

- [ ] Adicionar novos pipelines seguindo o template padrão
- [ ] Expandir validações de contratos de checkpoint
- [ ] Dashboard de execução (tempos, volume, falhas por pipeline)
- [ ] Melhorar documentação de troubleshooting e observabilidade
- [ ] Testes automatizados para validação de dados
