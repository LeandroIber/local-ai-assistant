# Local AI Assistant

Assistente pessoal que roda localmente e ajuda a organizar informações do dia a dia, como gastos, anotações e tarefas.

## Objetivo

Criar um assistente que entenda comandos em linguagem natural, extraia as informações importantes e salve esses dados de forma organizada em um banco de dados local.

## Status atual

O projeto está em desenvolvimento. Até agora foi criada a estrutura básica e a ferramenta para registrar gastos.

## Tecnologias

- Python
- Ollama
- DuckDB

## Estrutura do projeto

O projeto está organizado da seguinte forma:

- app/: Contém a lógica principal do programa
  - tools.py: Define as ferramentas que o assistente pode usar (ex: salvar gasto)
  - database.py: Cuida da conexão e operações com o banco de dados
  - ollama_client.py: Responsável pela comunicação com o Ollama e function calling
- data/: Onde fica o banco de dados local (arquivo assistant.duckdb)
- main.py: Ponto de entrada do programa, onde será criado o chat
- requirements.txt: Lista de dependências do projeto

## Como executar

```bash
cd local-ai-assistant
source .venv/bin/activate
python app/tools.py
