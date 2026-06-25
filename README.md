# Local AI Assistant

Assistente pessoal que roda localmente e ajuda a organizar gastos e outras informações do dia a dia.

## Objetivo

Criar um assistente local que entenda comandos em linguagem natural, registre gastos de forma segura e consiga evoluir para gerenciar anotações, tarefas e compromissos.

## Status Atual

O projeto está em desenvolvimento. Na versão atual já é possível registrar gastos com confirmação do usuário antes de salvar, listar os gastos registrados e conversar de forma básica com o assistente.

O maior desafio no momento é a velocidade das respostas e a precisão em consultas mais complexas, como resumos e agrupamentos de gastos.

## O que já funciona

- Registro de gastos com confirmação explícita antes de salvar
- Listagem de gastos
- Chat no terminal com medição de tempo de resposta
- Sistema que evita salvar informações sem autorização do usuário

## Tecnologias usadas

- Python
- Ollama (para rodar o modelo de linguagem localmente)
- DuckDB (banco de dados local)
- Rich (para melhorar a interface no terminal)

## Estrutura do projeto

O projeto está organizado da seguinte forma:

- `main.py`: Ponto de entrada do chat
- `app/`: Contém a lógica principal do assistente
  - `database.py`: Conexão com bd
  - `tools.py`: Definição das ferramentas
  - `ollama_client.py`: Comunicação com o Ollama
  - `prompt.py`: Instruções do sistema
- `data/`: BD
- `docs/`: Documentação do projeto

## Como executar

1. Ative o ambiente virtual:
   source .venv/bin/activate
text

2. (Opcional) Defina o endereço do Ollama, caso não esteja usando o padrão:
   export OLLAMA_HOST="http://localhost:11434"
   
3. Rode o assistente:
   python main.py
