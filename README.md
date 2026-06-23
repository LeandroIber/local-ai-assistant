# Local AI Assistant

Assistente pessoal local usando Ollama + modelos open-source (como Qwen3) para receber informações e salvar dados automaticamente em planilhas Excel/CSV.

## Objetivo

Criar um assistente conversacional local que:
- Entende comandos em linguagem natural
- Extrai informações estruturadas
- Salva os dados em planilhas de forma automática

## Status do Projeto

🚧 Em desenvolvimento - Fase inicial (esqueleto)

## Tecnologias

- Python 3.13+
- Ollama (modelos locais)
- Pandas + Openpyxl (manipulação de planilhas)

## Estrutura do Projeto

```
local-ai-assistant/
├── app/                  # Lógica principal
├── data/                 # Planilhas geradas
├── docs/
├── main.py
├── requirements.txt
└── README.md
```

## Como usar (futuro)

```bash
uv venv
uv sync
uv run main.py
```

## Roadmap

- [ ] Esqueleto do projeto
- [ ] Integração básica com Ollama
- [ ] Function Calling + Tools
- [ ] Interface simples (Gradio ou Terminal)
- [ ] Salvamento automático em Excel
- [ ] Múltiplas ferramentas (gastos, anotações, tarefas...)

## Licença

MIT License
