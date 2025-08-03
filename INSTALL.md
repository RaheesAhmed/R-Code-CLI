# R-Code CLI Installation Guide

## Quick Installation

### Install from PyPI (Recommended)

```bash
pip install rcode
```

After installation, you can run R-Code CLI with:

```bash
rcode

```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/RaheesAhmed/R-Code-CLI.git
cd R-Code-CLI

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Or run directly
python cli.py
```

## Build Package Locally

To build the package yourself:

```bash
# Install build dependencies
pip install build twine wheel

# Run the build script
python build_package.py

# Or build manually
python -m build

# Install locally built package
pip install dist/*.whl
```

## Requirements

- Python 3.8 or higher
- pip (latest version recommended)

## Environment Setup

R-Code CLI requires API keys for AI models. Set up your environment:

```bash
# For Claude (Anthropic)
export ANTHROPIC_API_KEY="your-api-key-here"

# For OpenAI
export OPENAI_API_KEY="your-api-key-here"

# For Tavily
export TAVILY_API_KEY="your-api-key-here"
```

Or create a `.env` file in your project directory:

```env
ANTHROPIC_API_KEY=your-api-key-here
OPENAI_API_KEY=your-api-key-here
```

## Verify Installation

After installation, verify it works:

```bash
rcode --help
```

You should see the R-Code CLI welcome screen and commands.

## Troubleshooting

### Import Errors

If you encounter import errors, ensure all dependencies are installed:

```bash
pip install --upgrade -r requirements.txt
```

### API Key Issues

Make sure your API keys are properly set in environment variables or `.env` file.

### Permission Issues

On some systems, you may need to use `pip3` instead of `pip`:

```bash
pip3 install rcode
```

## Uninstallation

To uninstall R-Code CLI:

```bash
pip uninstall rcode
```

## Support

For issues and support:

- GitHub Issues: https://github.com/RaheesAhmed/R-Code-CLI/issues
- Documentation: https://github.com/RaheesAhmed/R-Code-CLI/docs
