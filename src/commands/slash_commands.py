"""
R-Code Slash Commands Handler
============================

Professional command handler for R-Code CLI slash commands.
Provides enterprise-grade checkpoint management and system control.
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.padding import Padding
from datetime import datetime

from ..checkpoint.checkpoint_manager import CheckpointManager, OperationType


class SlashCommandHandler:
    """Professional slash command handler for R-Code CLI"""
    
    def __init__(self, checkpoint_manager: CheckpointManager):
        """Initialize slash command handler"""
        self.checkpoint_manager = checkpoint_manager
        self.console = Console()
        
        # Command registry
        self.commands = {
            'help': self.handle_help,
            'undo': self.handle_undo,
            'checkpoints': self.handle_checkpoints,
            'revert': self.handle_revert,
            'status': self.handle_status,
            'save': self.handle_save,
            'clean': self.handle_clean,
            'export': self.handle_export,
            'diff': self.handle_diff,
            'approve-command': self.handle_approve_command,
            'always-approve': self.handle_always_approve
        }
    
    def is_slash_command(self, message: str) -> bool:
        """Check if message is a slash command"""
        return message.strip().startswith('/')
    
    def parse_command(self, message: str) -> Tuple[str, List[str]]:
        """Parse slash command and arguments"""
        message = message.strip()
        if not message.startswith('/'):
            return '', []
        
        parts = message[1:].split()
        command = parts[0].lower() if parts else ''
        args = parts[1:] if len(parts) > 1 else []
        
        return command, args
    
    async def handle_command(self, message: str) -> Optional[str]:
        """Handle slash command and return response"""
        command, args = self.parse_command(message)
        
        if command not in self.commands:
            return self._format_unknown_command(command)
        
        try:
            return await self.commands[command](args)
        except Exception as e:
            return self._format_error(f"Command failed: {str(e)}")
    
    async def handle_help(self, args: List[str]) -> str:
        """Show help for available commands"""
        if args and args[0] in self.commands:
            return self._get_command_help(args[0])
        
        # Create beautiful help panel
        help_table = Table(
            title="🔧 R-Code Slash Commands",
            show_header=True,
            header_style="bold rgb(255,106,0)",
            border_style="rgb(255,106,0)",
            expand=False
        )
        
        help_table.add_column("Command", style="bold cyan", width=20)
        help_table.add_column("Description", style="white", width=50)
        help_table.add_column("Usage", style="dim", width=30)
        
        commands_info = [
            ("/help", "Show this help message", "/help [command]"),
            ("/undo", "Undo last AI operation", "/undo"),
            ("/checkpoints", "View save points", "/checkpoints [limit]"),
            ("/revert <id>", "Revert to checkpoint", "/revert abc12345"),
            ("/status", "Show session info", "/status"),
            ("/save <desc>", "Create checkpoint", "/save 'My checkpoint'"),
            ("/clean", "Clean old checkpoints", "/clean [count]"),
            ("/export <id>", "Export checkpoint", "/export abc12345"),
            ("/diff <id>", "Show changes in checkpoint", "/diff abc12345")
        ]
        
        for cmd, desc, usage in commands_info:
            help_table.add_row(cmd, desc, usage)
        
        # Create feature highlights
        features_text = Text()
        features_text.append("✨ Features:\n", style="bold yellow")
        features_text.append("• Automatic change tracking\n", style="dim white")
        features_text.append("• File-level rollback support\n", style="dim white")
        features_text.append("• Session persistence\n", style="dim white")
        features_text.append("• Backup management\n", style="dim white")
        
        # Combine in columns
        content = Columns([help_table, Padding(features_text, (2, 4))])
        
        with self.console.capture() as capture:
            self.console.print(content)
        
        return capture.get()
    
    async def handle_undo(self, args: List[str]) -> str:
        """Undo the last operation"""
        success = self.checkpoint_manager.undo_last_operation()
        
        if success:
            return self._format_success("✅ Last operation undone successfully")
        else:
            return self._format_error("❌ No operations to undo")
    
    async def handle_checkpoints(self, args: List[str]) -> str:
        """Show list of checkpoints"""
        limit = 10  # Default limit
        if args:
            try:
                limit = int(args[0])
            except ValueError:
                return self._format_error("Invalid limit. Use: /checkpoints [number]")
        
        checkpoints = self.checkpoint_manager.get_checkpoints(limit)
        
        if not checkpoints:
            return self._format_info("📝 No checkpoints found")
        
        # Create checkpoints table
        table = Table(
            title=f"📂 Recent Checkpoints (showing {len(checkpoints)})",
            show_header=True,
            header_style="bold rgb(255,106,0)",
            border_style="rgb(255,106,0)",
            expand=False
        )
        
        table.add_column("ID", style="bold cyan", width=12)
        table.add_column("Time", style="dim", width=20)
        table.add_column("Description", style="white", width=40)
        table.add_column("Operations", style="yellow", width=12)
        table.add_column("Type", style="green", width=10)
        
        for checkpoint in checkpoints:
            time_str = checkpoint.timestamp.strftime("%H:%M:%S %d/%m")
            op_count = len(checkpoint.operations)
            cp_type = "Auto" if checkpoint.auto_created else "Manual"
            
            # Truncate description if too long
            desc = checkpoint.description
            if len(desc) > 38:
                desc = desc[:35] + "..."
            
            table.add_row(
                checkpoint.id,
                time_str,
                desc,
                str(op_count),
                cp_type
            )
        
        with self.console.capture() as capture:
            self.console.print(table)
            self.console.print()
            self.console.print("[dim]Use [bold]/revert <id>[/bold] to revert to a checkpoint[/dim]")
        
        return capture.get()
    
    async def handle_revert(self, args: List[str]) -> str:
        """Revert to a specific checkpoint"""
        if not args:
            return self._format_error("Usage: /revert <checkpoint-id>")
        
        checkpoint_id = args[0]
        checkpoint = self.checkpoint_manager.get_checkpoint(checkpoint_id)
        
        if not checkpoint:
            return self._format_error(f"Checkpoint '{checkpoint_id}' not found")
        
        # Show confirmation info
        affected_files = set()
        for op in checkpoint.operations:
            affected_files.update(op.files_before.keys())
            affected_files.update(op.files_after.keys())
        
        success = self.checkpoint_manager.revert_to_checkpoint(checkpoint_id)
        
        if success:
            return self._format_success(
                f"✅ Reverted to checkpoint '{checkpoint_id}'\n"
                f"📁 Affected {len(affected_files)} files\n"
                f"🕒 Checkpoint: {checkpoint.description}"
            )
        else:
            return self._format_error(f"❌ Failed to revert to checkpoint '{checkpoint_id}'")
    
    async def handle_status(self, args: List[str]) -> str:
        """Show current session status"""
        status = self.checkpoint_manager.get_status()
        
        # Create status panel
        status_table = Table(
            title="📊 R-Code Session Status",
            show_header=False,
            border_style="rgb(255,106,0)",
            expand=False
        )
        
        status_table.add_column("Property", style="bold cyan", width=25)
        status_table.add_column("Value", style="white", width=35)
        
        status_items = [
            ("Session ID", status["session_id"]),
            ("Workspace", str(status["workspace_path"])[:50] + "..." if len(str(status["workspace_path"])) > 50 else str(status["workspace_path"])),
            ("Total Checkpoints", str(status["total_checkpoints"])),
            ("Total Operations", str(status["total_operations"])),
            ("Current Operations", str(status["current_operations"])),
            ("Last Checkpoint", status["last_checkpoint"][:19] if status["last_checkpoint"] else "None"),
            ("Checkpoint Storage", str(status["checkpoint_dir"])[:50] + "..." if len(str(status["checkpoint_dir"])) > 50 else str(status["checkpoint_dir"])),
            ("Backup Storage", str(status["backup_dir"])[:50] + "..." if len(str(status["backup_dir"])) > 50 else str(status["backup_dir"]))
        ]
        
        for prop, value in status_items:
            status_table.add_row(prop, value)
        
        with self.console.capture() as capture:
            self.console.print(status_table)
        
        return capture.get()
    
    async def handle_save(self, args: List[str]) -> str:
        """Create a manual checkpoint"""
        if not args:
            return self._format_error("Usage: /save <description>")
        
        description = " ".join(args)
        if len(description.strip()) < 3:
            return self._format_error("Description must be at least 3 characters")
        
        checkpoint_id = self.checkpoint_manager.create_checkpoint(
            description, 
            auto_created=False, 
            tag="manual"
        )
        
        return self._format_success(f"✅ Checkpoint created: {checkpoint_id}\n📝 Description: {description}")
    
    async def handle_clean(self, args: List[str]) -> str:
        """Clean old checkpoints"""
        keep_count = 20  # Default
        if args:
            try:
                keep_count = int(args[0])
                if keep_count < 5:
                    return self._format_error("Must keep at least 5 checkpoints")
            except ValueError:
                return self._format_error("Invalid count. Use: /clean [number]")
        
        old_count = len(self.checkpoint_manager.checkpoints)
        self.checkpoint_manager.cleanup_old_checkpoints(keep_count)
        new_count = len(self.checkpoint_manager.checkpoints)
        
        cleaned = old_count - new_count
        
        if cleaned > 0:
            return self._format_success(f"✅ Cleaned {cleaned} old checkpoints\n📦 Kept {new_count} most recent")
        else:
            return self._format_info("📝 No cleanup needed")
    
    async def handle_export(self, args: List[str]) -> str:
        """Export checkpoint information"""
        if not args:
            return self._format_error("Usage: /export <checkpoint-id>")
        
        checkpoint_id = args[0]
        checkpoint = self.checkpoint_manager.get_checkpoint(checkpoint_id)
        
        if not checkpoint:
            return self._format_error(f"Checkpoint '{checkpoint_id}' not found")
        
        # Create detailed export
        export_data = {
            "checkpoint_id": checkpoint.id,
            "timestamp": checkpoint.timestamp.isoformat(),
            "description": checkpoint.description,
            "auto_created": checkpoint.auto_created,
            "tag": checkpoint.tag,
            "operations": []
        }
        
        for op in checkpoint.operations:
            op_data = {
                "id": op.id,
                "type": op.type.value,
                "timestamp": op.timestamp.isoformat(),
                "description": op.description,
                "user_message": op.user_message,
                "ai_response": op.ai_response[:200] + "..." if op.ai_response and len(op.ai_response) > 200 else op.ai_response,
                "files_affected": list(op.files_before.keys())
            }
            export_data["operations"].append(op_data)
        
        # Save to export file
        export_file = self.checkpoint_manager.checkpoint_dir / f"export_{checkpoint_id}_{int(datetime.now().timestamp())}.json"
        
        try:
            import json
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return self._format_success(f"✅ Checkpoint exported to:\n📄 {export_file}")
        except Exception as e:
            return self._format_error(f"❌ Export failed: {str(e)}")
    
    async def handle_diff(self, args: List[str]) -> str:
        """Show changes in a checkpoint"""
        if not args:
            return self._format_error("Usage: /diff <checkpoint-id>")
        
        checkpoint_id = args[0]
        checkpoint = self.checkpoint_manager.get_checkpoint(checkpoint_id)
        
        if not checkpoint:
            return self._format_error(f"Checkpoint '{checkpoint_id}' not found")
        
        # Create diff table
        diff_table = Table(
            title=f"📋 Changes in Checkpoint {checkpoint_id}",
            show_header=True,
            header_style="bold rgb(255,106,0)",
            border_style="rgb(255,106,0)",
            expand=False
        )
        
        diff_table.add_column("File", style="bold cyan", width=40)
        diff_table.add_column("Action", style="yellow", width=15)
        diff_table.add_column("Size Change", style="green", width=15)
        diff_table.add_column("Operation", style="dim", width=30)
        
        for op in checkpoint.operations:
            for file_path in op.files_before.keys():
                before = op.files_before[file_path]
                after = op.files_after.get(file_path)
                
                if not after:
                    continue
                
                # Determine action
                if not before.exists and after.exists:
                    action = "Created"
                    size_change = f"+{after.size} bytes"
                elif before.exists and not after.exists:
                    action = "Deleted"
                    size_change = f"-{before.size} bytes"
                elif before.hash_md5 != after.hash_md5:
                    action = "Modified"
                    size_diff = after.size - before.size
                    size_change = f"{'+' if size_diff >= 0 else ''}{size_diff} bytes"
                else:
                    continue  # No change
                
                # Truncate file path if too long
                display_path = file_path
                if len(display_path) > 38:
                    display_path = "..." + display_path[-35:]
                
                diff_table.add_row(
                    display_path,
                    action,
                    size_change,
                    op.description[:28] + "..." if len(op.description) > 28 else op.description
                )
        
        with self.console.capture() as capture:
            self.console.print(diff_table)
            self.console.print()
            self.console.print(f"[dim]Checkpoint: {checkpoint.description}[/dim]")
            self.console.print(f"[dim]Time: {checkpoint.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
        
        return capture.get()
    
    def _get_command_help(self, command: str) -> str:
        """Get detailed help for a specific command"""
        help_info = {
            'help': "Show available commands or detailed help for a specific command.\nUsage: /help [command]",
            'undo': "Undo the most recent AI operation, restoring files to their previous state.\nUsage: /undo",
            'checkpoints': "Display a list of available checkpoints with their IDs and descriptions.\nUsage: /checkpoints [limit]",
            'revert': "Revert all files to the state they were in at a specific checkpoint.\nUsage: /revert <checkpoint-id>",
            'status': "Show detailed information about the current R-Code session.\nUsage: /status",
            'save': "Create a manual checkpoint with a custom description.\nUsage: /save <description>",
            'clean': "Remove old checkpoints to free up space, keeping the most recent ones.\nUsage: /clean [count]",
            'export': "Export checkpoint data to a JSON file for external analysis.\nUsage: /export <checkpoint-id>",
            'diff': "Show detailed changes made in a specific checkpoint.\nUsage: /diff <checkpoint-id>"
        }
        
        return self._format_info(f"📖 Help: /{command}\n\n{help_info.get(command, 'No help available')}")
    
    async def handle_approve_command(self, args: List[str]) -> str:
        """Approve and execute a specific terminal command"""
        if not args:
            return self._format_error("Usage: /approve-command \"<command>\"")
        
        # Join all args to get the full command (handles quoted strings)
        command = " ".join(args).strip('"\'')
        
        if not command:
            return self._format_error("Please provide a command to approve")
        
        try:
            # Import here to avoid circular imports
            from ..tools.terminal_operations import _terminal_ops
            
            # Execute the command directly (bypassing approval)
            result = _terminal_ops.execute_command(command=command)
            
            # Format execution result
            status_emoji = "✅" if result.exit_code == 0 else "❌"
            
            formatted_result = f"🔓 Command approved and executed:\n\n"
            formatted_result += f"{status_emoji} Command: {result.command}\n"
            formatted_result += f"📊 Status: {result.status.value} (Exit Code: {result.exit_code})\n"
            formatted_result += f"⏱️  Execution Time: {result.execution_time:.2f}s\n"
            formatted_result += f"📁 Working Directory: {result.working_directory}\n"
            
            if result.stdout:
                formatted_result += f"\n📤 STDOUT:\n{result.stdout}\n"
            
            if result.stderr:
                formatted_result += f"\n📥 STDERR:\n{result.stderr}\n"
            
            return self._format_success(formatted_result)
            
        except Exception as e:
            return self._format_error(f"❌ Failed to execute command: {str(e)}")
    
    async def handle_always_approve(self, args: List[str]) -> str:
        """Add a command to the always-approve list"""
        if not args:
            return self._format_error("Usage: /always-approve \"<command>\"")
        
        # Join all args to get the full command
        command = " ".join(args).strip('"\'')
        
        if not command:
            return self._format_error("Please provide a command to add to safe list")
        
        try:
            # Import config manager
            from ..config import config_manager
            
            # Get base command (first word)
            base_command = command.split()[0]
            
            # Load current config
            config = config_manager.load_config()
            safe_commands = config.get("tools", {}).get("terminal_operations", {}).get("safe_commands", [])
            
            if base_command not in safe_commands:
                safe_commands.append(base_command)
                config["tools"]["terminal_operations"]["safe_commands"] = safe_commands
                config_manager.save_config(config)
                
                return self._format_success(
                    f"✅ Added '{base_command}' to safe commands list\n"
                    f"🟢 Future '{base_command}' commands will be auto-approved\n"
                    f"💾 Configuration saved"
                )
            else:
                return self._format_info(f"ℹ️  '{base_command}' is already in the safe commands list")
                
        except Exception as e:
            return self._format_error(f"❌ Failed to update safe commands: {str(e)}")
    
    def _format_success(self, message: str) -> str:
        """Format success message"""
        with self.console.capture() as capture:
            self.console.print(Panel(
                message,
                title="[bold green]Success",
                border_style="green",
                padding=(1, 2)
            ))
        return capture.get()
    
    def _format_error(self, message: str) -> str:
        """Format error message"""
        with self.console.capture() as capture:
            self.console.print(Panel(
                message,
                title="[bold red]Error",
                border_style="red",
                padding=(1, 2)
            ))
        return capture.get()
    
    def _format_info(self, message: str) -> str:
        """Format info message"""
        with self.console.capture() as capture:
            self.console.print(Panel(
                message,
                title="[bold cyan]Info",
                border_style="cyan",
                padding=(1, 2)
            ))
        return capture.get()
    
    def _format_unknown_command(self, command: str) -> str:
        """Format unknown command message"""
        return self._format_error(
            f"Unknown command: /{command}\n\n"
            "Type /help to see available commands."
        )
