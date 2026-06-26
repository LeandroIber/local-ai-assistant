"""
main.py - Ponto de entrada do Local AI Assistant
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from app.ollama_client import chat_with_tools
from app.prompt import SYSTEM_PROMPT   # <-- Importa o prompt correto com regras de segurança


console = Console()


def main():
    console.print(Panel.fit(
        "[bold blue]Local AI Assistant[/bold blue]\n"
        "Assistente pessoal com controle de gastos\n"
        "Digite 'sair' para encerrar.",
        title="Bem-vindo",
        border_style="blue"
    ))


    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT   # <-- Usa o prompt rigoroso com regras de confirmação
        }
    ]

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]Você[/bold green]")

            if user_input.lower() in ["sair", "exit", "quit"]:
                console.print("[yellow]Até logo![/yellow]")
                break

            if not user_input.strip():
                continue

            # Adiciona mensagem do usuário ao histórico
            messages.append({"role": "user", "content": user_input})

            start_time = time.time()

            with console.status("[bold blue]Pensando...[/bold blue]"):
                assistant_response = chat_with_tools(messages)

            elapsed_time = time.time() - start_time

            # Mostra a resposta do assistente
            console.print(f"\n[bold cyan]Assistente[/bold cyan]: {assistant_response}")

            # Mostra o tempo de resposta (pode remover esta linha também)
            console.print(f"[dim italic]⏱️  Tempo de resposta: {elapsed_time:.2f} segundos[/dim italic]")

            # Adiciona resposta do assistente ao histórico
            messages.append({"role": "assistant", "content": assistant_response})

        except KeyboardInterrupt:
            console.print("\n[yellow]Programa interrompido pelo usuário.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Erro:[/red] {str(e)}")


if __name__ == "__main__":
    main()
