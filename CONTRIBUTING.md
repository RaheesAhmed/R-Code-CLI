# Contributing to R-Code CLI

Thank you for your interest in contributing to R-Code CLI! We welcome contributions from the community while maintaining high standards and protecting the project's intellectual property.

## 🚨 IMPORTANT LEGAL NOTICE

By contributing to this project, you agree that:

1. **Copyright Assignment**: You assign all rights in your contributions to Rahees Ahmed and the R-Code project
2. **Original Work**: Your contributions are your original work and do not infringe on third-party rights
3. **License Compliance**: Your contributions will be licensed under the GNU AGPL v3.0
4. **No Patent Claims**: You will not assert patent claims against this project or its users

## 🛡️ Code Protection Policy

R-Code CLI uses advanced anti-copying measures:

- **AGPL v3.0 License**: Strong copyleft license requiring all derivatives to be open source
- **Trademark Protection**: "R-Code" name and logos are protected trademarks
- **Attribution Requirements**: All derivatives must credit the original project
- **Network Use Clause**: Server deployments must provide source code access
- **Patent Grant**: Contributors grant patent licenses but retain termination rights

## 📋 Contribution Guidelines

### Before You Start

1. **Read the License**: Understand AGPL v3.0 requirements
2. **Check Issues**: Look for existing issues or feature requests
3. **Discuss Major Changes**: Open an issue for significant modifications
4. **Follow Standards**: Adhere to our coding standards and architecture

### Types of Contributions Welcome

✅ **Bug Fixes** - Help us maintain code quality
✅ **Performance Improvements** - Optimize existing functionality
✅ **Documentation** - Improve README, code comments, examples
✅ **Tests** - Add test coverage for existing features
✅ **Security Fixes** - Report and fix security vulnerabilities
✅ **Accessibility** - Improve accessibility features
✅ **Translations** - Help localize the interface

❌ **NOT Welcome** - Major architectural changes without approval
❌ **NOT Welcome** - Features that compete with premium offerings
❌ **NOT Welcome** - Code that violates our design principles

### Development Setup

1. **Fork the Repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/R-Code-CLI.git
   cd R-Code-CLI
   ```

2. **Install Dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run Tests**

   ```bash
   python -m pytest tests/
   ```

4. **Start Development**
   ```bash
   python cli.py
   ```

### Code Standards

#### Python Code Style

- **PEP 8 Compliance**: Follow Python style guidelines
- **Type Hints**: Use type annotations for all functions
- **Docstrings**: Google-style docstrings for all public functions
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Security**: No hardcoded secrets or unsafe operations

#### Architecture Principles

- **Modular Design**: Keep components loosely coupled
- **Configuration-Driven**: Use config files, not hardcoded values
- **Context-Aware**: Leverage the context system for intelligent operations
- **Performance**: Optimize for speed and memory usage
- **Maintainability**: Write self-documenting, clean code

#### Git Workflow

- **Branch Naming**: `feature/description`, `bugfix/description`, `security/description`
- **Commit Messages**: Clear, descriptive messages following conventional commits
- **Small PRs**: Keep pull requests focused and reviewable
- **Tests Required**: All code changes must include tests

### Pull Request Process

1. **Create Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**

   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Thoroughly**

   ```bash
   python -m pytest tests/
   python -m black src/
   python -m flake8 src/
   ```

4. **Commit Changes**

   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Pull Request Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Documentation update
- [ ] Security fix

## Testing

- [ ] All existing tests pass
- [ ] New tests added for changes
- [ ] Manual testing completed

## Legal Compliance

- [ ] I assign copyright to the R-Code project
- [ ] My code is original work
- [ ] No third-party IP violations
- [ ] No patent claims against project

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Breaking changes documented
```

## 🔒 Security Policy

### Reporting Security Issues

**DO NOT** create public issues for security vulnerabilities.

Instead:

1. Email: rahesahmed37@gmail.com
2. Include: Detailed description, reproduction steps, potential impact
3. Allow: 90 days for responsible disclosure
4. Expect: Acknowledgment within 48 hours

### Security Standards

- No hardcoded credentials
- Input validation and sanitization
- Secure dependency management
- Regular security audits
- Encryption for sensitive data

## 🏗️ Architecture Guidelines

### Core Principles

1. **Context-Aware**: Use the context system for intelligent operations
2. **Checkpoint-Safe**: All operations should support undo/redo
3. **Human-Approved**: Dangerous operations require user confirmation
4. **Configuration-Driven**: Behavior controlled by config files
5. **Performance-First**: Optimize for speed and resource usage

### Component Structure

```
src/
├── agents/          # AI agent implementations
├── checkpoint/      # Undo/redo system
├── commands/        # Slash commands
├── config/          # Configuration management
├── context/         # Project context system
├── tools/           # File and terminal operations
├── types/           # Type definitions
└── utils/           # Utility functions
```

### Adding New Features

1. **Design Document**: Create issue with detailed design
2. **Context Integration**: Ensure context-aware implementation
3. **Checkpoint Support**: Add undo/redo capability
4. **Human Approval**: Add confirmation for dangerous operations
5. **Configuration**: Make behavior configurable
6. **Tests**: Comprehensive test coverage
7. **Documentation**: Update all relevant docs

## 🎖️ Recognition

### Contributor Levels

**🌟 Core Contributors** - Major features, architectural improvements
**⭐ Regular Contributors** - Multiple merged PRs, ongoing involvement
**✨ Community Contributors** - Bug fixes, documentation, first-time contributors

### Recognition Program

- Contributors listed in README
- Special Discord role for contributors
- Early access to new features
- Invitation to contributor events
- Potential paid opportunities for major contributors

## 📞 Getting Help

### Community Support

- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time chat with community
- **Stack Overflow**: Tag questions with `rcode-cli`

### Direct Contact

- **Email**: contribute@rcode.dev
- **Maintainer**: @RaheesAhmed on GitHub
- **Issues**: Use GitHub issue templates

## 📜 Legal Requirements

### Contributor License Agreement (CLA)

By submitting code to this project, you certify that:

1. **Original Work**: The contribution is your original work
2. **Rights**: You have the right to submit the contribution
3. **License Grant**: You grant the project maintainers perpetual, worldwide, non-exclusive rights to your contribution
4. **No Conflicting Agreements**: You have no agreements that conflict with this grant
5. **Patent Rights**: You grant a patent license for any patents you hold that are infringed by your contribution

### Copyright Notice

Add this header to new files:

```python
"""
R-Code CLI - [File Description]
Copyright (C) 2025 Rahees Ahmed and R-Code Contributors

This file is part of R-Code CLI.
Licensed under the GNU AGPL v3.0.
See LICENSE file for details.
"""
```

---

Thank you for contributing to R-Code CLI! Together, we're building the most advanced AI coding assistant while protecting our intellectual property and maintaining the highest standards.

For questions about these guidelines, please open an issue or contact the maintainers.
