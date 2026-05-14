# AI Account Automation

A Bash-based project for generating customized prompts to use with NotebookLM, tailored for different clients based on industry and company name.

## Overview

This project streamlines the creation of personalized AI prompts for multiple clients. It uses template files and a configuration system to automatically generate client-specific versions without manual editing.

## Prerequisites

- **Bash shell** (available on macOS, Linux, and Windows with WSL/Git Bash)
- Basic command-line familiarity
- notebooklm-py
	- pip install notebooklm-py
	- pip install "notebooklm-py[browser]"
	- playwright install chromium
   - pip install "notebooklm-py[cookies]"

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jasoande/ai_automation
   cd ai_automation
   ```

2. Ensure the scripts are executable:
   ```bash
   chmod +x wrapper.sh
   ```

## Quick Start

1. **Configure clients** - Edit `vars.sh` to define your clients:
   ```bash
   CLIENTS=("Client1" "Client2" "Client3")
   ```

2. **Generate prompts** - Run the main script:
   ```bash
   bash wrapper.sh
   ```

3. **Find your outputs** - Customized prompts are saved in client-specific directories.

## Configuration

Client-specific variables are defined in `vars.sh`. This file contains:
- A list of client names
- Industry variables for each client
- Company name variables for each client

Edit `vars.sh` to add, remove, or modify client definitions as needed.

### Example vars.sh Structure

```bash
CLIENTS=("Hershey" "Merck" "Acme")

# Client: Hershey
Hershey_industry="Food & Beverage"
Hershey_name="Hershey Company"

# Client: Merck
Merck_industry="Pharmaceuticals"
Merck_name="Merck & Co."
```

## Usage

### Generating Prompts

Run the main script to generate customized prompts for all configured clients:

```bash
bash wrapper.sh
```

This will:
- Read client variables from `vars.sh`
- Process each `prompt*.txt` template file
- Replace placeholders (`$industry` and `$name`) with client-specific values
- Save customized prompts in client-specific directories (e.g., `Hershey/`, `Merck/`)

### Output

- **Location**: Customized prompt files are saved in subdirectories named after each client
- **Naming**: Each output file retains the original prompt template filename (e.g., `prompt1.txt`)
- **Example**: A template `prompt1.txt` becomes `Hershey/prompt1.txt`, `Merck/prompt1.txt`, etc.

## Project Structure

```
ai_automation/
├── README.md                 # This file
├── generate_prompts.sh       # Main script for prompt generation
├── vars.sh                   # Client variable definitions
├── prompt1.txt               # Template prompt file 1
├── prompt2.txt               # Template prompt file 2
├── prompt*.txt               # Additional template prompt files
├── Hershey/                  # Output directory for Hershey client
│   ├── prompt1.txt
│   └── prompt2.txt
└── Merck/                    # Output directory for Merck client
    ├── prompt1.txt
    └── prompt2.txt
```

## Contributing

Contributions are welcome! Please feel free to:
- Submit issues for bugs or feature requests
- Create pull requests with improvements
- Suggest enhancements to the automation process

## License

This project is open source. Please check for a LICENSE file or contact the repository owner for licensing details.

## Support

If you encounter issues:
1. Verify that `vars.sh` is properly configured
2. Ensure all `prompt*.txt` files exist
3. Check that the Bash script is executable
4. Review the script output for error messages
