# ❓ Frequently Asked Questions

Common questions and answers about R-Code CLI.

## 🚀 Getting Started

### **Q: What makes R-Code CLI different from other AI coding assistants?**

**A:** R-Code CLI is context-aware and project-intelligent. Unlike other tools that treat each request in isolation, R-Code understands your entire codebase, prevents duplicates, follows your coding patterns, and includes a time-travel system to safely experiment with changes.

### **Q: Which AI providers are supported?**

**A:** R-Code CLI supports:

- **Anthropic Claude** (Recommended) - Claude 3.5 Sonnet
- **OpenAI GPT** - GPT-4 Turbo and GPT-4
- **Custom providers** - Configure your own API endpoints
- **Multi-provider setup** - Use multiple models simultaneously

### **Q: Do I need to pay for AI API usage?**

**A:** Yes, you need your own API keys from AI providers. R-Code CLI is free, but AI API usage costs depend on your chosen provider:

- **Anthropic Claude**: ~$3-15 per million tokens
- **OpenAI GPT-4**: ~$10-30 per million tokens
- Most developers spend $5-20/month for regular usage

### **Q: Is R-Code CLI free?**

**A:** Yes! R-Code CLI is completely free and open source under GNU AGPL v3.0. You only pay for AI API usage from providers like Anthropic or OpenAI.

## 🛠️ Installation & Setup

### **Q: I'm getting "No API key found" error. How do I fix this?**

**A:** Set your API key as an environment variable:

```bash
# For Anthropic Claude (recommended)
export ANTHROPIC_API_KEY="your-api-key-here"

# For OpenAI
export OPENAI_API_KEY="your-api-key-here"

# On Windows Command Prompt
set ANTHROPIC_API_KEY=your-api-key-here

# On Windows PowerShell
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

### **Q: Can I use multiple AI providers at once?**

**A:** Yes! Configure multiple providers in `.rcode/config.json`:

```json
{
  "models": {
    "primary": "claude",
    "fallback": "openai",
    "claude": {
      "name": "anthropic:claude-3-5-sonnet-20241022",
      "api_key_env": "ANTHROPIC_API_KEY"
    },
    "openai": {
      "name": "openai:gpt-4-turbo-preview",
      "api_key_env": "OPENAI_API_KEY"
    }
  }
}
```

### **Q: What Python version is required?**

**A:** Python 3.8 or higher. We recommend Python 3.10+ for best performance.

### **Q: Can I use R-Code CLI on Windows/macOS/Linux?**

**A:** Yes! R-Code CLI is cross-platform and works on Windows, macOS, and Linux.

## 🧠 Context & Project Analysis

### **Q: How does R-Code understand my project?**

**A:** R-Code performs comprehensive project analysis:

- **AST parsing** of code files to understand structure
- **Dependency mapping** to track relationships between files
- **Pattern detection** to learn your coding conventions
- **Framework identification** (Flask, React, Django, etc.)
- **Architecture analysis** to understand design patterns

### **Q: What files does R-Code analyze?**

**A:** R-Code analyzes:

- All code files in common languages (Python, JavaScript, TypeScript, etc.)
- Configuration files (package.json, requirements.txt, etc.)
- Documentation files
- Excludes: `.git`, `node_modules`, `__pycache__`, binary files

### **Q: How can I exclude certain directories from analysis?**

**A:** Add excluded directories to your config:

```json
{
  "context": {
    "excluded_dirs": [".git", "node_modules", "__pycache__", "dist", "build"]
  }
}
```

### **Q: Why is project analysis slow?**

**A:** Large projects with many files take longer to analyze. Speed it up by:

- Adding more directories to `excluded_dirs`
- Enabling `cache_enabled` for faster subsequent loads
- Increasing `max_file_size_mb` to skip very large files

## 🔒 Security & Approval System

### **Q: Why does R-Code ask for approval before running commands?**

**A:** R-Code includes a human-in-the-loop security system to protect you from potentially dangerous operations. It analyzes commands for risk and only asks approval for operations that could be harmful.

### **Q: How do I configure the approval system?**

**A:** Customize security settings in `.rcode/config.json`:

```json
{
  "tools": {
    "terminal_operations": {
      "human_approval_required": true,
      "safe_commands": ["ls", "pwd", "git status"],
      "dangerous_commands": ["rm", "sudo", "shutdown"],
      "auto_approve_safe": false
    }
  }
}
```

### **Q: Can I disable the approval system?**

**A:** Yes, but not recommended. Set `human_approval_required: false` in config. However, this removes important safety protections.

### **Q: What do the risk levels mean?**

**A:**

- **🟢 Safe**: Reading files, safe commands (ls, pwd)
- **🟡 Caution**: File modifications, package installations
- **🟠 Warning**: System changes, configuration modifications
- **🚨 Dangerous**: File deletion, system commands, network operations

## ⏰ Checkpoints & Time Travel

### **Q: What are checkpoints?**

**A:** Checkpoints are save points that capture the state of your project. They allow you to safely experiment and revert changes if needed.

### **Q: When are checkpoints created automatically?**

**A:** Automatic checkpoints are created:

- Before major file operations
- Before running potentially destructive commands
- At regular intervals during long operations
- When starting significant refactoring tasks

### **Q: How do I create manual checkpoints?**

**A:** Use the `/save` command:

```
› /save "Before adding authentication system"
› /save "Working version before optimization"
```

### **Q: How do I revert to a previous checkpoint?**

**A:** Use `/checkpoints` to list available checkpoints, then `/revert`:

```
› /checkpoints
› /revert cp_20250208_142301
```

### **Q: How long are checkpoints kept?**

**A:** By default, checkpoints are kept for 30 days. Configure retention in your settings:

```json
{
  "checkpoint": {
    "retention_days": 30,
    "max_checkpoints": 100
  }
}
```

## 💻 Usage & Features

### **Q: Can I use R-Code CLI in any directory?**

**A:** Yes, but R-Code works best in project directories with code files. It can analyze and understand any directory structure.

### **Q: Does R-Code work with all programming languages?**

**A:** R-Code has excellent support for:

- **Python** (Django, Flask, FastAPI)
- **JavaScript/TypeScript** (React, Vue, Node.js)
- **Web technologies** (HTML, CSS, etc.)
- **Configuration files** (JSON, YAML, TOML)

Basic support for other languages, with ongoing improvements.

### **Q: Can I use R-Code CLI with my existing IDE?**

**A:** Yes! R-Code CLI works alongside any IDE:

- **VS Code**: Works great with integrated terminal
- **PyCharm**: Use built-in terminal
- **Vim/Neovim**: Terminal integration
- **Emacs**: Shell integration
- Future: Native IDE extensions planned

### **Q: How do I get the best results from R-Code?**

**A:** Follow these best practices:

1. **Be specific**: "Fix authentication bug with special characters" vs "fix this"
2. **Use context**: "Add validation that matches our existing approach"
3. **Use checkpoints**: Save before major changes
4. **Review AI suggestions**: Always verify generated code
5. **Start small**: Begin with small changes, build confidence

## 🚨 Troubleshooting

### **Q: R-Code seems slow or unresponsive. What should I do?**

**A:** Try these solutions:

1. **Check API key**: Ensure your API key is valid and has credits
2. **Reduce context**: Add more directories to `excluded_dirs`
3. **Clear cache**: Delete `.rcode/cache/` directory
4. **Restart session**: Exit and restart R-Code CLI
5. **Check network**: Ensure stable internet connection

### **Q: "Project analysis failed" error. How do I fix this?**

**A:** Common solutions:

1. **Check permissions**: Ensure R-Code can read project files
2. **Verify directory**: Make sure you're in a valid project directory
3. **Check excluded dirs**: Ensure important files aren't excluded
4. **File encoding**: Ensure files use UTF-8 encoding
5. **Reduce file size**: Very large files might cause issues

### **Q: R-Code isn't following my coding style. Why?**

**A:** R-Code learns from your existing code. To improve style matching:

1. **Ensure sufficient examples**: Have enough existing code for pattern recognition
2. **Consistent patterns**: Use consistent naming and structure in existing code
3. **Explicit requests**: Ask for specific style preferences
4. **Configuration**: Set style preferences in config

### **Q: Can I recover deleted files?**

**A:** If deletion happened through R-Code:

1. **Use `/undo`** immediately after the operation
2. **Revert to checkpoint** using `/revert <id>`
3. **Check backups** in `.rcode/backups/` directory

If files were deleted outside R-Code, use your version control system or system backups.

## 🤝 Community & Support

### **Q: How do I report bugs or request features?**

**A:**

- **Bugs**: [GitHub Issues](https://github.com/RaheesAhmed/R-Code-CLI/issues)
- **Features**: [GitHub Discussions](https://github.com/RaheesAhmed/R-Code-CLI/discussions)
- **Security**: [security@rcode.dev](mailto:security@rcode.dev)

### **Q: Can I contribute to R-Code CLI?**

**A:** Absolutely! We welcome contributions:

1. Read our [Contributing Guide](../CONTRIBUTING.md)
2. Check our [Code of Conduct](../CODE_OF_CONDUCT.md)
3. Start with good first issues
4. Join our community discussions

### **Q: Is there a Discord or community chat?**

**A:** Currently we use:

- **GitHub Discussions** for long-form discussions
- **GitHub Issues** for bug reports
- **Discord** (coming soon)

### **Q: Do you offer professional support?**

**A:** Yes! Contact us for:

- **Enterprise support**: [enterprise@rcode.dev](mailto:enterprise@rcode.dev)
- **Custom development**: [custom@rcode.dev](mailto:custom@rcode.dev)
- **Training & consulting**: [training@rcode.dev](mailto:training@rcode.dev)

## ⚖️ Legal & Licensing

### **Q: What license is R-Code CLI under?**

**A:** GNU Affero General Public License v3.0 (AGPL v3.0) with additional terms for trademark protection.

### **Q: Can I use R-Code CLI commercially?**

**A:** Yes! The AGPL v3.0 allows commercial use. Key requirements:

- Keep the source code open if you distribute modified versions
- Server deployments must provide source code to users
- Respect trademark restrictions for "R-Code" branding

### **Q: Can I create a proprietary fork of R-Code CLI?**

**A:** No. The AGPL v3.0 copyleft license requires all derivatives to remain open source. This prevents proprietary forks while encouraging open source innovation.

### **Q: Can I use "R-Code" in my project name?**

**A:** "R-Code" is a protected trademark. For commercial use of the trademark, contact [trademark@rcode.dev](mailto:trademark@rcode.dev). Attribution and fair use are generally acceptable.

## 🔮 Future & Roadmap

### **Q: What's coming next for R-Code CLI?**

**A:** Our roadmap includes:

- **IDE Extensions**: VS Code, PyCharm native extensions
- **Web Interface**: Optional browser-based interface
- **Team Features**: Multi-developer collaboration
- **Custom Models**: Train on your specific codebase
- **More Languages**: Expanded language support

### **Q: Will R-Code CLI always be free?**

**A:** Yes! The core R-Code CLI will always be free and open source. We may offer premium services like:

- Hosted AI models (no API key needed)
- Enterprise support and consulting
- Advanced team collaboration features
- Priority support

---

## 📞 Still Have Questions?

**Didn't find your answer?** We're here to help:

- **Community**: [GitHub Discussions](https://github.com/RaheesAhmed/R-Code-CLI/discussions)
- **Email**: [support@rcode.dev](mailto:support@rcode.dev)
- **Documentation**: [docs/](README.md)
- **Examples**: [examples/](examples/)

---

_This FAQ is updated regularly. If you have suggestions for additional questions, please let us know!_
