#!/usr/bin/env python3
"""
R-Code CLI Entry Point
=====================

Main entry point for the R-Code AI-powered interactive code assistant.
Provides a modern CLI interface with rich formatting and interactive features.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional
import threading

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.rule import Rule
from rich.padding import Padding
from rich.layout import Layout
from rich.table import Table
from rich.spinner import Spinner
from rich.live import Live
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

from src import __version__, __author__

# Load environment variables
load_dotenv()

# Initialize Rich console
console = Console()

# Create the main Typer app
app = typer.Typer(
    name="rcode",
    help="🤖 R-Code - AI-Powered Interactive Code Assistant",
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich"
)


class RCodeWelcome:
    """Professional enterprise-grade welcome screen for R-Code CLI"""
    
    @staticmethod
    def display_welcome() -> None:
        """Display a professional, Ali Baba-inspired welcome screen"""
        console.clear()
        
        # R-Code Logo with Ali Baba branding colors (Orange/Gold)
        logo_text = """
     ██████╗       ██████╗ ██████╗ ██████╗ ███████╗
     ██╔══██╗     ██╔════╝██╔═══██╗██╔══██╗██╔════╝
     ██████╔╝     ██║     ██║   ██║██║  ██║█████╗  
     ██╔══██╗     ██║     ██║   ██║██║  ██║██╔══╝  
     ██║  ██║     ╚██████╗╚██████╔╝██████╔╝███████╗
     ╚═╝  ╚═╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
        """
        
        # Ali Baba-inspired gradient: orange to gold
        logo = Text(logo_text, style="bold rgb(255,106,0)")  # Ali Baba orange
        console.print(Align.center(logo))
        console.print()
        
        # Professional tagline with gold accent
        welcome_text = Text("Welcome to R-Code - Your AI Coding Companion", style="bold rgb(255,215,0)")  # Gold
        console.print(Align.center(welcome_text))
        console.print()
        
        # Subtle instruction in professional gray
        instruction_text = Text("Type 'rcode chat' to start or 'rcode --help' for commands", style="rgb(128,128,128)")
        console.print(Align.center(instruction_text))
        console.print()


def check_api_key() -> bool:
    """Check if Anthropic API key is configured"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print()
        console.print(Panel(
            "[bold red]⚠️  API Key Required[/bold red]\n\n"
            "Please set your Anthropic API key:\n\n"
            "[bold cyan]Windows:[/bold cyan]\n"
            "set ANTHROPIC_API_KEY=your-api-key-here\n\n"
            "[bold cyan]macOS/Linux:[/bold cyan]\n"
            "export ANTHROPIC_API_KEY=your-api-key-here\n\n"
            "[bold cyan]Or create a .env file:[/bold cyan]\n"
            "ANTHROPIC_API_KEY=your-api-key-here",
            border_style="red",
            padding=(1, 2)
        ))
        return False
    return True


@app.command("chat", help="🗣️  Start interactive chat with AI coding assistant")
def start_chat(
    model: str = typer.Option("claude", "--model", "-m", help="Preferred model (openai/claude)"),
    task: str = typer.Option("code_generation", "--task", "-t", help="Task type (code_generation/code_fixing/code_analysis)")
):
    """Start the interactive chat interface with intelligent agents"""
    if not check_api_key():
        raise typer.Exit(1)
    
    # Run the async chat function
    import asyncio
    asyncio.run(run_chat_interface(model, task))


class PremiumUI:
    """Premium Claude-like user interface"""
    
    @staticmethod
    def create_thinking_spinner():
        """Create beautiful thinking spinner"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold rgb(255,106,0)]R-Code is thinking..."),
            transient=True,
        )
    
    @staticmethod
    def format_response(content: str) -> Panel:
        """Format AI response with premium styling"""
        # Check if content contains code blocks
        if "```" in content:
            # Handle code blocks with syntax highlighting
            formatted_content = content
        else:
            # Regular markdown formatting
            formatted_content = content
        
        return Panel(
            formatted_content,
            title="[bold rgb(255,106,0)]R-Code Assistant",
            title_align="left",
            border_style="rgb(255,106,0)",
            padding=(1, 2),
            expand=False
        )
    
    @staticmethod
    def format_user_input(user_input: str) -> Panel:
        """Format user input with premium styling"""
        return Panel(
            f"[white]{user_input}[/white]",
            title="[bold cyan]You",
            title_align="left", 
            border_style="cyan",
            padding=(0, 2),
            expand=False
        )


async def run_chat_interface(preferred_model: str, task_type: str):
    """Run the premium interactive chat interface with R-Code agent"""
    from .agnets import RCodeAgent
    from .tools import is_web_search_available
    from .config import config_manager
    from .rcode_mcp import is_mcp_available, get_mcp_status
    
    # Premium initialization with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold rgb(255,106,0)]Initializing R-Code AI Assistant..."),
        transient=True,
    ) as progress:
        progress.add_task("init", total=None)
        
        try:
            # Initialize the R-Code agent with MCP support (this will create .rcode folder)
            agent = await RCodeAgent.create()
            time.sleep(0.5)  # Brief pause for premium feel
            
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize: {str(e)}[/red]")
            return
    
    # Get configuration info
    config_info = agent.get_config_info()
    
    # Check various system statuses
    web_search_status = "🌐 Web search enabled" if is_web_search_available() else "⚠️  Web search unavailable (set TAVILY_API_KEY)"
    
    mcp_status_info = get_mcp_status()
    if mcp_status_info["mcp_available"] and mcp_status_info["client_initialized"]:
        mcp_status = f"🔌 MCP: {len(mcp_status_info['connected_servers'])} servers, {mcp_status_info['total_tools']} tools"
    elif mcp_status_info["mcp_available"]:
        mcp_status = "🔌 MCP available (no servers configured)"
    else:
        mcp_status = "⚠️  MCP unavailable (install langchain-mcp-adapters)"
    
    # Get checkpoint system status
    checkpoint_status = agent.checkpoint_manager.get_status()
    checkpoint_info = f"🔄 Checkpoints: {checkpoint_status['total_checkpoints']} saved, auto-tracking enabled"
    
    # Success message with elegant styling
    console.print(Panel(
        "[bold green]✨ R-Code AI Assistant Ready[/bold green]\n\n"
        "[dim white]I'm your AI coding companion with full project access.\n"
        "I can read, write, modify files, and help with any coding task.[/dim white]\n\n"
        f"[dim]📁 Config: {config_info['config_dir']}[/dim]\n"
        f"[dim]🤖 Models: {', '.join(config_info['enabled_models'])}[/dim]\n"
        f"[dim]{web_search_status}[/dim]\n"
        f"[dim]{mcp_status}[/dim]\n"
        f"[dim]{checkpoint_info}[/dim]",
        title="[bold rgb(255,106,0)]Welcome to R-Code",
        border_style="rgb(255,106,0)",
        padding=(1, 2)
    ))
    console.print()
    
    # Interactive chat loop with premium UX
    thread_id = f"session_{int(time.time())}"
    
    while True:
        try:
            # Get user input with premium styling
            console.print("[bold cyan]┌─ You[/bold cyan]")
            user_input = console.input("[bold cyan]└─❯[/bold cyan] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                console.print(Panel(
                    "[bold yellow]👋 Thank you for using R-Code![/bold yellow]\n"
                    "[dim]Session saved. See you next time![/dim]",
                    title="[bold yellow]Goodbye",
                    border_style="yellow",
                    padding=(1, 2)
                ))
                break
            
            if user_input.lower() == 'help':
                show_premium_help()
                continue
            
            if user_input.lower() == 'status':
                show_premium_status(agent, thread_id)
                continue
            
            # Display response header
            console.print()
            console.print("[bold rgb(255,106,0)]┌─ R-Code Assistant[/bold rgb(255,106,0)]")
            
            # Use async streaming to support MCP tools - we're already in async context
            async for chunk in agent.astream_chat(user_input, thread_id):
                if chunk["type"] == "tool_use":
                    # Show beautiful tool usage indicator
                    tool_name = chunk.get("tool_name", "Tool")
                    console.print(f"\n[dim yellow]🔍 Using {tool_name}...[/dim yellow]")
                elif chunk["type"] == "tool_result":
                    # Show tool results in beautiful panels
                    tool_name = chunk.get("tool_name", "Tool")
                    console.print()
                    console.print(Panel(
                        chunk["content"],
                        title=f"[bold blue]🔍 {tool_name}[/bold blue]",
                        border_style="blue",
                        padding=(1, 1)
                    ))
                elif chunk["type"] == "token":
                    # Stream clean AI response text
                    print(chunk["content"], end="", flush=True)
            
            console.print()
            console.print("[bold rgb(255,106,0)]└─[/bold rgb(255,106,0)]")
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[dim yellow]Press Ctrl+C again to exit, or type 'exit'[/dim yellow]")
            continue
        except Exception as e:
            console.print(Panel(
                f"[bold red]❌ Error: {str(e)}[/bold red]\n"
                "[dim]Please try again or contact support[/dim]",
                title="[bold red]Error",
                border_style="red",
                padding=(1, 2)
            ))
            continue


def show_premium_help():
    """Show premium R-Code help information"""
    console.print(Panel(
        "[bold cyan]🔧 R-Code Commands[/bold cyan]\n\n"
        "[green]help[/green]          Show this help message\n"
        "[green]status[/green]        Show detailed agent status\n"
        "[green]exit[/green]          Exit the chat session\n\n"
        "[bold cyan]🔄 Checkpoint Commands[/bold cyan]\n\n"
        "[yellow]/help[/yellow]        Show checkpoint commands\n"
        "[yellow]/undo[/yellow]        Undo last AI operation\n"
        "[yellow]/checkpoints[/yellow] View save points\n"
        "[yellow]/revert <id>[/yellow] Revert to checkpoint\n"
        "[yellow]/status[/yellow]      Show session info\n"
        "[yellow]/save <desc>[/yellow] Create checkpoint\n\n"
        "[bold cyan]💻 What I can do for you[/bold cyan]\n\n"
        "✨ [white]Generate, fix, and refactor code[/white]\n"
        "📁 [white]Read, write, and modify files[/white]\n"
        "🏗️  [white]Create directories and manage project structure[/white]\n"
        "🔍 [white]Analyze codebases and provide solutions[/white]\n"
        "📚 [white]Write documentation and tests[/white]\n"
        "🚀 [white]Debug issues and optimize performance[/white]\n"
        "🔄 [white]Automatically track and revert changes[/white]\n\n"
        "[bold cyan]💡 Example Requests[/bold cyan]\n\n"
        "[dim]→[/dim] [italic]'Create a Python Flask API for user management'[/italic]\n"
        "[dim]→[/dim] [italic]'Fix the bug in src/main.py'[/italic]\n"
        "[dim]→[/dim] [italic]'Read the README.md file and summarize it'[/italic]\n"
        "[dim]→[/dim] [italic]'Refactor this code to use TypeScript'[/italic]",
        title="[bold rgb(255,106,0)]R-Code Help",
        border_style="rgb(255,106,0)",
        padding=(1, 2)
    ))
    console.print()


def show_premium_status(agent, thread_id: str):
    """Show premium R-Code agent status"""
    # Get conversation state
    try:
        state = agent.get_state(thread_id)
        message_count = len(state.values.get('messages', [])) if state and state.values else 0
    except Exception:
        message_count = "Unable to retrieve"
    
    console.print(Panel(
        f"[bold cyan]🤖 Agent Information[/bold cyan]\n\n"
        f"[white]Available Models:[/white] [dim]{', '.join(agent.get_available_models())}[/dim]\n"
        f"[white]Session ID:[/white] [dim]{thread_id}[/dim]\n"
        f"[white]Messages in Conversation:[/white] [dim]{message_count}[/dim]\n"
        f"[white]Agent Instance:[/white] [dim]{agent}[/dim]\n\n"
        "[bold green]✅ Status: Active and Ready[/bold green]\n"
        "[dim]LangGraph orchestration with persistent memory[/dim]",
        title="[bold rgb(255,106,0)]R-Code Status",
        border_style="rgb(255,106,0)",
        padding=(1, 2)
    ))
    console.print()


def show_help():
    """Show basic R-Code help information (fallback)"""
    show_premium_help()


def show_status(agent, thread_id: str):
    """Show basic R-Code agent status (fallback)"""
    show_premium_status(agent, thread_id)


@app.command("version", help="📋 Show version information")
def show_version():
    """Display version and system information"""
    RCodeWelcome.create_status_panel()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version")
):
    """
    🤖 R-Code - AI-Powered Interactive Code Assistant
    
    Transform your coding workflow with intelligent AI assistance.
    Chat naturally about your code needs and get instant, context-aware help.
    """
    if version:
        console.print(f"[bold cyan]R-Code CLI v{__version__}[/bold cyan]")
        return
        
    if ctx.invoked_subcommand is None:
        # Start chat directly when no command is provided
        if not check_api_key():
            raise typer.Exit(1)
        
        # Run the async chat function directly
        import asyncio
        asyncio.run(run_chat_interface("claude", "code_generation"))


def cli_entry_point():
    """Entry point for the CLI application"""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli_entry_point()
