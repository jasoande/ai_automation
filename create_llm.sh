#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/vars.sh"

# Basic installation of notebooklm-py
#pip install notebooklm-py

#With browser login support (required for first-time setup)
#pip install "notebooklm-py[browser]"
#playwright install chromium

# Optional: import cookies from your existing browser instead of running Playwright
#pip install "notebooklm-py[cookies]"

escape_sed_replacement() {
  printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'
}

# Log into google notebooklm
notebooklm login --browser-cookies chrome

for prompt_file in "$SCRIPT_DIR"/*prompt*.txt  ;do
  [ -f "$prompt_file" ] || continue
  prompt_name="$(basename "$prompt_file")"

  for client in "${clients[@]}"; do
    industry_var="${client}_industry"
    name_var="${client}_name"
    industry_value="${!industry_var}"
    name_value="${!name_var}"

    output_dir="$SCRIPT_DIR/$client"
    mkdir -p "$output_dir/"

    echo "Processing client: $name_value in industry: $industry_value"
    if ! notebooklm list | grep "$name_value"; then
      echo "Creating notebook for $name_value"
      notebooklm create "$name_value"
    else
      echo "Notebook for $name_value already exists"
    fi
    notebooklm login --browser-cookies chrome
    nb="$(notebooklm list | grep "$name_value" | awk '{print $2}')"
    notebooklm use "$nb"
    echo "Using notebook $nb for client $client"
  done
done
