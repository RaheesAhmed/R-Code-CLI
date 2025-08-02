# 🚀 Getting Started with R-Code CLI

Welcome to R-Code CLI! This guide will help you get up and running with the most advanced AI coding assistant in just a few minutes.

## 📋 Prerequisites

Before installing R-Code CLI, ensure you have:

- **Python 3.8+** installed on your system
- **Git** for cloning the repository
- **AI Provider API Key** from one of these providers:
  - [Anthropic Claude](https://console.anthropic.com/) (Recommended)
  - [OpenAI GPT](https://platform.openai.com/api-keys)
  - Other compatible providers

## 🛠️ Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/RaheesAhmed/R-Code-CLI.git
cd R-Code-CLI
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure API Keys

**Option A: Environment Variables (Recommended)**

```bash
# For Anthropic Claude (Recommended)
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"

# For OpenAI GPT
export OPENAI_API_KEY="your-openai-api-key-here"
```

**Option B: Configuration File**

Create `.rcode/config.json`:

```json
{
  "models": {
    "primary": "claude",
    "claude": {
      "name": "anthropic:claude-3-5-sonnet-20241022",
      "api_key_env": "ANTHROPIC_API_KEY",
      "temperature": 0.1,
      "max_tokens": 4000
    },
    "openai": {
      "name": "openai:gpt-4-turbo-preview",
      "api_key_env": "OPENAI_API_KEY",
      "temperature": 0.1,
      "max_tokens": 4000
    }
  }
}
```

## 🎯 First Run

### Launch R-Code CLI

```bash
python cli.py
```

You should see:

```
🚀 Welcome to R-Code CLI v1.0.0
🧠 Analyzing project structure...
📁 Found X files to analyze
✅ Project analysis complete

┌─ R-Code Assistant
│ Hello! I'm your AI coding assistant with complete project understanding.
│ I can help you write, debug, and improve code while preventing conflicts.
│
│ Try asking me to:
│ • "Create a new user authentication module"
│ • "Fix the bug in user_service.py"
│ • "Add error handling to the API endpoints"
│
│ Type /help for commands or just start chatting!
└─

›
```

## 🌟 Your First Interaction

### Try These Commands

1. **Get Help**

   ```
   › /help
   ```

2. **Check Status**

   ```
   › /status
   ```

3. **Ask for Code**

   ```
   › Create a simple Python function to calculate fibonacci numbers
   ```

4. **Project Analysis**
   ```
   › Tell me about this project structure
   ```

## 🔧 Essential Slash Commands

| Command               | Purpose                      | Example                      |
| --------------------- | ---------------------------- | ---------------------------- |
| `/help`               | Show all available commands  | `/help`                      |
| `/status`             | Display current session info | `/status`                    |
| `/save <description>` | Create a checkpoint          | `/save "Before refactoring"` |
| `/undo`               | Undo last AI operation       | `/undo`                      |
| `/checkpoints`        | List save points             | `/checkpoints`               |
| `/revert <id>`        | Go back to checkpoint        | `/revert cp_20250208_142301` |

## 🛡️ Security Features

R-Code CLI includes smart security features:

### Human Approval System

When R-Code wants to execute potentially dangerous commands, you'll see:

```
🔐 Human Approval Required
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 AI wants to execute a terminal command                        │
│                                                                 │
│ Command: rm temp_file.txt                                       │
│ Directory: /your/project/path                                   │
│ Risk Level: ⚠️ Medium                                           │
│                                                                 │
│ Analysis:                                                       │
│ • File deletion command                                         │
│ • Affects only temporary files                                  │
└─────────────────────────────────────────────────────────────────┘

Your response (approve/deny/modify/always-approve/always-deny):
```

### Response Options

- **approve**: Allow the command
- **deny**: Block the command
- **modify**: Edit before executing
- **always-approve**: Add to safe commands
- **always-deny**: Add to blocked commands

## 🎨 Customization

### Basic Configuration

Create `.rcode/config.json` for basic customization:

```json
{
  "models": {
    "primary": "claude",
    "fallback": "openai"
  },
  "tools": {
    "file_operations": {
      "enabled": true,
      "auto_backup": true
    },
    "terminal_operations": {
      "enabled": true,
      "human_approval_required": true
    }
  },
  "context": {
    "auto_analyze": true,
    "cache_enabled": true
  }
}
```

### Advanced Settings

See our [Configuration Guide](configuration.md) for detailed customization options.

## 🚨 Common Issues

### Issue: "No API key found"

**Solution**: Ensure your API key is properly set:

```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# If empty, set it:
export ANTHROPIC_API_KEY="your-key-here"
```

### Issue: "Permission denied" on commands

**Solution**: R-Code CLI uses human approval for security. Respond to approval prompts.

### Issue: "Project analysis failed"

**Solution**: Ensure you're in a valid project directory with readable files.

For more troubleshooting, see our [Troubleshooting Guide](troubleshooting.md).

## 🎓 Learning Path

### Beginner (Day 1)

1. ✅ Complete this getting started guide
2. ✅ Try basic chat interactions
3. ✅ Learn essential slash commands
4. ✅ Create your first checkpoint

### Intermediate (Week 1)

1. 📖 Read the [User Guide](user-guide.md)
2. ⚙️ Customize [Configuration](configuration.md)
3. 💡 Try [Examples](examples/)
4. 🔧 Explore advanced features

### Advanced (Month 1)

1. 🏗️ Understand [Architecture](architecture.md)
2. 🔌 Set up [IDE Integration](integrations/ide-integration.md)
3. 🤖 Configure [Custom AI Providers](integrations/ai-providers.md)
4. 🤝 Consider [Contributing](../CONTRIBUTING.md)

## 📚 Next Steps

Now that you're set up, explore these resources:

- **[User Guide](user-guide.md)**: Complete feature walkthrough
- **[Examples](examples/)**: Real-world usage scenarios
- **[Configuration](configuration.md)**: Customize R-Code for your workflow
- **[Command Reference](api-reference.md)**: Complete command documentation

## 🤝 Getting Help

If you run into issues:

1. **Check our [FAQ](faq.md)** for common questions
2. **Visit [Troubleshooting](troubleshooting.md)** for detailed solutions
3. **Join [GitHub Discussions](https://github.com/RaheesAhmed/R-Code-CLI/discussions)** for community help
4. **Report bugs** on [GitHub Issues](https://github.com/RaheesAhmed/R-Code-CLI/issues)
5. **Email us** at [rahesahmed37@gmail.com](mailto:rahesahmed37@gmail.com)

## 🎉 Welcome to the Community!

You're now part of the R-Code CLI community! Here's how to stay connected:

- ⭐ **Star the repository** to support the project
- 👀 **Watch for updates** to get notified of new releases
- 💬 **Join discussions** to share your experience
- 🐛 **Report issues** to help improve R-Code
- 🤝 **Contribute** to make R-Code even better

---

**Happy coding with R-Code CLI!** 🚀

_Next: Continue with the [User Guide](user-guide.md) to explore all features._
