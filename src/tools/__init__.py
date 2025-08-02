"""
R-Code Tools Package
===================

Professional tools for the R-Code AI assistant including web search,
file operations, terminal management, and other utilities integrated with LangGraph.
"""

from .web_search import (
    web_search,
    search_coding_help,
    get_web_search_tools,
    is_web_search_available,
    search_web
)

from .file_operations import (
    read_file,
    write_file,
    create_and_open_file,
    live_write_file,
    search_in_file,
    replace_in_file,
    delete_file,
    create_directory,
    delete_directory,
    list_files,
    check_mcp_installation,
    get_file_operation_tools
)

from .terminal_operations import (
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
    get_environment_variables,
    get_terminal_operation_tools
)

__all__ = [
    # Web search tools
    "web_search",
    "search_coding_help", 
    "get_web_search_tools",
    "is_web_search_available",
    "search_web",
    
    # File operation tools
    "read_file",
    "write_file",
    "create_and_open_file",
    "live_write_file",
    "search_in_file",
    "replace_in_file",
    "delete_file",
    "create_directory",
    "delete_directory",
    "list_files",
    "check_mcp_installation",
    "get_file_operation_tools",
    
    # Terminal operation tools
    "execute_command",
    "get_terminal_state",
    "get_running_processes",
    "kill_process",
    "get_system_info",
    "get_command_history",
    "change_directory",
    "create_terminal_session",
    "list_terminal_sessions",
    "set_environment_variable",
    "get_environment_variables",
    "get_terminal_operation_tools"
]
