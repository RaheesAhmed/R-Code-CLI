# 📖 R-Code CLI User Guide

Complete guide to using R-Code CLI's advanced features and capabilities.

## 🎯 Overview

R-Code CLI is a context-aware AI coding assistant that understands your entire project and helps you write, debug, and improve code while preventing conflicts and mistakes.

## 🧠 Core Concepts

### **Context Awareness**

R-Code CLI analyzes your entire project to understand:

- **File Structure**: Organization and architecture patterns
- **Dependencies**: Import/export relationships between files
- **Code Patterns**: Naming conventions and coding standards
- **Project Type**: Framework detection (Flask, React, etc.)
- **Quality Metrics**: Code complexity and maintainability

### **Time Travel System**

- **Automatic Checkpoints**: Created before major operations
- **Manual Checkpoints**: Save points you create with `/save`
- **Surgical Undo**: Revert specific changes without losing other work
- **Change Visualization**: See exactly what changed between checkpoints

### **Human-in-the-Loop Security**

- **Smart Risk Analysis**: Automatically assess command safety
- **Selective Approval**: Only dangerous operations require confirmation
- **Learning System**: Remembers your approval preferences
- **Configurable Policies**: Customize security levels for your needs

## 💬 Interactive Chat Interface

### **Natural Language Conversations**

R-Code CLI understands natural language requests:

```
› Create a user authentication system with JWT tokens
› Fix the performance issue in the database queries
› Add error handling to all API endpoints
› Refactor this code to follow SOLID principles
```

### **Context-Aware Responses**

The AI provides responses based on your project:

```
› Add logging to the application

🔍 I can see you're using a Flask application with the standard Python logging module.

I'll add structured logging that follows your existing patterns:
- Configure logging in your app factory
- Add request logging middleware
- Use the same log format as your existing code
- Include correlation IDs for request tracking

Would you like me to proceed with this approach?
```

## 🔧 Slash Commands

### **Essential Commands**

| Command            | Purpose                             | Example   |
| ------------------ | ----------------------------------- | --------- |
| `/help`            | Show all available commands         | `/help`   |
| `/status`          | Display current session information | `/status` |
| `/exit` or `/quit` | End the R-Code session              | `/exit`   |

### **Checkpoint Management**

| Command                | Purpose                            | Example                           |
| ---------------------- | ---------------------------------- | --------------------------------- |
| `/save <description>`  | Create a manual checkpoint         | `/save "Before refactoring auth"` |
| `/checkpoints [limit]` | List available checkpoints         | `/checkpoints 10`                 |
| `/undo`                | Undo the last AI operation         | `/undo`                           |
| `/redo`                | Redo a previously undone operation | `/redo`                           |
| `/revert <id>`         | Revert to a specific checkpoint    | `/revert cp_20250208_142301`      |
| `/diff <id>`           | Show changes in a checkpoint       | `/diff cp_20250208_142301`        |

### **Session Management**

| Command          | Purpose                          | Example                      |
| ---------------- | -------------------------------- | ---------------------------- |
| `/clean [count]` | Clean old checkpoints            | `/clean 5`                   |
| `/export <id>`   | Export checkpoint data           | `/export cp_20250208_142301` |
| `/reset`         | Reset session (keep checkpoints) | `/reset`                     |
| `/clear`         | Clear chat history               | `/clear`                     |

## 🛡️ Security Features

### **Human Approval System**

When R-Code wants to execute potentially dangerous commands, you'll see a detailed approval prompt:

```
🔐 Human Approval Required
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI wants to execute a terminal command                        │
│                                                                 │
│ Command: rm -rf temp_directory                                  │
│ Directory: /your/project/path                                   │
│ Risk Level: 🚨 Dangerous                                        │
│                                                                 │
│ Analysis:                                                       │
│ • Recursive deletion command                                    │
│ • Affects multiple files                                        │
│ • Cannot be easily undone                                       │
│                                                                 │
│ Recommendation: Consider using 'rm temp_directory/*' instead    │
└─────────────────────────────────────────────────────────────────┘

Your response (approve/deny/modify/always-approve/always-deny):
```

### **Approval Options**

- **approve**: Execute the command as-is
- **deny**: Block the command completely
- **modify**: Edit the command before execution
- **always-approve**: Add to safe commands list
- **always-deny**: Add to blocked commands list

### **Risk Levels**

- **🟢 Safe**: Low-risk operations (reading files, safe commands)
- **🟡 Caution**: Medium-risk operations (file modifications)
- **🟠 Warning**: High-risk operations (system changes)
- **🚨 Dangerous**: Very high-risk operations (deletion, system commands)

## 🎨 Customization

### **Basic Configuration**

Create `.rcode/config.json` in your project root:

```json
{
  "models": {
    "primary": "claude",
    "fallback": "openai"
  },
  "tools": {
    "file_operations": {
      "enabled": true,
      "auto_backup": true,
      "backup_limit": 10
    },
    "terminal_operations": {
      "enabled": true,
      "human_approval_required": true,
      "safe_commands": ["ls", "pwd", "git status"],
      "dangerous_commands": ["rm", "sudo", "shutdown"]
    },
    "web_search": {
      "enabled": true,
      "provider": "duckduckgo"
    }
  },
  "context": {
    "auto_analyze": true,
    "cache_enabled": true,
    "max_file_size_mb": 1,
    "excluded_dirs": [".git", "node_modules", "__pycache__"]
  },
  "ui": {
    "theme": "dark",
    "show_timestamps": true,
    "max_history": 100
  }
}
```

### **Advanced Settings**

See our [Configuration Guide](configuration.md) for detailed customization options.

## 🔍 Context System Deep Dive

### **Project Analysis**

R-Code CLI performs comprehensive project analysis:

```
🔍 Analyzing project structure...
📁 Found 42 files to analyze
📊 Detected framework: Flask 2.3.0
🏗️ Architecture pattern: MVC with Repository pattern
📋 Naming convention: snake_case
⚙️ Code quality: 8.5/10
✅ Project analysis complete
```

### **What Gets Analyzed**

- **File Structure**: Directory organization and file relationships
- **Code Elements**: Classes, functions, variables, imports
- **Dependencies**: Internal and external dependencies
- **Patterns**: Architecture patterns and design principles
- **Quality Metrics**: Complexity, maintainability, documentation coverage
- **Standards**: Naming conventions, coding style, best practices

### **Context Usage**

The AI uses this context to:

- **Prevent Duplicates**: Avoid creating files that already exist
- **Follow Patterns**: Match your existing coding style and patterns
- **Suggest Improvements**: Recommend better approaches based on your codebase
- **Avoid Breaking Changes**: Understand dependencies before making changes
- **Maintain Consistency**: Keep naming and structure consistent

## 💡 Best Practices

### **Getting the Most from R-Code**

#### **1. Start with Clear Requests**

```
❌ "Fix this"
✅ "Fix the authentication bug where users can't login with special characters in passwords"

❌ "Make it better"
✅ "Optimize the database queries in the user service to reduce load times"
```

#### **2. Use Checkpoints Strategically**

```
› /save "Working authentication system"
› Refactor authentication to use OAuth2
› /save "OAuth2 implementation complete"
```

#### **3. Leverage Context Awareness**

```
› Create a new API endpoint that follows our existing patterns
› Add validation that matches our current validation approach
› Implement error handling consistent with the rest of the codebase
```

#### **4. Review AI Suggestions**

Always review AI-generated code before applying it:

- Check for security implications
- Verify it follows your team's standards
- Test the functionality
- Ensure it integrates properly with existing code

### **Common Workflows**

#### **Feature Development**

1. `/save "Before adding new feature"`
2. Describe the feature in natural language
3. Review the AI's implementation plan
4. Approve file operations step by step
5. Test the implementation
6. `/save "New feature complete"`

#### **Bug Fixing**

1. Describe the bug and its symptoms
2. Let R-Code analyze the codebase for potential causes
3. Review suggested fixes
4. Apply fixes incrementally
5. Test after each change

#### **Code Refactoring**

1. `/save "Before refactoring"`
2. Explain what you want to refactor and why
3. Review the refactoring plan
4. Apply changes in small steps
5. Verify tests still pass
6. `/save "Refactoring complete"`

## 🚨 Troubleshooting

### **Common Issues**

#### **"No API key found"**

```bash
# Check if your API key is set
echo $ANTHROPIC_API_KEY

# Set it if missing
export ANTHROPIC_API_KEY="your-key-here"
```

#### **"Project analysis failed"**

- Ensure you're in a valid project directory
- Check file permissions
- Verify excluded directories aren't blocking analysis

#### **"Command requires approval but none given"**

- R-Code is waiting for your approval response
- Type one of: approve, deny, modify, always-approve, always-deny

#### **"Context cache is stale"**

- Use `/refresh` to update project context
- Check if files have been modified outside R-Code

### **Performance Issues**

#### **Slow Project Analysis**

- Add more directories to `excluded_dirs` in config
- Increase `max_file_size_mb` limit
- Enable `cache_enabled` for faster subsequent loads

#### **Memory Usage**

- Reduce `max_history` in configuration
- Clean old checkpoints with `/clean`
- Disable features you don't use

## 📊 Advanced Features

### **Multi-Provider AI**

R-Code can use multiple AI providers simultaneously:

```json
{
  "models": {
    "primary": "claude",
    "fallback": "openai",
    "claude": {
      "name": "anthropic:claude-3-5-sonnet-20241022",
      "temperature": 0.1
    },
    "openai": {
      "name": "openai:gpt-4-turbo-preview",
      "temperature": 0.1
    }
  }
}
```

### **Custom Tools**

Extend R-Code with custom tools by creating plugins in the `tools/` directory.

### **Integration with IDEs**

R-Code works seamlessly with popular IDEs:

- VS Code extension (coming soon)
- PyCharm plugin (coming soon)
- Vim/Neovim integration
- Emacs integration

## 🤝 Getting Help

### **Built-in Help**

- `/help` - List all available commands
- `/help <command>` - Get detailed help for a specific command

### **Community Support**

- **GitHub Discussions**: [Join the conversation](https://github.com/RaheesAhmed/R-Code-CLI/discussions)
- **Issue Tracker**: [Report bugs](https://github.com/RaheesAhmed/R-Code-CLI/issues)
- **Email Support**: [rahesahmed37@gmail.com](mailto:rahesahmed37@gmail.com)

### **Professional Support**

- **Enterprise Support**: [rahesahmed37@gmail.com](mailto:rahesahmed37@gmail.com)
- **Custom Development**: [rahesahmed37@gmail.com](mailto:rahesahmed37@gmail.com)
- **Training**: [rahesahmed37@gmail.com](mailto:rahesahmed37@gmail.com)

---

## 📚 Next Steps

- **[Configuration Guide](configuration.md)**: Customize R-Code for your needs
- **[Examples](examples/)**: See real-world usage scenarios
- **[API Reference](api-reference.md)**: Complete command documentation
- **[Contributing](../CONTRIBUTING.md)**: Help improve R-Code CLI

---

_This guide covers the core functionality of R-Code CLI. For specific use cases and advanced scenarios, check out our [Examples](examples/) directory._
