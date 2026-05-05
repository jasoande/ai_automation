
# AI Account Automation

A simple project for generating customized prompts to use with NotebookLM, tailored for different clients based on industry and company name.

## Getting Started

### Prerequisites
- Bash shell (available on macOS, Linux, and Windows with WSL/Git Bash)

### Installation
1. Clone the repository:
   git clone https://github.com/jasoande/ai_automation
   ```
2. Navigate to the project directory:
   cd ai_automation
   ```

## Usage

### Configuration
Client-specific variables are defined in `vars.sh`. This file contains:
- A list of clients
- Industry and name variables for each client

Edit `vars.sh` to add, remove, or modify client definitions as needed.

### Generating Prompts
Run the script to generate customized prompts for all clients:
```bash
bash generate_prompts.sh
```

This will:
- Read variables from `vars.sh`
- Process each `prompt*.txt` file
- Replace placeholders (`$industry` and `$name`) with client-specific values
- Save the customized prompts in client-specific directories (e.g., `Hershey/`, `Merck/`)

### Output
- Customized prompt files are saved in subdirectories named after each client.
- Each output file retains the original prompt filename (e.g., `prompt1.txt`).

## Project Structure
- `generate_prompts.sh`: Main script for prompt generation
- `vars.sh`: Client variable definitions
- `prompt*.txt`: Template prompt files
- Client directories: Output folders for customized prompts

## Contributing
Feel free to submit issues or pull requests for improvements.
