"""
R-Code Intelligent Agent Chat
============================

Interactive chat using the same premium UI/UX as the main R-Code CLI.
Matches the professional Ali Baba-inspired design and behavior.
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import uuid
import tiktoken

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.align import Align
from rich.markdown import Markdown
from rich.table import Table

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents import IntelligentRCodeAgent, RCodeContext

# Initialize Rich console like the main CLI
console = Console()


class TokenTracker:
    """Professional token usage and cost tracking"""
    
    def __init__(self):
        self.session_tokens = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
        self.session_costs = {
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0
        }
        
        # Claude 3.5 Sonnet pricing (per 1M tokens)
        self.pricing = {
            "claude-3-5-sonnet": {
                "input": 3.00,  # $3 per 1M input tokens
                "output": 15.00  # $15 per 1M output tokens
            },
            "gpt-4-turbo": {
                "input": 10.00,  # $10 per 1M input tokens  
                "output": 30.00  # $30 per 1M output tokens
            },
            "default": {
                "input": 5.00,
                "output": 15.00
            }
        }
        
        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        except:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.tokenizer.encode(text))
        except:
            # Fallback: rough estimate
            return len(text.split()) * 1.3
    
    def calculate_cost(self, tokens: int, token_type: str, model: str = "claude-3-5-sonnet") -> float:
        """Calculate cost for tokens"""
        pricing = self.pricing.get(model, self.pricing["default"])
        rate = pricing[token_type] / 1_000_000  # Convert to per-token rate
        return tokens * rate
    
    def track_request(self, input_text: str, output_text: str, model: str = "claude-3-5-sonnet"):
        """Track tokens and costs for a request"""
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        
        input_cost = self.calculate_cost(input_tokens, "input", model)
        output_cost = self.calculate_cost(output_tokens, "output", model)
        
        # Update session totals
        self.session_tokens["input_tokens"] += input_tokens
        self.session_tokens["output_tokens"] += output_tokens
        self.session_tokens["total_tokens"] += input_tokens + output_tokens
        
        self.session_costs["input_cost"] += input_cost
        self.session_costs["output_cost"] += output_cost
        self.session_costs["total_cost"] += input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost
        }
    
    def get_session_stats(self) -> dict:
        """Get current session statistics"""
        return {
            "tokens": self.session_tokens.copy(),
            "costs": self.session_costs.copy()
        }
    
    def format_cost_display(self) -> Panel:
        """Create beautiful cost display panel"""
        tokens = self.session_tokens
        costs = self.session_costs
        
        # Create cost breakdown table
        table = Table(show_header=True, header_style="bold rgb(255,106,0)")
        table.add_column("Metric", style="dim")
        table.add_column("Tokens", justify="right", style="cyan")
        table.add_column("Cost (USD)", justify="right", style="green")
        
        table.add_row(
            "Input", 
            f"{tokens['input_tokens']:,}", 
            f"${costs['input_cost']:.4f}"
        )
        table.add_row(
            "Output", 
            f"{tokens['output_tokens']:,}", 
            f"${costs['output_cost']:.4f}"
        )
        table.add_separator()
        table.add_row(
            "[bold]Total[/bold]", 
            f"[bold]{tokens['total_tokens']:,}[/bold]", 
            f"[bold]${costs['total_cost']:.4f}[/bold]"
        )
        
        return Panel(
            table,
            title="[bold rgb(255,106,0)]💰 Token Usage & Costs",
            border_style="rgb(255,106,0)",
            padding=(1, 1)
        )
    
    def format_mini_display(self) -> str:
        """Create compact cost display for status bar"""
        tokens = self.session_tokens["total_tokens"]
        cost = self.session_costs["total_cost"]
        return f"🪙 {tokens:,} tokens | 💰 ${cost:.4f}"

class RCodeChatWelcome:
    """Professional R-Code welcome screen matching main CLI style"""
    
    @staticmethod
    def display_welcome(user_name: str) -> None:
        """Display professional welcome screen with Ali Baba styling"""
        console.clear()
        
        # R-Code Logo with Ali Baba branding colors (Orange/Gold) - same as main CLI
        logo_text = """
     ██████╗       ██████╗ ██████╗ ██████╗ ███████╗
     ██╔══██╗     ██╔════╝██╔═══██╗██╔══██╗██╔════╝
     ██████╔╝     ██║     ██║   ██║██║  ██║█████╗  
     ██╔══██╗     ██║     ██║   ██║██║  ██║██╔══╝  
     ██║  ██║     ╚██████╗╚██████╔╝██████╔╝███████╗
     ╚═╝  ╚═╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
        """
        
        # Ali Baba orange color - same as main CLI
        logo = Text(logo_text, style="bold rgb(255,106,0)")
        console.print(Align.center(logo))
        console.print()
        
        # Professional tagline with gold accent - same as main CLI
        welcome_text = Text(f"Welcome {user_name} - Interactive AI Chat Session", style="bold rgb(255,215,0)")
        console.print(Align.center(welcome_text))
        console.print()
        
        # Subtle instruction in professional gray - same as main CLI
        instruction_text = Text("Type 'exit' to quit or 'help' for commands", style="rgb(128,128,128)")
        console.print(Align.center(instruction_text))
        console.print()


class PremiumChatUI:
    """Premium chat UI matching the main R-Code CLI style exactly"""
    
    @staticmethod
    def create_thinking_spinner():
        """Create beautiful thinking spinner - same as main CLI"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold rgb(255,106,0)]R-Code is thinking..."),
            transient=True,
        )
    
    @staticmethod
    def format_tool_result(tool_name: str, content: str) -> Panel:
        """Format tool results with premium styling - same as main CLI"""
        return Panel(
            content,
            title=f"[bold blue]🔍 {tool_name}[/bold blue]",
            border_style="blue",
            padding=(1, 1)
        )
    
    @staticmethod
    def format_error(error_msg: str) -> Panel:
        """Format error messages - same as main CLI"""
        return Panel(
            f"[bold red]❌ Error: {error_msg}[/bold red]\n"
            "[dim]Please try again or contact support[/dim]",
            title="[bold red]Error",
            border_style="red",
            padding=(1, 2)
        )


class ChatAgent:
    """Interactive chat agent using R-Code's professional CLI style"""
    
    def __init__(self):
        self.agent = None
        self.context = None
        self.session_id = str(uuid.uuid4())[:8]
        self.thread_id = f"chat_{int(time.time())}"
        self.conversation = []
        self.token_tracker = TokenTracker()
        
    async def initialize_agent(self):
        """Initialize the agent with premium progress display"""
        # Get user name first
        user_name = console.input("👤 Your name: ").strip() or "Developer"
        
        # Premium initialization with progress - same as main CLI
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold rgb(255,106,0)]Initializing R-Code AI Assistant..."),
            transient=True,
        ) as progress:
            progress.add_task("init", total=None)
            
            try:
                # Create context
                self.context = RCodeContext(
                    user_name=user_name,
                    user_id=user_name.lower().replace(" ", "_"),
                    project_root=os.getcwd(),
                    session_id=f"chat_{self.session_id}",
                    coding_style={
                        "indentation": "4_spaces",
                        "naming_convention": "snake_case", 
                        "comment_style": "comprehensive",
                        "error_handling": "detailed",
                        "documentation": "docstring"
                    },
                    preferred_frameworks=["fastapi", "langchain", "langgraph"],
                    language_preferences=["python", "typescript", "javascript"],
                    project_type="development",
                    tech_stack=["python", "langchain", "langgraph"],
                    project_goals=["intelligent_development", "premium_chat"]
                )
                
                # Initialize the R-Code agent
                self.agent = await IntelligentRCodeAgent.create(self.context)
                time.sleep(0.3)  # Brief pause for premium feel
                
            except Exception as e:
                console.print(PremiumChatUI.format_error(str(e)))
                return False
        
        # Show welcome screen
        RCodeChatWelcome.display_welcome(self.context.user_name)
        
        # Success message with elegant styling - same as main CLI
        console.print(Panel(
            "[bold green]✨ R-Code AI Assistant Ready[/bold green]\n\n"
            "[dim white]I'm your AI coding companion with full project access.\n"
            "I can read, write, modify files, and help with any coding task.[/dim white]\n\n"
            f"[dim]🎯 Session: {self.session_id}[/dim]\n"
            f"[dim]🤖 Agent: {str(self.agent)}[/dim]\n"
            f"[dim]📚 Learning system active[/dim]\n"
            f"[dim]🔧 Real-time tool execution[/dim]",
            title="[bold rgb(255,106,0)]Welcome to R-Code Chat",
            border_style="rgb(255,106,0)",
            padding=(1, 2)
        ))
        console.print()
        return True
    
    def show_help(self):
        """Show help information - same style as main CLI"""
        console.print(Panel(
            "[bold cyan]💬 R-Code Chat Commands[/bold cyan]\n\n"
            "[green]help[/green]          Show this help message\n"
            "[green]status[/green]        Show session status\n"
            "[green]stats[/green]         Show learning statistics\n"
            "[green]costs[/green]         Show token usage and costs\n"
            "[green]clear[/green]         Clear conversation history\n"
            "[green]export[/green]        Export conversation to file\n"
            "[green]exit[/green]          Exit the chat session\n\n"
            "[bold cyan]💡 What I can do for you[/bold cyan]\n\n"
            "✨ [white]Generate, fix, and refactor code[/white]\n"
            "📁 [white]Read, write, and modify files[/white]\n"
            "🏗️  [white]Create directories and manage project structure[/white]\n"
            "🔍 [white]Analyze codebases and provide solutions[/white]\n"
            "📚 [white]Write documentation and tests[/white]\n"
            "🔧 [white]Run terminal commands with real-time output[/white]\n\n"
            "[bold cyan]💡 Example Requests[/bold cyan]\n\n"
            "[dim]→[/dim] [italic]'Create a FastAPI app with authentication'[/italic]\n"
            "[dim]→[/dim] [italic]'Fix the bug in my Python code'[/italic]\n"
            "[dim]→[/dim] [italic]'Analyze this project structure'[/italic]\n"
            "[dim]→[/dim] [italic]'Add tests for my functions'[/italic]",
            title="[bold rgb(255,106,0)]R-Code Help",
            border_style="rgb(255,106,0)",
            padding=(1, 2)
        ))
        console.print()
    
    def show_status(self):
        """Show session status - same style as main CLI"""
        try:
            state = self.agent.get_state(self.thread_id)
            message_count = len(state.values.get('messages', [])) if state and state.values else 0
        except Exception:
            message_count = "Unable to retrieve"
        
        console.print(Panel(
            f"[bold cyan]🤖 Chat Session Information[/bold cyan]\n\n"
            f"[white]Session ID:[/white] [dim]{self.session_id}[/dim]\n"
            f"[white]Thread ID:[/white] [dim]{self.thread_id}[/dim]\n"
            f"[white]User:[/white] [dim]{self.context.user_name}[/dim]\n"
            f"[white]Messages:[/white] [dim]{message_count}[/dim]\n"
            f"[white]Agent Type:[/white] [dim]IntelligentRCodeAgent[/dim]\n\n"
            "[bold green]✅ Status: Active and Ready[/bold green]\n"
            "[dim]Intelligent agent with learning capabilities[/dim]",
            title="[bold rgb(255,106,0)]Session Status",
            border_style="rgb(255,106,0)",
            padding=(1, 2)
        ))
        console.print()
    
    def show_stats(self):
        """Show learning statistics"""
        stats = self.agent.get_learning_stats()
        
        task_dist = ""
        if stats.get('task_types'):
            task_lines = []
            for task_type, count in stats['task_types'].items():
                task_lines.append(f"   • {task_type.title()}: {count}")
            task_dist = "\n".join(task_lines)
        else:
            task_dist = "   No data yet - start asking questions!"
        
        console.print(Panel(
            f"[bold cyan]📊 Learning Statistics[/bold cyan]\n\n"
            f"[white]Total Interactions:[/white] [dim]{stats.get('total_interactions', 0)}[/dim]\n"
            f"[white]Average Success Rate:[/white] [dim]{stats.get('average_success_rating', 0):.1%}[/dim]\n"
            f"[white]This Session:[/white] [dim]{len(self.conversation) // 2} exchanges[/dim]\n\n"
            f"[bold cyan]📈 Task Distribution:[/bold cyan]\n{task_dist}",
            title="[bold rgb(255,106,0)]Intelligence Metrics",
            border_style="rgb(255,106,0)",
            padding=(1, 2)
        ))
        console.print()
    
    def export_conversation(self):
        """Export conversation to markdown file"""
        filename = f"rcode_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# R-Code Chat Session\n\n")
            f.write(f"**Session ID:** {self.session_id}\n")
            f.write(f"**User:** {self.context.user_name}\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Exchanges:** {len(self.conversation) // 2}\n\n")
            f.write("---\n\n")
            
            for msg in self.conversation:
                role = "👤 User" if msg["role"] == "user" else "🤖 R-Code Agent"
                timestamp = msg["timestamp"].strftime("%H:%M:%S")
                f.write(f"## {role} ({timestamp})\n\n")
                f.write(f"{msg['content']}\n\n")
                
                if msg.get("tools_used"):
                    f.write(f"**Tools used:** {', '.join(msg['tools_used'])}\n\n")
                
                f.write("---\n\n")
        
        console.print(f"✅ [green]Conversation exported to: {filename}[/green]")
        console.print()
    
    async def handle_user_message(self, user_input: str):
        """Handle user message with real-time tool streaming - same style as main CLI"""
        response_parts = []
        tools_used = []
        current_tool = None
        
        # Display response header - same as main CLI
        console.print()
        console.print("[bold rgb(255,106,0)]┌─ R-Code Assistant[/bold rgb(255,106,0)]")
        
        try:
            # Stream with real-time tool feedback showing progress
            async for chunk in self.agent.astream_chat(user_input, self.context, thread_id=self.thread_id):
                
                if chunk["type"] == "tool_use":
                    # Show tool start indicator with visible progress
                    tool_name = chunk.get("tool_name", "Tool")
                    current_tool = tool_name
                    tools_used.append(tool_name)
                    print(f"\n🔄 Starting {tool_name}", end="", flush=True)
                    
                    # Show visible progress dots
                    for i in range(3):
                        await asyncio.sleep(0.3)
                        print(".", end="", flush=True)
                    
                    print(f" 🔍 Executing...")
                
                elif chunk["type"] == "tool_result":
                    # Show completed tool result with success indicator
                    tool_name = chunk.get("tool_name", current_tool or "Tool")
                    result_content = chunk["content"]
                    
                    console.print(f"[dim green]✅ {tool_name} completed[/dim green]")
                    console.print()
                    
                    # Show detailed tool result in beautiful panel
                    console.print(PremiumChatUI.format_tool_result(tool_name, result_content))
                    
                    # Reset current tool
                    current_tool = None
                
                elif chunk["type"] == "token":
                    # Stream AI response text in real-time AND collect for markdown
                    response_parts.append(chunk["content"])
                    print(chunk["content"], end="", flush=True)
            
            # After streaming, also show as beautiful markdown if it contains formatting
            full_response = ''.join(response_parts)
            if full_response and ("```" in full_response or "#" in full_response or "*" in full_response):
                console.print("\n")
                
                # Render as markdown with syntax highlighting
                markdown = Markdown(full_response)
                console.print(markdown)
            
            console.print()
            console.print("[bold rgb(255,106,0)]└─[/bold rgb(255,106,0)]")
            console.print()
            
            # Add to conversation history and track tokens/costs
            full_response = ''.join(response_parts)
            if full_response:
                # Track token usage and costs for this request
                request_stats = self.token_tracker.track_request(user_input, full_response)
                
                # Show real-time cost info
                cost_info = self.token_tracker.format_mini_display()
                console.print(f"[dim]{cost_info}[/dim]")
                
                self.conversation.extend([
                    {"role": "user", "content": user_input, "timestamp": datetime.now()},
                    {"role": "assistant", "content": full_response, "timestamp": datetime.now(), "tools_used": tools_used, "token_stats": request_stats}
                ])
                
                # Learn from interaction
                self.agent.learn_from_interaction(
                    user_input=user_input,
                    ai_response=full_response,
                    success_rating=0.9
                )
            
        except Exception as e:
            console.print(PremiumChatUI.format_error(str(e)))
    
    async def run_chat(self):
        """Main chat loop with premium UX - same style as main CLI"""
        # Initialize agent
        if not await self.initialize_agent():
            return
        
        # Interactive chat loop with premium UX - same as main CLI
        while True:
            try:
                # Get user input with premium styling - same as main CLI
                console.print("[bold cyan]┌─ You[/bold cyan]")
                user_input = console.input("[bold cyan]└─❯[/bold cyan] ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print(Panel(
                        "[bold yellow]👋 Thank you for using R-Code![/bold yellow]\n"
                        "[dim]Session saved. See you next time![/dim]",
                        title="[bold yellow]Goodbye",
                        border_style="yellow",
                        padding=(1, 2)
                    ))
                    break
                
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                elif user_input.lower() == 'status':
                    self.show_status()
                    continue
                
                elif user_input.lower() == 'stats':
                    self.show_stats()
                    continue
                
                elif user_input.lower() == 'costs':
                    console.print(self.token_tracker.format_cost_display())
                    console.print()
                    continue
                
                elif user_input.lower() == 'clear':
                    self.conversation = []
                    console.clear()
                    RCodeChatWelcome.display_welcome(self.context.user_name)
                    console.print("🗑️ [green]Conversation cleared - Fresh start![/green]\n")
                    continue
                
                elif user_input.lower() == 'export':
                    self.export_conversation()
                    continue
                
                # Handle regular message
                await self.handle_user_message(user_input)
                
            except KeyboardInterrupt:
                console.print("\n[dim yellow]Press Ctrl+C again to exit, or type 'exit'[/dim yellow]")
                continue
            except Exception as e:
                console.print(PremiumChatUI.format_error(str(e)))
                continue


async def main():
    """Launch the R-Code chat using the premium CLI style"""
    chat_agent = ChatAgent()
    await chat_agent.run_chat()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Goodbye![/yellow]")
