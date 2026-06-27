"""
main.py - Ponto de entrada do Local AI Assistant (Financeiro)
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from app.ollama_client import chat_with_tools


console = Console()


def main():
    console.print(Panel.fit(
        "[bold blue]Alfred > Assistente Financeiro[/bold blue]\n\n"
        "Olá! Eu soua seu assistente pessoal de finanças.\n"
        "Posso te ajudar a registrar suas compras e organizar seu balanço financeiro.\n\n"
        "Digite [bold]\"sair\"[/bold] para encerrar.",
        title="Olá,Bem-vindo!",
        border_style="blue"
    ))

    # Histórico da conversa (apenas user e assistant)
    messages = []

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]Você[/bold green]")

            if user_input.lower().strip() in ["sair", "exit", "quit"]:
                console.print("[yellow]Até logo! Seus dados estão salvos com segurança.[/yellow]")
                break

            if not user_input.strip():
                continue

            # Adiciona mensagem do usuário ao histórico
            messages.append({"role": "user", "content": user_input})

            start_time = time.time()

            with console.status("[bold blue]Pensando...[/bold blue]"):
                assistant_response = chat_with_tools(messages)

            elapsed_time = time.time() - start_time

            # Exibe resposta do assistente
            console.print(f"\n[bold cyan]Alfred[/bold cyan]: {assistant_response}")

            # Tempo de resposta (útil em desenvolvimento)
            console.print(f"[dim]  {elapsed_time:.2f}s[/dim]")

            # Adiciona resposta do assistente ao histórico
            messages.append({"role": "assistant", "content": assistant_response})

        except KeyboardInterrupt:
            console.print("\n[yellow]Programa interrompido pelo usuário.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Erro inesperado:[/red] {str(e)}")


if __name__ == "__main__":
    main()
