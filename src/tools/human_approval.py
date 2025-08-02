"""
R-Code Human Approval System
===========================

Human-in-the-loop approval system for terminal commands using LangGraph's interrupt mechanism.
Provides configurable security controls for AI-executed commands.
"""

import os
import re
import shlex
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from langchain_core.tools import tool
from langgraph.types import interrupt
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..config import config_manager


class CommandRiskLevel(Enum):
    """Risk levels for terminal commands"""
    SAFE = "safe"
    MODERATE = "moderate"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"


@dataclass
class CommandAnalysis:
    """Analysis of a terminal command"""
    command: str
    risk_level: CommandRiskLevel
    reasons: List[str]
    working_directory: str
    is_directory_allowed: bool
    requires_approval: bool
    auto_approve_reason: Optional[str] = None


class CommandSecurityAnalyzer:
    """Analyzes commands for security risks and approval requirements"""
    
    def __init__(self):
        """Initialize the security analyzer"""
        self.console = Console()
        self._load_security_patterns()
    
    def _load_security_patterns(self):
        """Load security patterns for command analysis"""
        # Dangerous command patterns
        self.dangerous_patterns = [
            r'\brm\s+.*-[rf]+',  # rm with recursive/force flags
            r'\bsudo\s+rm',      # sudo rm commands
            r'\bformat\s+',      # format commands
            r'\bfdisk\s+',       # disk partitioning
            r'\bdd\s+if=',       # disk dump commands
            r'\bshutdown\s+',    # shutdown commands
            r'\breboot\s+',      # reboot commands
            r'\bkill\s+-9',      # force kill commands
            r'\bchmod\s+777',    # dangerous permissions
            r'\bcurl\s+.*\|\s*(bash|sh)', # pipe to shell
            r'\bwget\s+.*\|\s*(bash|sh)', # pipe to shell
            r'>\s*/dev/sd[a-z]', # writing to disk devices
            r'\bmount\s+',       # mount commands
            r'\bumount\s+',      # unmount commands
            r'\buseradd\s+',     # user management
            r'\buserdel\s+',     # user deletion
            r'\bpasswd\s+',      # password changes
        ]
        
        # Moderately risky patterns
        self.moderate_patterns = [
            r'\brm\s+',          # any rm command
            r'\bmv\s+.*\s+/',    # moving to root directories
            r'\bcp\s+.*-r',      # recursive copy
            r'\bchmod\s+',       # permission changes
            r'\bchown\s+',       # ownership changes
            r'\bssh\s+',         # SSH connections
            r'\bscp\s+',         # secure copy
            r'\brsync\s+',       # rsync commands
            r'\bnpm\s+install\s+-g', # global npm installs
            r'\bpip\s+install\s+--user', # user pip installs
            r'\bapt\s+install',  # package installations
            r'\byum\s+install',  # package installations
            r'\bbrew\s+install', # package installations
        ]
        
        # Network-related patterns
        self.network_patterns = [
            r'\bcurl\s+',
            r'\bwget\s+',
            r'\bnc\s+',          # netcat
            r'\btelnet\s+',
            r'\bftp\s+',
            r'\bsftp\s+',
        ]
    
    def analyze_command(self, command: str, working_directory: str = None) -> CommandAnalysis:
        """Analyze a command for security risks and approval requirements"""
        config = config_manager.load_config()
        terminal_config = config.get("tools", {}).get("terminal_operations", {})
        
        working_directory = working_directory or os.getcwd()
        
        # Parse command to get the base command
        try:
            parsed_command = shlex.split(command)
            base_command = parsed_command[0] if parsed_command else ""
        except ValueError:
            # If parsing fails, use the first word
            base_command = command.split()[0] if command.split() else ""
        
        # Initialize analysis
        reasons = []
        risk_level = CommandRiskLevel.SAFE
        
        # Check if command is in safe list
        safe_commands = terminal_config.get("safe_commands", [])
        if any(command.strip().startswith(safe_cmd) for safe_cmd in safe_commands):
            risk_level = CommandRiskLevel.SAFE
            reasons.append("Command is in safe commands list")
        
        # Check dangerous patterns
        elif any(re.search(pattern, command, re.IGNORECASE) for pattern in self.dangerous_patterns):
            risk_level = CommandRiskLevel.DANGEROUS
            reasons.append("Command matches dangerous pattern")
        
        # Check moderate patterns
        elif any(re.search(pattern, command, re.IGNORECASE) for pattern in self.moderate_patterns):
            risk_level = CommandRiskLevel.MODERATE
            reasons.append("Command matches moderate risk pattern")
        
        # Check network patterns
        elif any(re.search(pattern, command, re.IGNORECASE) for pattern in self.network_patterns):
            risk_level = CommandRiskLevel.MODERATE
            reasons.append("Command involves network operations")
        
        # Check if command is explicitly dangerous
        dangerous_commands = terminal_config.get("dangerous_commands", [])
        if base_command in dangerous_commands:
            risk_level = CommandRiskLevel.CRITICAL
            reasons.append(f"'{base_command}' is in dangerous commands list")
        
        # Check directory restrictions
        is_directory_allowed = self._check_directory_permissions(working_directory, terminal_config)
        if not is_directory_allowed:
            risk_level = CommandRiskLevel.CRITICAL
            reasons.append("Command would run in restricted directory")
        
        # Determine if approval is required
        requires_approval = self._requires_approval(risk_level, terminal_config)
        auto_approve_reason = None
        
        if not requires_approval:
            if terminal_config.get("auto_approve_safe_commands", False) and risk_level == CommandRiskLevel.SAFE:
                auto_approve_reason = "Auto-approved: Safe command"
            elif not terminal_config.get("human_approval_required", True):
                auto_approve_reason = "Auto-approved: Human approval disabled"
        
        return CommandAnalysis(
            command=command,
            risk_level=risk_level,
            reasons=reasons,
            working_directory=working_directory,
            is_directory_allowed=is_directory_allowed,
            requires_approval=requires_approval,
            auto_approve_reason=auto_approve_reason
        )
    
    def _check_directory_permissions(self, working_directory: str, terminal_config: Dict[str, Any]) -> bool:
        """Check if command execution is allowed in the specified directory"""
        work_path = Path(working_directory).resolve()
        
        # Check restricted directories
        restricted_dirs = terminal_config.get("restricted_directories", [])
        for restricted in restricted_dirs:
            restricted_path = Path(restricted).resolve()
            try:
                if work_path == restricted_path or restricted_path in work_path.parents:
                    return False
            except (OSError, ValueError):
                continue
        
        # Check allowed directories
        allowed_dirs = terminal_config.get("allowed_directories", ["."])
        if not allowed_dirs:
            return True  # If no restrictions, allow all
        
        for allowed in allowed_dirs:
            allowed_path = Path(allowed).resolve()
            try:
                if work_path == allowed_path or allowed_path in work_path.parents:
                    return True
            except (OSError, ValueError):
                continue
        
        return False
    
    def _requires_approval(self, risk_level: CommandRiskLevel, terminal_config: Dict[str, Any]) -> bool:
        """Determine if a command requires human approval"""
        # If human approval is disabled entirely
        if not terminal_config.get("human_approval_required", True):
            return False
        
        # If auto-approve safe commands is enabled and command is safe
        if (terminal_config.get("auto_approve_safe_commands", False) and 
            risk_level == CommandRiskLevel.SAFE):
            return False
        
        # All other commands require approval when human approval is enabled
        return True
    
    def format_approval_request(self, analysis: CommandAnalysis) -> str:
        """Format a human-readable approval request"""
        # Create risk level styling
        risk_colors = {
            CommandRiskLevel.SAFE: "green",
            CommandRiskLevel.MODERATE: "yellow", 
            CommandRiskLevel.DANGEROUS: "red",
            CommandRiskLevel.CRITICAL: "bright_red"
        }
        
        risk_icons = {
            CommandRiskLevel.SAFE: "✅",
            CommandRiskLevel.MODERATE: "⚠️",
            CommandRiskLevel.DANGEROUS: "🚨",
            CommandRiskLevel.CRITICAL: "🛑"
        }
        
        with self.console.capture() as capture:
            # Main approval panel
            self.console.print(Panel(
                f"[bold]🤖 AI wants to execute a terminal command[/bold]\n\n"
                f"[bold cyan]Command:[/bold cyan] [white]{analysis.command}[/white]\n"
                f"[bold cyan]Directory:[/bold cyan] [dim]{analysis.working_directory}[/dim]\n"
                f"[bold cyan]Risk Level:[/bold cyan] [{risk_colors[analysis.risk_level]}]{risk_icons[analysis.risk_level]} {analysis.risk_level.value.title()}[/{risk_colors[analysis.risk_level]}]\n\n"
                f"[bold yellow]Analysis:[/bold yellow]\n" +
                "\n".join(f"• {reason}" for reason in analysis.reasons),
                title="[bold red]🔐 Human Approval Required[/bold red]",
                border_style="red",
                padding=(1, 2)
            ))
            
            # Options table
            options_table = Table(
                title="Available Options",
                show_header=True,
                header_style="bold cyan",
                border_style="cyan"
            )
            
            options_table.add_column("Option", style="bold")
            options_table.add_column("Description", style="white")
            
            options_table.add_row("approve", "✅ Allow the command to execute")
            options_table.add_row("deny", "❌ Block the command execution")
            options_table.add_row("modify", "✏️  Modify the command before execution")
            options_table.add_row("always-approve", "🟢 Approve and add to safe commands")
            options_table.add_row("always-deny", "🔴 Deny and add to dangerous commands")
            
            self.console.print()
            self.console.print(options_table)
            
            # Safety notice
            if analysis.risk_level in [CommandRiskLevel.DANGEROUS, CommandRiskLevel.CRITICAL]:
                self.console.print()
                self.console.print(Panel(
                    "[bold red]⚠️  WARNING[/bold red]\n\n"
                    "This command has been flagged as potentially dangerous. "
                    "Please review carefully before approving.\n\n"
                    "Consider the following:\n"
                    "• Could this command damage your system?\n"
                    "• Does it access sensitive files or directories?\n"
                    "• Is it making network connections?\n"
                    "• Do you trust the AI's intent with this command?",
                    border_style="red",
                    padding=(1, 2)
                ))
        
        return capture.get()


# Global analyzer instance
_security_analyzer = CommandSecurityAnalyzer()


@tool
def request_terminal_approval(command: str, working_directory: str = None, 
                            session_id: str = "default") -> str:
    """
    Request human approval for terminal command execution using LangGraph interrupt.
    
    This tool analyzes commands for security risks and requests human approval
    when needed based on configuration settings. Uses LangGraph's human-in-the-loop
    mechanism to pause execution and wait for user input.
    
    Args:
        command: Terminal command to analyze and request approval for
        working_directory: Directory where command will be executed  
        session_id: Terminal session ID
        
    Returns:
        String indicating approval status and any modifications
    """
    # Analyze the command
    analysis = _security_analyzer.analyze_command(command, working_directory)
    
    # If approval is not required, auto-approve
    if not analysis.requires_approval:
        if analysis.auto_approve_reason:
            return f"✅ {analysis.auto_approve_reason}\n🚀 Command approved for execution: {command}"
        else:
            return f"✅ Command approved for execution: {command}"
    
    # Format approval request
    approval_request = _security_analyzer.format_approval_request(analysis)
    
    # Request human approval using LangGraph interrupt
    try:
        human_response = interrupt({
            "type": "terminal_approval",
            "command": command,
            "working_directory": working_directory or os.getcwd(),
            "risk_level": analysis.risk_level.value,
            "reasons": analysis.reasons,
            "session_id": session_id,
            "approval_request": approval_request,
            "analysis": {
                "command": analysis.command,
                "risk_level": analysis.risk_level.value,  
                "reasons": analysis.reasons,
                "working_directory": analysis.working_directory,
                "is_directory_allowed": analysis.is_directory_allowed
            }
        })
        
        # Process human response
        if isinstance(human_response, dict) and "action" in human_response:
            action = human_response["action"].lower()
            
            if action == "approve":
                return f"✅ Human approved command execution: {command}"
            
            elif action == "deny":
                return f"❌ Human denied command execution: {command}\n🚫 Command blocked for security reasons"
            
            elif action == "modify":
                modified_command = human_response.get("modified_command", command)
                return f"✏️  Human modified command\n📝 Original: {command}\n🔄 Modified: {modified_command}\n✅ Approved for execution: {modified_command}"
            
            elif action == "always-approve":
                # Add to safe commands
                config = config_manager.load_config()
                safe_commands = config.get("tools", {}).get("terminal_operations", {}).get("safe_commands", [])
                
                # Add the base command to safe list
                try:
                    base_command = shlex.split(command)[0]
                    if base_command not in safe_commands:
                        safe_commands.append(base_command)
                        config["tools"]["terminal_operations"]["safe_commands"] = safe_commands
                        config_manager.save_config(config)
                except:
                    pass
                
                return f"✅ Human approved and added to safe commands: {command}\n🟢 Future similar commands will be auto-approved"
            
            elif action == "always-deny":
                # Add to dangerous commands
                config = config_manager.load_config()
                dangerous_commands = config.get("tools", {}).get("terminal_operations", {}).get("dangerous_commands", [])
                
                # Add the base command to dangerous list
                try:
                    base_command = shlex.split(command)[0]
                    if base_command not in dangerous_commands:
                        dangerous_commands.append(base_command)
                        config["tools"]["terminal_operations"]["dangerous_commands"] = dangerous_commands
                        config_manager.save_config(config)
                except:
                    pass
                
                return f"❌ Human denied and added to dangerous commands: {command}\n🔴 Future similar commands will be auto-blocked"
            
            else:
                return f"❓ Unknown human response: {action}\n🚫 Command execution blocked due to invalid response"
        
        else:
            # Handle simple approve/deny response
            response_str = str(human_response).lower().strip()
            if response_str in ["approve", "yes", "y", "allow"]:
                return f"✅ Human approved command execution: {command}"
            else:
                return f"❌ Human denied command execution: {command}\n🚫 Command blocked"
                
    except Exception as e:
        return f"❌ Error during approval process: {str(e)}\n🚫 Command execution blocked for safety"


def get_command_analysis(command: str, working_directory: str = None) -> CommandAnalysis:
    """Get security analysis for a command without requesting approval"""
    return _security_analyzer.analyze_command(command, working_directory)


def is_command_safe(command: str, working_directory: str = None) -> bool:
    """Quick check if a command is considered safe"""
    analysis = _security_analyzer.analyze_command(command, working_directory)
    return analysis.risk_level == CommandRiskLevel.SAFE and analysis.is_directory_allowed


def format_command_analysis(analysis: CommandAnalysis) -> str:
    """Format command analysis for display"""
    return _security_analyzer.format_approval_request(analysis)
