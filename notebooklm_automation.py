#!/usr/bin/env python3
"""
NotebookLM Automation Script

Consolidated automation for:
1. Creating NotebookLM notebooks for configured clients
2. Processing prompts and uploading sources to notebooks

Features:
- Parallel execution for client processing
- Ask prompts processed before chat prompts
- Sequential source loading per client
- Comprehensive error handling and logging
- Retry logic for API calls
- Input validation and environment checks
"""

import os
import sys
import subprocess
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
import time


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notebooklm_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Enum for prompt file types"""
    ASK = "ask"
    CHAT = "chat"
    UNKNOWN = "unknown"


@dataclass
class Client:
    """Client configuration"""
    key: str
    name: str
    industry: str

    def validate(self) -> bool:
        """Validate client configuration"""
        if not self.name or not self.industry:
            logger.error(f"Client {self.key} missing name or industry")
            return False
        return True


@dataclass
class PromptFile:
    """Prompt file information"""
    path: Path
    filename: str
    prompt_type: PromptType

    @staticmethod
    def from_path(path: Path) -> 'PromptFile':
        """Create PromptFile from path"""
        filename = path.name
        if "ask" in filename.lower():
            prompt_type = PromptType.ASK
        elif "chat" in filename.lower():
            prompt_type = PromptType.CHAT
        else:
            prompt_type = PromptType.UNKNOWN
        return PromptFile(path=path, filename=filename, prompt_type=prompt_type)


class NotebookLMClient:
    """Wrapper for notebooklm CLI interactions"""

    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    @staticmethod
    def run_command(cmd: List[str], description: str = "") -> Tuple[bool, str, str]:
        """
        Execute a notebooklm CLI command with retry logic
        
        Returns:
            Tuple of (success, stdout, stderr)
        """
        for attempt in range(NotebookLMClient.MAX_RETRIES):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    logger.debug(f"Command succeeded: {' '.join(cmd)}")
                    return True, result.stdout.strip(), result.stderr.strip()
                else:
                    logger.warning(
                        f"Command failed (attempt {attempt + 1}/{NotebookLMClient.MAX_RETRIES}): "
                        f"{description or ' '.join(cmd)}\n{result.stderr}"
                    )
                    
                    if attempt < NotebookLMClient.MAX_RETRIES - 1:
                        time.sleep(NotebookLMClient.RETRY_DELAY)
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Command timeout: {' '.join(cmd)}")
                if attempt < NotebookLMClient.MAX_RETRIES - 1:
                    time.sleep(NotebookLMClient.RETRY_DELAY)
            except Exception as e:
                logger.error(f"Command error: {e}")
                if attempt < NotebookLMClient.MAX_RETRIES - 1:
                    time.sleep(NotebookLMClient.RETRY_DELAY)
        
        return False, "", f"Failed after {NotebookLMClient.MAX_RETRIES} attempts"

    @staticmethod
    def login() -> bool:
        """Authenticate with NotebookLM"""
        logger.info("Logging into NotebookLM with browser cookies...")
        success, _, stderr = NotebookLMClient.run_command(
            ["notebooklm", "login", "--browser-cookies", "chrome"],
            "NotebookLM login"
        )
        if not success:
            logger.error(f"Failed to login: {stderr}")
        return success

    @staticmethod
    def list_notebooks() -> Optional[str]:
        """Get list of notebooks"""
        success, stdout, _ = NotebookLMClient.run_command(
            ["notebooklm", "list"],
            "List notebooks"
        )
        return stdout if success else None

    @staticmethod
    def notebook_exists(name: str) -> bool:
        """Check if notebook exists"""
        notebooks = NotebookLMClient.list_notebooks()
        if not notebooks:
            return False
        return name in notebooks

    @staticmethod
    def create_notebook(name: str) -> bool:
        """Create a new notebook"""
        logger.info(f"Creating notebook: {name}")
        success, _, stderr = NotebookLMClient.run_command(
            ["notebooklm", "create", name],
            f"Create notebook '{name}'"
        )
        if not success:
            logger.error(f"Failed to create notebook '{name}': {stderr}")
        return success

    @staticmethod
    def get_notebook_id(name: str) -> Optional[str]:
        """Get notebook ID by name"""
        notebooks = NotebookLMClient.list_notebooks()
        if not notebooks:
            return None
        
        for line in notebooks.split('\n'):
            if name in line:
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
        return None

    @staticmethod
    def use_notebook(notebook_id: str) -> bool:
        """Set active notebook"""
        success, _, stderr = NotebookLMClient.run_command(
            ["notebooklm", "use", notebook_id],
            f"Use notebook {notebook_id}"
        )
        return success

    @staticmethod
    def add_research_source(content: str) -> bool:
        """Add research source to notebook"""
        logger.info("Adding research source to notebook...")
        success, _, stderr = NotebookLMClient.run_command(
            ["notebooklm", "source", "add-research", content, "--import-all"],
            "Add research source"
        )
        if not success:
            logger.error(f"Failed to add research source: {stderr}")
        return success

    @staticmethod
    def ask_question(question: str) -> bool:
        """Ask a question and save as note"""
        logger.info("Asking question and saving as note...")
        success, _, stderr = NotebookLMClient.run_command(
            ["notebooklm", "ask", question, "--save-as-note"],
            "Ask question"
        )
        if not success:
            logger.error(f"Failed to ask question: {stderr}")
        return success


class PromptProcessor:
    """Process and substitute variables in prompt files"""

    @staticmethod
    def escape_sed_replacement(value: str) -> str:
        """Escape special characters for sed replacement"""
        # Escape backslash, ampersand, and pipe
        return value.replace('\\', '\\\\').replace('&', '\\&').replace('|', '\\|')

    @staticmethod
    def process_prompt(
        prompt_path: Path,
        client: Client,
        output_dir: Path
    ) -> Optional[Path]:
        """
        Process prompt file with variable substitution
        
        Substitutes $industry and $name variables
        
        Returns:
            Path to generated prompt file or None if failed
        """
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Perform variable substitution
            escaped_industry = PromptProcessor.escape_sed_replacement(client.industry)
            escaped_name = PromptProcessor.escape_sed_replacement(client.name)
            
            content = re.sub(r'\$industry\b', escaped_industry, content, flags=re.IGNORECASE)
            content = re.sub(r'\$name\b', escaped_name, content, flags=re.IGNORECASE)
            
            # Write processed prompt
            output_path = output_dir / prompt_path.name
            output_path.write_text(content, encoding='utf-8')
            
            logger.info(f"Generated prompt: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to process prompt {prompt_path}: {e}")
            return None


class NotebookLMAutomation:
    """Main orchestrator for NotebookLM automation"""

    def __init__(self, script_dir: Optional[Path] = None):
        """Initialize automation engine"""
        self.script_dir = script_dir or Path(__file__).parent
        self.clients: List[Client] = []
        self.prompt_files: List[PromptFile] = []
        self.max_workers = 4  # Adjust based on system capacity

    def load_config(self) -> bool:
        """Load client configuration from vars.sh"""
        try:
            vars_file = self.script_dir / "vars.sh"
            if not vars_file.exists():
                logger.error(f"Configuration file not found: {vars_file}")
                return False
            
            config_content = vars_file.read_text(encoding='utf-8')
            
            # Parse clients array
            clients_match = re.search(r'clients=\((.*?)\)', config_content, re.DOTALL)
            if not clients_match:
                logger.error("Could not parse clients array from vars.sh")
                return False
            
            client_keys = re.findall(
                r'"([^"]+)"|\'([^\']+)\'|(\w+)',
                clients_match.group(1)
            )
            client_keys = [key[0] or key[1] or key[2] for key in client_keys if any(key)]
            
            # Filter out comments
            client_keys = [k for k in client_keys if k and not k.startswith('#')]
            
            # Extract client variables
            for client_key in client_keys:
                industry_pattern = f'{client_key}_industry="([^"]*)"'
                name_pattern = f'{client_key}_name="([^"]*)"'
                
                industry_match = re.search(industry_pattern, config_content)
                name_match = re.search(name_pattern, config_content)
                
                if industry_match and name_match:
                    client = Client(
                        key=client_key,
                        name=name_match.group(1),
                        industry=industry_match.group(1)
                    )
                    if client.validate():
                        self.clients.append(client)
            
            if not self.clients:
                logger.error("No valid clients found in configuration")
                return False
            
            logger.info(f"Loaded {len(self.clients)} clients: {[c.name for c in self.clients]}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def discover_prompts(self) -> bool:
        """Discover all prompt files in script directory"""
        try:
            prompt_paths = list(self.script_dir.glob("*prompt*.txt"))
            
            if not prompt_paths:
                logger.warning("No prompt files found")
                return True
            
            for path in sorted(prompt_paths):
                prompt = PromptFile.from_path(path)
                self.prompt_files.append(prompt)
            
            # Sort: ASK prompts first, then CHAT
            self.prompt_files.sort(
                key=lambda p: (p.prompt_type != PromptType.ASK, p.filename)
            )
            
            logger.info(f"Discovered {len(self.prompt_files)} prompts")
            for prompt in self.prompt_files:
                logger.info(f"  - {prompt.filename} ({prompt.prompt_type.value})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to discover prompts: {e}")
            return False

    def create_notebooks(self) -> bool:
        """Create NotebookLM notebooks for all clients"""
        logger.info("Creating NotebookLM notebooks...")
        
        all_created = True
        for client in self.clients:
            if NotebookLMClient.notebook_exists(client.name):
                logger.info(f"Notebook already exists: {client.name}")
            else:
                if not NotebookLMClient.create_notebook(client.name):
                    all_created = False
        
        return all_created

    def process_client(self, client: Client) -> bool:
        """
        Process all prompts for a single client (runs in parallel)
        
        Process order:
        1. All ASK prompts (sequential)
        2. All CHAT prompts (sequential)
        """
        try:
            logger.info(f"Processing client: {client.name}")
            
            # Create client output directory
            output_dir = self.script_dir / client.key
            output_dir.mkdir(exist_ok=True)
            
            # Get notebook ID
            nb_id = NotebookLMClient.get_notebook_id(client.name)
            if not nb_id:
                logger.error(f"Could not find notebook ID for {client.name}")
                return False
            
            if not NotebookLMClient.use_notebook(nb_id):
                logger.error(f"Failed to use notebook {nb_id}")
                return False
            
            # Group prompts by type
            ask_prompts = [p for p in self.prompt_files if p.prompt_type == PromptType.ASK]
            chat_prompts = [p for p in self.prompt_files if p.prompt_type == PromptType.CHAT]
            
            # Process ASK prompts first (sequential)
            logger.info(f"Processing {len(ask_prompts)} ask prompts for {client.name}")
            for prompt in ask_prompts:
                if not self._process_prompt_for_client(prompt, client, output_dir, nb_id):
                    logger.warning(f"Failed to process {prompt.filename} for {client.name}")
            
            # Process CHAT prompts (sequential)
            logger.info(f"Processing {len(chat_prompts)} chat prompts for {client.name}")
            for prompt in chat_prompts:
                if not self._process_prompt_for_client(prompt, client, output_dir, nb_id):
                    logger.warning(f"Failed to process {prompt.filename} for {client.name}")
            
            logger.info(f"Completed processing for client: {client.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing client {client.name}: {e}")
            return False

    def _process_prompt_for_client(
        self,
        prompt: PromptFile,
        client: Client,
        output_dir: Path,
        notebook_id: str
    ) -> bool:
        """
        Process a single prompt for a client
        
        Returns:
            True if successful
        """
        try:
            # Generate processed prompt
            processed_path = PromptProcessor.process_prompt(
                prompt.path,
                client,
                output_dir
            )
            
            if not processed_path:
                return False
            
            # Read processed content
            content = processed_path.read_text(encoding='utf-8')
            
            # Upload to notebook
            if prompt.prompt_type == PromptType.ASK:
                logger.info(f"Adding research source from {prompt.filename}")
                success = NotebookLMClient.add_research_source(content)
            else:  # CHAT
                logger.info(f"Asking question from {prompt.filename}")
                success = NotebookLMClient.ask_question(content)
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing prompt {prompt.filename}: {e}")
            return False

    def run(self) -> bool:
        """Execute full automation workflow"""
        logger.info("=" * 60)
        logger.info("Starting NotebookLM Automation")
        logger.info("=" * 60)
        
        # Step 1: Validate environment
        if not self._check_dependencies():
            return False
        
        # Step 2: Load configuration
        if not self.load_config():
            logger.error("Failed to load configuration")
            return False
        
        # Step 3: Discover prompts
        if not self.discover_prompts():
            logger.error("Failed to discover prompts")
            return False
        
        # Step 4: Authenticate
        if not NotebookLMClient.login():
            logger.error("Failed to authenticate with NotebookLM")
            return False
        
        # Step 5: Create notebooks
        if not self.create_notebooks():
            logger.warning("Some notebooks could not be created")
        
        # Step 6: Process clients in parallel
        logger.info("Processing clients in parallel...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.process_client, client): client
                for client in self.clients
            }
            
            results = {}
            for future in as_completed(futures):
                client = futures[future]
                try:
                    success = future.result()
                    results[client.name] = success
                    status = "✓ SUCCESS" if success else "✗ FAILED"
                    logger.info(f"{status}: {client.name}")
                except Exception as e:
                    logger.error(f"Error processing {client.name}: {e}")
                    results[client.name] = False
        
        # Summary
        logger.info("=" * 60)
        logger.info("Automation Summary")
        logger.info("=" * 60)
        successful = sum(1 for v in results.values() if v)
        logger.info(f"Completed: {successful}/{len(self.clients)} clients successful")
        
        for client_name, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} {client_name}")
        
        return all(results.values())

    def _check_dependencies(self) -> bool:
        """Verify required dependencies are available"""
        try:
            result = subprocess.run(
                ["notebooklm", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                logger.error(
                    "notebooklm CLI not found or not working. "
                    "Install with: pip install notebooklm-py[browser]"
                )
                return False
            logger.info("✓ notebooklm CLI available")
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.error(
                "notebooklm CLI not found. "
                "Install with: pip install notebooklm-py[browser]"
            )
            return False


def main():
    """Main entry point"""
    try:
        automation = NotebookLMAutomation()
        success = automation.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("Automation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
