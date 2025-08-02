"""
R-Code Terminal Operations Tool
==============================

World-class terminal management and command execution system for R-Code AI assistant.
Provides comprehensive terminal control, command execution, output streaming, process management,
and terminal state awareness across all platforms.
"""

import os
import sys
import subprocess
import threading
import time
import signal
import json
import shlex
import queue
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import asyncio
import psutil
from langchain_core.tools import tool


class CommandStatus(Enum):
    """Command execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ProcessPriority(Enum):
    """Process priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    REALTIME = "realtime"


@dataclass
class CommandResult:
    """Comprehensive command execution result"""
    command: str
    status: CommandStatus
    exit_code: Optional[int]
    stdout: str
    stderr: str
    execution_time: float
    start_time: datetime
    end_time: Optional[datetime]
    working_directory: str
    environment: Dict[str, str]
    process_id: Optional[int]
    memory_usage: Optional[float]
    cpu_usage: Optional[float]
    error_message: Optional[str] = None


@dataclass
class ProcessInfo:
    """Information about running process"""
    pid: int
    command: str
    status: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    start_time: datetime
    working_directory: str
    user: str
    children: List[int]


class TerminalSession:
    """Manages a persistent terminal session"""
    
    def __init__(self, session_id: str, working_dir: str = None, shell: str = None):
        self.session_id = session_id
        self.working_dir = working_dir or os.getcwd()
        self.shell = shell or self._get_default_shell()
        self.environment = os.environ.copy()
        self.command_history = deque(maxlen=1000)
        self.active_processes = {}
        self.session_start_time = datetime.now()
        self.last_activity = datetime.now()
        
    def _get_default_shell(self) -> str:
        """Get default shell for the platform"""
        if sys.platform == "win32":
            return os.environ.get("COMSPEC", "cmd.exe")
        else:
            return os.environ.get("SHELL", "/bin/bash")
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def add_to_history(self, command: str, result: CommandResult):
        """Add command and result to history"""
        self.command_history.append({
            "timestamp": datetime.now(),
            "command": command,
            "result": asdict(result)
        })
        self.update_activity()


class RCodeTerminalOperations:
    """World-class terminal operations manager for R-Code AI assistant"""
    
    def __init__(self, max_output_size: int = 10 * 1024 * 1024):  # 10MB default
        """
        Initialize terminal operations manager
        
        Args:
            max_output_size: Maximum size of command output to capture (bytes)
        """
        self.max_output_size = max_output_size
        self.sessions: Dict[str, TerminalSession] = {}
        self.active_processes: Dict[int, subprocess.Popen] = {}
        self.command_queue = queue.Queue()
        self.output_callbacks: Dict[str, Callable] = {}
        self.global_environment = os.environ.copy()
        self.command_timeout_default = 300  # 5 minutes default timeout
        
        # Create default session
        self.create_session("default")
        
        # Platform-specific configurations
        self.is_windows = sys.platform == "win32"
        self.shell_flags = self._get_shell_flags()
    
    def _get_shell_flags(self) -> List[str]:
        """Get appropriate shell flags for the platform"""
        if self.is_windows:
            return ["/c"]  # cmd.exe flags
        else:
            return ["-c"]  # bash/sh flags
    
    def create_session(self, session_id: str, working_dir: str = None, 
                      shell: str = None, environment: Dict[str, str] = None) -> Dict[str, Any]:
        """Create a new terminal session"""
        try:
            if session_id in self.sessions:
                return {
                    "success": False,
                    "error": f"Session '{session_id}' already exists"
                }
            
            session = TerminalSession(session_id, working_dir, shell)
            
            if environment:
                session.environment.update(environment)
            
            self.sessions[session_id] = session
            
            return {
                "success": True,
                "session_id": session_id,
                "working_directory": session.working_dir,
                "shell": session.shell,
                "message": f"Created terminal session '{session_id}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create session '{session_id}': {str(e)}"
            }
    
    def get_session(self, session_id: str = "default") -> Optional[TerminalSession]:
        """Get terminal session by ID"""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> Dict[str, Any]:
        """List all active terminal sessions"""
        sessions_info = []
        
        for session_id, session in self.sessions.items():
            sessions_info.append({
                "session_id": session_id,
                "working_directory": session.working_dir,
                "shell": session.shell,
                "start_time": session.session_start_time.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "command_count": len(session.command_history),
                "active_processes": len(session.active_processes)
            })
        
        return {
            "success": True,
            "sessions": sessions_info,
            "total_sessions": len(sessions_info)
        }
    
    def execute_command(self, command: str, session_id: str = "default", 
                       timeout: Optional[int] = None, working_dir: str = None,
                       capture_output: bool = True, stream_output: bool = False,
                       environment: Dict[str, str] = None,
                       priority: ProcessPriority = ProcessPriority.NORMAL) -> CommandResult:
        """
        Execute a command with comprehensive monitoring and control
        
        Args:
            command: Command to execute
            session_id: Terminal session ID
            timeout: Command timeout in seconds
            working_dir: Working directory for command
            capture_output: Whether to capture stdout/stderr
            stream_output: Whether to stream output in real-time
            environment: Additional environment variables
            priority: Process priority level
            
        Returns:
            CommandResult with execution details
        """
        start_time = datetime.now()
        session = self.get_session(session_id)
        
        if not session:
            return CommandResult(
                command=command,
                status=CommandStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr=f"Session '{session_id}' not found",
                execution_time=0.0,
                start_time=start_time,
                end_time=datetime.now(),
                working_directory="",
                environment={},
                process_id=None,
                memory_usage=None,
                cpu_usage=None,
                error_message=f"Session '{session_id}' not found"
            )
        
        # Prepare command execution environment
        exec_env = session.environment.copy()
        if environment:
            exec_env.update(environment)
        
        work_dir = working_dir or session.working_dir
        timeout = timeout or self.command_timeout_default
        
        try:
            # Prepare command for execution
            if self.is_windows:
                # Windows command preparation
                full_command = [session.shell] + self.shell_flags + [command]
            else:
                # Unix command preparation
                full_command = [session.shell] + self.shell_flags + [command]
            
            # Start process with comprehensive monitoring
            process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE if capture_output else None,
                stderr=subprocess.PIPE if capture_output else None,
                stdin=subprocess.PIPE,
                cwd=work_dir,
                env=exec_env,
                text=True,
                bufsize=0 if stream_output else -1,
                universal_newlines=True,
                shell=False
            )
            
            self.active_processes[process.pid] = process
            session.active_processes[process.pid] = process
            
            # Set process priority
            self._set_process_priority(process.pid, priority)
            
            # Monitor process execution
            stdout_lines = []
            stderr_lines = []
            
            if capture_output:
                if stream_output:
                    stdout_data, stderr_data = self._stream_process_output(
                        process, timeout, stdout_lines, stderr_lines
                    )
                else:
                    try:
                        stdout_data, stderr_data = process.communicate(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        stdout_data, stderr_data = process.communicate()
                        status = CommandStatus.TIMEOUT
                    else:
                        status = CommandStatus.COMPLETED if process.returncode == 0 else CommandStatus.FAILED
            else:
                process.wait(timeout=timeout)
                stdout_data = stderr_data = ""
                status = CommandStatus.COMPLETED if process.returncode == 0 else CommandStatus.FAILED
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Get process resource usage
            memory_usage, cpu_usage = self._get_process_resources(process.pid)
            
            # Clean up
            if process.pid in self.active_processes:
                del self.active_processes[process.pid]
            if process.pid in session.active_processes:
                del session.active_processes[process.pid]
            
            # Create result
            result = CommandResult(
                command=command,
                status=status,
                exit_code=process.returncode,
                stdout=stdout_data[:self.max_output_size] if stdout_data else "",
                stderr=stderr_data[:self.max_output_size] if stderr_data else "",
                execution_time=execution_time,
                start_time=start_time,
                end_time=end_time,
                working_directory=work_dir,
                environment=exec_env,
                process_id=process.pid,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage
            )
            
            # Add to session history
            session.add_to_history(command, result)
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            error_result = CommandResult(
                command=command,
                status=CommandStatus.FAILED,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                execution_time=execution_time,
                start_time=start_time,
                end_time=end_time,
                working_directory=work_dir,
                environment=exec_env,
                process_id=None,
                memory_usage=None,
                cpu_usage=None,
                error_message=str(e)
            )
            
            session.add_to_history(command, error_result)
            return error_result
    
    def _set_process_priority(self, pid: int, priority: ProcessPriority):
        """Set process priority"""
        try:
            process = psutil.Process(pid)
            
            if self.is_windows:
                priority_map = {
                    ProcessPriority.LOW: psutil.BELOW_NORMAL_PRIORITY_CLASS,
                    ProcessPriority.NORMAL: psutil.NORMAL_PRIORITY_CLASS,
                    ProcessPriority.HIGH: psutil.HIGH_PRIORITY_CLASS,
                    ProcessPriority.REALTIME: psutil.REALTIME_PRIORITY_CLASS
                }
                process.nice(priority_map[priority])
            else:
                priority_map = {
                    ProcessPriority.LOW: 10,
                    ProcessPriority.NORMAL: 0,
                    ProcessPriority.HIGH: -10,
                    ProcessPriority.REALTIME: -20
                }
                process.nice(priority_map[priority])
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, PermissionError):
            pass  # Ignore priority setting failures
    
    def _stream_process_output(self, process: subprocess.Popen, timeout: int,
                             stdout_lines: List[str], stderr_lines: List[str]) -> Tuple[str, str]:
        """Stream process output in real-time"""
        import select
        
        start_time = time.time()
        
        while process.poll() is None:
            if time.time() - start_time > timeout:
                process.kill()
                break
            
            if not self.is_windows and hasattr(select, 'select'):
                # Unix-like systems with select
                ready, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
                
                for stream in ready:
                    line = stream.readline()
                    if line:
                        if stream == process.stdout:
                            stdout_lines.append(line)
                            print(f"STDOUT: {line.rstrip()}", flush=True)
                        else:
                            stderr_lines.append(line)
                            print(f"STDERR: {line.rstrip()}", flush=True)
            else:
                # Windows or systems without select - use threading
                time.sleep(0.1)
        
        # Get remaining output
        remaining_stdout, remaining_stderr = process.communicate()
        
        if remaining_stdout:
            stdout_lines.append(remaining_stdout)
        if remaining_stderr:
            stderr_lines.append(remaining_stderr)
        
        return ''.join(stdout_lines), ''.join(stderr_lines)
    
    def _get_process_resources(self, pid: int) -> Tuple[Optional[float], Optional[float]]:
        """Get process memory and CPU usage"""
        try:
            process = psutil.Process(pid)
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
            return memory_mb, cpu_percent
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None, None
    
    def get_running_processes(self, session_id: str = "default") -> Dict[str, Any]:
        """Get information about running processes"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 
                                           'memory_percent', 'memory_info', 'create_time',
                                           'cwd', 'username']):
                try:
                    pinfo = proc.info
                    memory_mb = pinfo['memory_info'].rss / 1024 / 1024 if pinfo['memory_info'] else 0
                    
                    process_info = ProcessInfo(
                        pid=pinfo['pid'],
                        command=pinfo['name'],
                        status=pinfo['status'],
                        cpu_percent=pinfo['cpu_percent'] or 0,
                        memory_percent=pinfo['memory_percent'] or 0,
                        memory_mb=memory_mb,
                        start_time=datetime.fromtimestamp(pinfo['create_time']) if pinfo['create_time'] else datetime.now(),
                        working_directory=pinfo['cwd'] or "Unknown",
                        user=pinfo['username'] or "Unknown",
                        children=[]
                    )
                    
                    # Get child processes
                    try:
                        children = proc.children()
                        process_info.children = [child.pid for child in children]
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                    
                    processes.append(asdict(process_info))
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return {
                "success": True,
                "processes": processes,
                "total_processes": len(processes),
                "session_id": session_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get running processes: {str(e)}"
            }
    
    def kill_process(self, pid: int, force: bool = False) -> Dict[str, Any]:
        """Kill a process by PID"""
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            
            if force:
                process.kill()  # SIGKILL
                action = "forcefully killed"
            else:
                process.terminate()  # SIGTERM
                action = "terminated"
                
                # Wait for graceful termination
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    process.kill()
                    action = "killed after timeout"
            
            # Clean up from active processes
            if pid in self.active_processes:
                del self.active_processes[pid]
            
            for session in self.sessions.values():
                if pid in session.active_processes:
                    del session.active_processes[pid]
            
            return {
                "success": True,
                "message": f"Process {pid} ({process_name}) {action}",
                "pid": pid,
                "process_name": process_name
            }
            
        except psutil.NoSuchProcess:
            return {
                "success": False,
                "error": f"Process {pid} not found"
            }
        except psutil.AccessDenied:
            return {
                "success": False,
                "error": f"Access denied to kill process {pid}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to kill process {pid}: {str(e)}"
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            # CPU information
            cpu_info = {
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "cpu_freq": asdict(psutil.cpu_freq()) if psutil.cpu_freq() else None
            }
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_info = {
                "total_gb": memory.total / 1024 / 1024 / 1024,
                "available_gb": memory.available / 1024 / 1024 / 1024,
                "used_gb": memory.used / 1024 / 1024 / 1024,
                "percent_used": memory.percent
            }
            
            # Disk information
            disk_info = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "total_gb": usage.total / 1024 / 1024 / 1024,
                        "used_gb": usage.used / 1024 / 1024 / 1024,
                        "free_gb": usage.free / 1024 / 1024 / 1024,
                        "percent_used": (usage.used / usage.total) * 100
                    })
                except PermissionError:
                    continue
            
            # Network information
            network_info = psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            
            # System uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            return {
                "success": True,
                "system": {
                    "platform": sys.platform,
                    "python_version": sys.version,
                    "boot_time": boot_time.isoformat(),
                    "uptime_seconds": uptime.total_seconds(),
                    "current_working_directory": os.getcwd(),
                    "user": os.getenv("USER") or os.getenv("USERNAME") or "Unknown"
                },
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get system info: {str(e)}"
            }
    
    def get_command_history(self, session_id: str = "default", limit: int = 50) -> Dict[str, Any]:
        """Get command history for a session"""
        session = self.get_session(session_id)
        
        if not session:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found"
            }
        
        history = list(session.command_history)[-limit:]
        
        return {
            "success": True,
            "session_id": session_id,
            "history": [
                {
                    "timestamp": entry["timestamp"].isoformat(),
                    "command": entry["command"],
                    "status": entry["result"]["status"],
                    "exit_code": entry["result"]["exit_code"],
                    "execution_time": entry["result"]["execution_time"]
                }
                for entry in history
            ],
            "total_commands": len(session.command_history)
        }
    
    def clear_session_history(self, session_id: str = "default") -> Dict[str, Any]:
        """Clear command history for a session"""
        session = self.get_session(session_id)
        
        if not session:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found"
            }
        
        history_count = len(session.command_history)
        session.command_history.clear()
        
        return {
            "success": True,
            "message": f"Cleared {history_count} commands from session '{session_id}' history"
        }
    
    def change_directory(self, path: str, session_id: str = "default") -> Dict[str, Any]:
        """Change working directory for a session"""
        session = self.get_session(session_id)
        
        if not session:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found"
            }
        
        try:
            # Resolve and validate path
            new_path = Path(path).resolve()
            
            if not new_path.exists():
                return {
                    "success": False,
                    "error": f"Directory does not exist: {path}"
                }
            
            if not new_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {path}"
                }
            
            old_path = session.working_dir
            session.working_dir = str(new_path)
            session.update_activity()
            
            return {
                "success": True,
                "message": f"Changed directory from '{old_path}' to '{new_path}'",
                "old_directory": old_path,
                "new_directory": str(new_path),
                "session_id": session_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to change directory: {str(e)}"
            }
    
    def get_environment_variables(self, session_id: str = "default") -> Dict[str, Any]:
        """Get environment variables for a session"""
        session = self.get_session(session_id)
        
        if not session:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found"
            }
        
        return {
            "success": True,
            "session_id": session_id,
            "environment": dict(session.environment),
            "variable_count": len(session.environment)
        }
    
    def set_environment_variable(self, name: str, value: str, 
                                session_id: str = "default") -> Dict[str, Any]:
        """Set environment variable for a session"""
        session = self.get_session(session_id)
        
        if not session:
            return {
                "success": False,
                "error": f"Session '{session_id}' not found"
            }
        
        old_value = session.environment.get(name)
        session.environment[name] = value
        session.update_activity()
        
        return {
            "success": True,
            "message": f"Set environment variable '{name}' = '{value}'",
            "variable_name": name,
            "new_value": value,
            "old_value": old_value,
            "session_id": session_id
        }


# Global instance
_terminal_ops = RCodeTerminalOperations()


@tool
def execute_command(command: str, session_id: str = "default", 
                   timeout: int = 300, stream_output: bool = False) -> str:
    """
    Execute a terminal command with comprehensive monitoring and output capture.
    
    This is the primary tool for running terminal commands. It provides:
    - Cross-platform command execution
    - Real-time output streaming (optional)
    - Comprehensive error handling
    - Resource usage monitoring
    - Command history tracking
    
    Use this tool to run any terminal command like 'ls', 'npm install', 'python script.py', etc.
    
    Args:
        command: The command to execute (e.g., "ls -la", "python --version")
        session_id: Terminal session ID (default: "default")
        timeout: Command timeout in seconds (default: 300)
        stream_output: Whether to stream output in real-time (default: False)
        
    Returns:
        Formatted string with command execution results
    """
    result = _terminal_ops.execute_command(
        command=command,
        session_id=session_id,
        timeout=timeout,
        stream_output=stream_output
    )
    
    status_emoji = {
        CommandStatus.COMPLETED: "✅",
        CommandStatus.FAILED: "❌",
        CommandStatus.TIMEOUT: "⏰",
        CommandStatus.CANCELLED: "🚫"
    }
    
    emoji = status_emoji.get(result.status, "❓")
    
    formatted_result = f"{emoji} Command: {result.command}\n"
    formatted_result += f"📊 Status: {result.status.value} (Exit Code: {result.exit_code})\n"
    formatted_result += f"⏱️  Execution Time: {result.execution_time:.2f}s\n"
    formatted_result += f"📁 Working Directory: {result.working_directory}\n"
    
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


@tool
def get_terminal_state(session_id: str = "default") -> str:
    """
    Get comprehensive information about the current terminal state.
    
    This tool provides detailed information about:
    - Current working directory
    - Environment variables
    - Active processes
    - Command history summary
    - Session information
    
    Use this tool to understand the current state of the terminal environment.
    
    Args:
        session_id: Terminal session ID (default: "default")
        
    Returns:
        Formatted string with terminal state information
    """
    session = _terminal_ops.get_session(session_id)
    
    if not session:
        return f"❌ Session '{session_id}' not found"
    
    result = f"🖥️  Terminal State - Session '{session_id}'\n"
    result += f"{'=' * 50}\n\n"
    
    result += f"📁 Working Directory: {session.working_dir}\n"
    result += f"🐚 Shell: {session.shell}\n"
    result += f"🕐 Session Started: {session.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    result += f"📝 Last Activity: {session.last_activity.strftime('%Y-%m-%d %H:%M:%S')}\n"
    result += f"📊 Commands in History: {len(session.command_history)}\n"
    result += f"🔄 Active Processes: {len(session.active_processes)}\n\n"
    
    # Environment variables summary
    env_count = len(session.environment)
    result += f"🌐 Environment Variables: {env_count} total\n"
    
    # Show important environment variables
    important_vars = ['PATH', 'HOME', 'USER', 'USERNAME', 'PYTHON_PATH', 'NODE_PATH']
    for var in important_vars:
        if var in session.environment:
            value = session.environment[var]
            if len(value) > 100:
                value = value[:97] + "..."
            result += f"   {var}: {value}\n"
    
    # Recent command history
    if session.command_history:
        result += f"\n📜 Recent Commands (last 5):\n"
        recent_commands = list(session.command_history)[-5:]
        for i, entry in enumerate(recent_commands, 1):
            timestamp = entry["timestamp"].strftime('%H:%M:%S')
            command = entry["command"][:50] + "..." if len(entry["command"]) > 50 else entry["command"]
            status = entry["result"]["status"]
            result += f"   {i}. [{timestamp}] {command} ({status})\n"
    
    return result


@tool
def get_running_processes(session_id: str = "default", limit: int = 20) -> str:
    """
    Get information about currently running processes on the system.
    
    This tool provides detailed information about:
    - Process IDs and names
    - CPU and memory usage
    - Process status and start times
    - Working directories
    - Child processes
    
    Use this tool to monitor system resource usage and identify running programs.
    
    Args:
        session_id: Terminal session ID (default: "default")
        limit: Maximum number of processes to show (default: 20)
        
    Returns:
        Formatted string with process information
    """
    result_data = _terminal_ops.get_running_processes(session_id)
    
    if not result_data["success"]:
        return f"❌ Error: {result_data['error']}"
    
    processes = result_data["processes"]
    
    # Sort by CPU usage (descending)
    processes.sort(key=lambda p: p["cpu_percent"], reverse=True)
    
    result = f"🔄 Running Processes (Top {limit} by CPU usage)\n"
    result += f"{'=' * 70}\n\n"
    result += f"📊 Total Processes: {result_data['total_processes']}\n\n"
    
    # Header
    result += f"{'PID':>8} {'Name':25} {'CPU%':>6} {'MEM%':>6} {'Memory':>8} {'Status':12}\n"
    result += f"{'-' * 70}\n"
    
    # Show top processes
    for process in processes[:limit]:
        result += f"{process['pid']:>8} "
        result += f"{process['command'][:24]:25} "
        result += f"{process['cpu_percent']:>6.1f} "
        result += f"{process['memory_percent']:>6.1f} "
        result += f"{process['memory_mb']:>7.1f}M "
        result += f"{process['status']:12}\n"
        
        # Show child processes if any
        if process['children']:
            result += f"         └─ Children: {', '.join(map(str, process['children']))}\n"
    
    return result


@tool
def kill_process(pid: int, force: bool = False) -> str:
    """
    Terminate a process by its Process ID (PID).
    
    This tool allows you to stop running processes:
    - Graceful termination (SIGTERM) by default
    - Forceful termination (SIGKILL) if force=True
    - Automatic cleanup of process tracking
    
    Use this tool to stop unresponsive programs or clean up processes.
    
    Args:
        pid: Process ID to terminate
        force: Whether to force kill the process (default: False)
        
    Returns:
        Formatted string with termination result
    """
    result = _terminal_ops.kill_process(pid, force)
    
    if result["success"]:
        return f"✅ {result['message']}"
    else:
        return f"❌ Error: {result['error']}"


@tool
def get_system_info() -> str:
    """
    Get comprehensive system information and resource usage.
    
    This tool provides detailed information about:
    - CPU usage and specifications
    - Memory usage and availability
    - Disk space and partitions
    - Network statistics
    - System uptime and platform info
    
    Use this tool to monitor system health and resource availability.
    
    Returns:
        Formatted string with system information
    """
    result_data = _terminal_ops.get_system_info()
    
    if not result_data["success"]:
        return f"❌ Error: {result_data['error']}"
    
    data = result_data
    result = f"💻 System Information\n"
    result += f"{'=' * 50}\n\n"
    
    # System info
    system = data["system"]
    result += f"🖥️  Platform: {system['platform']}\n"
    result += f"🐍 Python: {system['python_version'].split()[0]}\n"
    result += f"👤 User: {system['user']}\n"
    result += f"📁 Working Dir: {system['current_working_directory']}\n"
    result += f"⏰ Boot Time: {system['boot_time'][:19]}\n"
    
    uptime_hours = system['uptime_seconds'] / 3600
    result += f"🕐 Uptime: {uptime_hours:.1f} hours\n\n"
    
    # CPU info
    cpu = data["cpu"]
    result += f"🔄 CPU Information:\n"
    result += f"   Cores: {cpu['physical_cores']} physical, {cpu['logical_cores']} logical\n"
    result += f"   Usage: {cpu['cpu_percent']:.1f}%\n"
    if cpu['cpu_freq']:
        result += f"   Frequency: {cpu['cpu_freq']['current']:.0f} MHz\n"
    result += "\n"
    
    # Memory info
    memory = data["memory"]
    result += f"💾 Memory Information:\n"
    result += f"   Total: {memory['total_gb']:.1f} GB\n"
    result += f"   Used: {memory['used_gb']:.1f} GB ({memory['percent_used']:.1f}%)\n"
    result += f"   Available: {memory['available_gb']:.1f} GB\n\n"
    
    # Disk info
    if data["disk"]:
        result += f"💿 Disk Information:\n"
        for disk in data["disk"]:
            result += f"   {disk['device']} ({disk['filesystem']})\n"
            result += f"      Mount: {disk['mountpoint']}\n"
            result += f"      Total: {disk['total_gb']:.1f} GB\n"
            result += f"      Used: {disk['used_gb']:.1f} GB ({disk['percent_used']:.1f}%)\n"
            result += f"      Free: {disk['free_gb']:.1f} GB\n"
    
    return result


@tool
def get_command_history(session_id: str = "default", limit: int = 20) -> str:
    """
    Get the command history for a terminal session.
    
    This tool shows:
    - Recently executed commands
    - Execution timestamps
    - Command status and exit codes
    - Execution times
    
    Use this tool to review what commands have been run and their results.
    
    Args:
        session_id: Terminal session ID (default: "default")
        limit: Maximum number of commands to show (default: 20)
        
    Returns:
        Formatted string with command history
    """
    result_data = _terminal_ops.get_command_history(session_id, limit)
    
    if not result_data["success"]:
        return f"❌ Error: {result_data['error']}"
    
    history = result_data["history"]
    
    if not history:
        return f"📜 No command history found for session '{session_id}'"
    
    result = f"📜 Command History - Session '{session_id}'\n"
    result += f"{'=' * 60}\n\n"
    result += f"Showing last {len(history)} of {result_data['total_commands']} commands:\n\n"
    
    for i, entry in enumerate(reversed(history), 1):
        timestamp = entry["timestamp"][:19]  # Remove microseconds
        command = entry["command"]
        status = entry["status"]
        exit_code = entry["exit_code"]
        exec_time = entry["execution_time"]
        
        status_emoji = "✅" if status == "completed" else "❌"
        
        result += f"{i:2}. [{timestamp}] {status_emoji}\n"
        result += f"    Command: {command}\n"
        result += f"    Status: {status} (Exit: {exit_code}) - {exec_time:.2f}s\n\n"
    
    return result


@tool
def change_directory(path: str, session_id: str = "default") -> str:
    """
    Change the working directory for a terminal session.
    
    This tool allows you to navigate the file system:
    - Change to absolute or relative paths
    - Validates directory exists
    - Updates session working directory
    - Affects future command execution
    
    Use this tool to navigate to different directories before running commands.
    
    Args:
        path: Directory path to change to
        session_id: Terminal session ID (default: "default")
        
    Returns:
        Formatted string with directory change result
    """
    result = _terminal_ops.change_directory(path, session_id)
    
    if result["success"]:
        return f"✅ {result['message']}"
    else:
        return f"❌ Error: {result['error']}"


@tool  
def create_terminal_session(session_id: str, working_dir: str = None, shell: str = None) -> str:
    """
    Create a new terminal session with custom configuration.
    
    This tool allows you to create isolated terminal environments:
    - Custom working directories
    - Different shell environments
    - Separate command histories
    - Independent environment variables
    
    Use this tool to create specialized environments for different tasks.
    
    Args:
        session_id: Unique identifier for the new session
        working_dir: Initial working directory (default: current directory)
        shell: Shell to use (default: system default)
        
    Returns:
        Formatted string with session creation result
    """
    result = _terminal_ops.create_session(session_id, working_dir, shell)
    
    if result["success"]:
        return f"✅ {result['message']}\n📁 Working Directory: {result['working_directory']}\n🐚 Shell: {result['shell']}"
    else:
        return f"❌ Error: {result['error']}"


@tool
def list_terminal_sessions() -> str:
    """
    List all active terminal sessions and their information.
    
    This tool shows:
    - Session IDs and configurations
    - Working directories
    - Shell types
    - Activity timestamps
    - Command counts
    
    Use this tool to see all available terminal sessions.
    
    Returns:
        Formatted string with session list
    """
    result_data = _terminal_ops.list_sessions()
    
    if not result_data["success"]:
        return f"❌ Error: {result_data.get('error', 'Unknown error')}"
    
    sessions = result_data["sessions"]
    
    if not sessions:
        return "📝 No active terminal sessions found"
    
    result = f"📝 Active Terminal Sessions ({result_data['total_sessions']})\n"
    result += f"{'=' * 60}\n\n"
    
    for session in sessions:
        result += f"🖥️  Session: {session['session_id']}\n"
        result += f"   📁 Directory: {session['working_directory']}\n"
        result += f"   🐚 Shell: {session['shell']}\n"
        result += f"   🕐 Started: {session['start_time'][:19]}\n"
        result += f"   📝 Last Activity: {session['last_activity'][:19]}\n"
        result += f"   📊 Commands: {session['command_count']}\n"
        result += f"   🔄 Active Processes: {session['active_processes']}\n\n"
    
    return result


@tool
def set_environment_variable(name: str, value: str, session_id: str = "default") -> str:
    """
    Set an environment variable for a terminal session.
    
    This tool allows you to:
    - Set custom environment variables
    - Configure application settings
    - Modify PATH and other system variables
    - Affect command execution environment
    
    Use this tool to configure the environment for your commands.
    
    Args:
        name: Environment variable name
        value: Environment variable value
        session_id: Terminal session ID (default: "default")
        
    Returns:
        Formatted string with operation result
    """
    result = _terminal_ops.set_environment_variable(name, value, session_id)
    
    if result["success"]:
        old_value = result.get("old_value")
        if old_value:
            return f"✅ {result['message']}\n📝 Previous value: {old_value}"
        else:
            return f"✅ {result['message']}\n📝 New variable created"
    else:
        return f"❌ Error: {result['error']}"


@tool
def get_environment_variables(session_id: str = "default", filter_pattern: str = None) -> str:
    """
    Get environment variables for a terminal session.
    
    This tool shows:
    - All environment variables and their values
    - Optional filtering by pattern
    - Variable counts
    - Important system variables
    
    Use this tool to inspect the current environment configuration.
    
    Args:
        session_id: Terminal session ID (default: "default")
        filter_pattern: Optional pattern to filter variable names (case-insensitive)
        
    Returns:
        Formatted string with environment variables
    """
    result_data = _terminal_ops.get_environment_variables(session_id)
    
    if not result_data["success"]:
        return f"❌ Error: {result_data['error']}"
    
    env_vars = result_data["environment"]
    
    # Apply filter if provided
    if filter_pattern:
        filtered_vars = {
            k: v for k, v in env_vars.items() 
            if filter_pattern.lower() in k.lower()
        }
    else:
        filtered_vars = env_vars
    
    result = f"🌐 Environment Variables - Session '{session_id}'\n"
    result += f"{'=' * 60}\n\n"
    result += f"📊 Total Variables: {result_data['variable_count']}\n"
    
    if filter_pattern:
        result += f"🔍 Filtered by: '{filter_pattern}' ({len(filtered_vars)} matches)\n"
    
    result += "\n"
    
    # Sort variables by name
    for name in sorted(filtered_vars.keys()):
        value = filtered_vars[name]
        
        # Truncate very long values
        if len(value) > 100:
            display_value = value[:97] + "..."
        else:
            display_value = value
        
        result += f"{name}: {display_value}\n"
    
    return result


def get_terminal_operation_tools() -> List:
    """
    Get list of terminal operation tools for LangGraph integration
    
    Returns:
        List of terminal operation tools
    """
    return [
        execute_command,
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
