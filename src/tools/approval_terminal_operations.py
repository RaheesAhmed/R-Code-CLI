"""
R-Code Approval-Aware Terminal Operations
========================================

Terminal operations with integrated human approval system using LangGraph's interrupt mechanism.
Provides secure command execution with configurable approval workflows.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

from .terminal_operations import _terminal_ops, CommandStatus
from .human_approval import (
    _security_analyzer, 
    get_command_analysis, 
    is_command_safe,
    CommandRiskLevel
)
from ..config import config_manager


@tool
def execute_command_with_approval(command: str, session_id: str = "default", 
                                timeout: int = 300, stream_output: bool = False,
                                working_directory: str = None) -> str:
    """
    Execute a terminal command with human approval when required.
    
    This tool provides secure command execution by:
    - Analyzing commands for security risks
    - Requesting human approval for potentially dangerous commands
    - Supporting configurable approval workflows
    - Providing detailed execution feedback
    - Tracking command history and results
    
    The approval system can be configured in .rcode/config.json:
    - human_approval_required: Enable/disable approval system
    - auto_approve_safe_commands: Auto-approve verified safe commands
    - allowed_directories: Restrict execution to specific directories
    - safe_commands: Commands that don't require approval
    - dangerous_commands: Commands that are always blocked
    
    Args:
        command: The command to execute (e.g., "ls -la", "python script.py")
        session_id: Terminal session ID (default: "default")
        timeout: Command timeout in seconds (default: 300)
        stream_output: Whether to stream output in real-time (default: False) 
        working_directory: Directory to execute command in (optional)
        
    Returns:
        Formatted string with command execution results or approval status
    """
    from .human_approval import request_terminal_approval
    
    # Get session and working directory
    session = _terminal_ops.get_session(session_id)
    if not session:
        return f"❌ Error: Session '{session_id}' not found"
    
    work_dir = working_directory or session.working_dir
    
    # Analyze command for security risks
    analysis = get_command_analysis(command, work_dir)
    
    # If approval is required, show security warning and require manual approval
    if analysis.requires_approval:
        # Risk level styling
        risk_icons = {
            CommandRiskLevel.SAFE: "✅",
            CommandRiskLevel.MODERATE: "⚠️",
            CommandRiskLevel.DANGEROUS: "🚨", 
            CommandRiskLevel.CRITICAL: "🛑"
        }
        
        risk_colors = {
            CommandRiskLevel.SAFE: "green",
            CommandRiskLevel.MODERATE: "yellow", 
            CommandRiskLevel.DANGEROUS: "red",
            CommandRiskLevel.CRITICAL: "bright_red"
        }
        
        approval_message = f"""
🔐 HUMAN APPROVAL REQUIRED

Command: {command}
Directory: {work_dir}
Risk Level: {risk_icons[analysis.risk_level]} {analysis.risk_level.value.title()}

Security Analysis:
{chr(10).join(f'• {reason}' for reason in analysis.reasons)}

To execute this command, please use one of these slash commands:
• /approve-command "{command}" - Approve this specific command
• /always-approve "{command.split()[0]}" - Add base command to safe list
• Use 'configure_terminal_approval' tool to modify security settings

For safety, this command has been blocked until you explicitly approve it.
"""
        return approval_message.strip()
    
    else:
        # Command doesn't require approval, but show the reason
        if analysis.auto_approve_reason:
            approval_info = f"🔓 {analysis.auto_approve_reason}\n"
        else:
            approval_info = "🔓 Command auto-approved\n"
    
    # Execute the approved command
    try:
        result = _terminal_ops.execute_command(
            command=command,
            session_id=session_id,
            timeout=timeout,
            working_dir=work_dir,
            stream_output=stream_output
        )
        
        # Format execution result
        status_emoji = {
            CommandStatus.COMPLETED: "✅",
            CommandStatus.FAILED: "❌", 
            CommandStatus.TIMEOUT: "⏰",
            CommandStatus.CANCELLED: "🚫"
        }
        
        emoji = status_emoji.get(result.status, "❓")
        
        formatted_result = ""
        
        # Add approval info if available
        if 'approval_info' in locals():
            formatted_result += approval_info
        
        formatted_result += f"{emoji} Command Executed: {result.command}\n"
        formatted_result += f"📊 Status: {result.status.value} (Exit Code: {result.exit_code})\n"
        formatted_result += f"⏱️  Execution Time: {result.execution_time:.2f}s\n"
        formatted_result += f"📁 Working Directory: {result.working_directory}\n"
        
        # Add security analysis info for dangerous commands
        if analysis.risk_level in [CommandRiskLevel.MODERATE, CommandRiskLevel.DANGEROUS, CommandRiskLevel.CRITICAL]:
            formatted_result += f"🔍 Security Analysis: {analysis.risk_level.value.title()} risk level\n"
        
        if result.memory_usage:
            formatted_result += f"💾 Memory Usage: {result.memory_usage:.1f} MB\n"
        
        if result.cpu_usage:
            formatted_result += f"🔄 CPU Usage: {result.cpu_usage:.1f}%\n"
        
        if result.stdout:
            formatted_result += f"\n📤 STDOUT:\n{result.stdout}\n"
        
        if result.stderr:
            formatted_result += f"\n📥 STDERR:\n{result.stderr}\n"
        
        if result.error_message:
            formatted_result += f"\n❌ ERROR: {result.error_message}\n"
        
        return formatted_result
        
    except Exception as e:
        return f"❌ Command execution failed: {str(e)}"


@tool
def analyze_command_security(command: str, working_directory: str = None) -> str:
    """
    Analyze a command for security risks without executing it.
    
    This tool provides detailed security analysis including:
    - Risk level assessment (Safe, Moderate, Dangerous, Critical)
    - Security pattern matching
    - Directory permission checks
    - Approval requirement analysis
    - Detailed reasoning for risk assessment
    
    Use this tool to understand why a command might require approval
    or to assess command safety before execution.
    
    Args:
        command: Command to analyze
        working_directory: Directory context for analysis
        
    Returns:
        Formatted security analysis report
    """
    import os
    
    work_dir = working_directory or os.getcwd()
    analysis = get_command_analysis(command, work_dir)
    
    # Risk level styling
    risk_icons = {
        CommandRiskLevel.SAFE: "✅",
        CommandRiskLevel.MODERATE: "⚠️",
        CommandRiskLevel.DANGEROUS: "🚨", 
        CommandRiskLevel.CRITICAL: "🛑"
    }
    
    result = f"🔍 Security Analysis Report\n"
    result += f"{'=' * 40}\n\n"
    
    result += f"📝 Command: {analysis.command}\n"
    result += f"📁 Directory: {analysis.working_directory}\n"
    result += f"🔒 Risk Level: {risk_icons[analysis.risk_level]} {analysis.risk_level.value.title()}\n"
    result += f"🚪 Directory Allowed: {'✅ Yes' if analysis.is_directory_allowed else '❌ No'}\n"
    result += f"👤 Requires Approval: {'✅ Yes' if analysis.requires_approval else '❌ No'}\n"
    
    if analysis.auto_approve_reason:
        result += f"🔓 Auto-Approval: {analysis.auto_approve_reason}\n"
    
    result += f"\n📋 Analysis Details:\n"
    for i, reason in enumerate(analysis.reasons, 1):
        result += f"  {i}. {reason}\n"
    
    # Configuration info
    config = config_manager.load_config() 
    terminal_config = config.get("tools", {}).get("terminal_operations", {})
    
    result += f"\n⚙️  Configuration:\n"
    result += f"  • Human Approval: {'Enabled' if terminal_config.get('human_approval_required', True) else 'Disabled'}\n"
    result += f"  • Auto-Approve Safe: {'Enabled' if terminal_config.get('auto_approve_safe_commands', False) else 'Disabled'}\n"
    result += f"  • Allowed Directories: {len(terminal_config.get('allowed_directories', ['.']))}\n"
    result += f"  • Safe Commands: {len(terminal_config.get('safe_commands', []))}\n"
    result += f"  • Dangerous Commands: {len(terminal_config.get('dangerous_commands', []))}\n"
    
    return result


@tool
def configure_terminal_approval(setting: str, value: str = None) -> str:
    """
    Configure terminal approval system settings.
    
    This tool allows you to modify the approval system configuration:
    - Enable/disable human approval requirement
    - Configure auto-approval for safe commands
    - Manage allowed and restricted directories
    - Update safe and dangerous command lists
    
    Settings can be:
    - human_approval_required: true/false
    - auto_approve_safe_commands: true/false
    - add_safe_command: <command> (adds to safe list)
    - remove_safe_command: <command> (removes from safe list)
    - add_dangerous_command: <command> (adds to dangerous list)
    - remove_dangerous_command: <command> (removes from dangerous list)
    - add_allowed_directory: <path> (adds to allowed directories)
    - remove_allowed_directory: <path> (removes from allowed directories)
    
    Args:
        setting: Setting name to modify
        value: New value for the setting (optional for some operations)
        
    Returns:
        Formatted result of configuration change
    """
    config = config_manager.load_config()
    terminal_config = config.get("tools", {}).get("terminal_operations", {})
    
    try:
        if setting == "human_approval_required":
            if value is None:
                return f"❌ Error: Value required for {setting}. Use 'true' or 'false'"
            
            enabled = value.lower() in ['true', 'yes', '1', 'enable', 'on']
            terminal_config["human_approval_required"] = enabled
            status = "enabled" if enabled else "disabled"
            result = f"✅ Human approval requirement {status}"
            
        elif setting == "auto_approve_safe_commands":
            if value is None:
                return f"❌ Error: Value required for {setting}. Use 'true' or 'false'"
            
            enabled = value.lower() in ['true', 'yes', '1', 'enable', 'on']
            terminal_config["auto_approve_safe_commands"] = enabled
            status = "enabled" if enabled else "disabled"
            result = f"✅ Auto-approve safe commands {status}"
            
        elif setting == "add_safe_command":
            if value is None:
                return f"❌ Error: Command value required for {setting}"
            
            safe_commands = terminal_config.get("safe_commands", [])
            if value not in safe_commands:
                safe_commands.append(value)
                terminal_config["safe_commands"] = safe_commands
                result = f"✅ Added '{value}' to safe commands list"
            else:
                result = f"ℹ️  '{value}' is already in safe commands list"
                
        elif setting == "remove_safe_command":
            if value is None:
                return f"❌ Error: Command value required for {setting}"
            
            safe_commands = terminal_config.get("safe_commands", [])
            if value in safe_commands:
                safe_commands.remove(value)
                terminal_config["safe_commands"] = safe_commands
                result = f"✅ Removed '{value}' from safe commands list"
            else:
                result = f"ℹ️  '{value}' is not in safe commands list"
                
        elif setting == "add_dangerous_command":
            if value is None:
                return f"❌ Error: Command value required for {setting}"
            
            dangerous_commands = terminal_config.get("dangerous_commands", [])
            if value not in dangerous_commands:
                dangerous_commands.append(value)
                terminal_config["dangerous_commands"] = dangerous_commands
                result = f"✅ Added '{value}' to dangerous commands list"
            else:
                result = f"ℹ️  '{value}' is already in dangerous commands list"
                
        elif setting == "remove_dangerous_command":
            if value is None:
                return f"❌ Error: Command value required for {setting}"
            
            dangerous_commands = terminal_config.get("dangerous_commands", [])
            if value in dangerous_commands:
                dangerous_commands.remove(value)
                terminal_config["dangerous_commands"] = dangerous_commands
                result = f"✅ Removed '{value}' from dangerous commands list"
            else:
                result = f"ℹ️  '{value}' is not in dangerous commands list"
                
        elif setting == "add_allowed_directory":
            if value is None:
                return f"❌ Error: Directory path required for {setting}"
            
            allowed_dirs = terminal_config.get("allowed_directories", [])
            if value not in allowed_dirs:
                allowed_dirs.append(value)
                terminal_config["allowed_directories"] = allowed_dirs
                result = f"✅ Added '{value}' to allowed directories"
            else:
                result = f"ℹ️  '{value}' is already in allowed directories"
                
        elif setting == "remove_allowed_directory":
            if value is None:
                return f"❌ Error: Directory path required for {setting}"
            
            allowed_dirs = terminal_config.get("allowed_directories", [])
            if value in allowed_dirs:
                allowed_dirs.remove(value)
                terminal_config["allowed_directories"] = allowed_dirs
                result = f"✅ Removed '{value}' from allowed directories"
            else:
                result = f"ℹ️  '{value}' is not in allowed directories"
        
        else:
            return f"❌ Error: Unknown setting '{setting}'"
        
        # Save updated configuration
        config["tools"]["terminal_operations"] = terminal_config
        config_manager.save_config(config)
        
        result += f"\n💾 Configuration saved to {config_manager.config_file}"
        return result
        
    except Exception as e:
        return f"❌ Error updating configuration: {str(e)}"


@tool
def show_terminal_approval_status() -> str:
    """
    Show current terminal approval system status and configuration.
    
    This tool displays:
    - Current approval system settings
    - Safe and dangerous command lists
    - Directory restrictions
    - Recent approval statistics
    - Configuration file location
    
    Use this to understand the current security configuration.
    
    Returns:
        Formatted status report
    """
    config = config_manager.load_config()
    terminal_config = config.get("tools", {}).get("terminal_operations", {})
    
    result = f"🔐 Terminal Approval System Status\n"
    result += f"{'=' * 45}\n\n"
    
    # Main settings
    human_approval = terminal_config.get("human_approval_required", True)
    auto_approve_safe = terminal_config.get("auto_approve_safe_commands", False)
    
    result += f"⚙️  Configuration:\n"
    result += f"   • Human Approval Required: {'✅ Enabled' if human_approval else '❌ Disabled'}\n"
    result += f"   • Auto-Approve Safe Commands: {'✅ Enabled' if auto_approve_safe else '❌ Disabled'}\n"
    
    # Directory settings
    allowed_dirs = terminal_config.get("allowed_directories", ["."])
    restricted_dirs = terminal_config.get("restricted_directories", [])
    
    result += f"\n📁 Directory Settings:\n"
    result += f"   • Allowed Directories ({len(allowed_dirs)}):\n"
    for directory in allowed_dirs:
        result += f"     - {directory}\n"
    
    if restricted_dirs:
        result += f"   • Restricted Directories ({len(restricted_dirs)}):\n"
        for directory in restricted_dirs:
            result += f"     - {directory}\n"
    
    # Command lists
    safe_commands = terminal_config.get("safe_commands", [])
    dangerous_commands = terminal_config.get("dangerous_commands", [])
    
    result += f"\n📋 Command Lists:\n"
    result += f"   • Safe Commands ({len(safe_commands)}):\n"
    if safe_commands:
        for cmd in safe_commands[:10]:  # Show first 10
            result += f"     - {cmd}\n"
        if len(safe_commands) > 10:
            result += f"     ... and {len(safe_commands) - 10} more\n"
    else:
        result += f"     (None configured)\n"
    
    result += f"   • Dangerous Commands ({len(dangerous_commands)}):\n"
    if dangerous_commands:
        for cmd in dangerous_commands[:10]:  # Show first 10
            result += f"     - {cmd}\n"
        if len(dangerous_commands) > 10:
            result += f"     ... and {len(dangerous_commands) - 10} more\n"
    else:
        result += f"     (Using default patterns)\n"
    
    # Configuration file info
    result += f"\n💾 Configuration:\n"
    result += f"   • Config File: {config_manager.config_file}\n"
    result += f"   • Last Modified: {config.get('version', 'Unknown')}\n"
    
    # Usage instructions
    result += f"\n💡 Usage:\n"
    result += f"   • Use 'configure_terminal_approval' to modify settings\n"
    result += f"   • Use 'analyze_command_security' to check command safety\n"
    result += f"   • Commands requiring approval will pause execution for user input\n"
    
    return result


def get_approval_aware_terminal_tools() -> List:
    """
    Get list of approval-aware terminal operation tools for LangGraph integration
    
    Returns:
        List of approval-aware terminal operation tools
    """
    # Import other tools from terminal_operations (non-execute tools)
    from .terminal_operations import (
        get_terminal_state,
        get_running_processes,
        kill_process,
        get_system_info,
        get_command_history,
        change_directory,
        create_terminal_session,
        list_terminal_sessions,
        set_environment_variable,
        get_environment_variables
    )
    
    return [
        execute_command_with_approval,  # Replace the standard execute_command
        analyze_command_security,
        configure_terminal_approval,
        show_terminal_approval_status,
        # Include all the other terminal tools unchanged
        get_terminal_state,
        get_running_processes,
        kill_process,
        get_system_info,
        get_command_history,
        change_directory,
        create_terminal_session,
        list_terminal_sessions,
        set_environment_variable,
        get_environment_variables
    ]
