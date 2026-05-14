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

# Log into google notebooklm
notebooklm login

escape_sed_replacement() {
  printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'
}

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
    if [[ -z $(notebooklm list | grep "$name_value") ]]; then
      echo "Creating notebook for $name_value"
      notebooklm create "$name_value"
    else
      echo "Notebook for $name_value already exists"
    fi

    nb="$(notebooklm list | grep "$name_value" | awk '{print $2}')"
    echo "Using notebook $nb for client $client"

    escaped_industry="$(escape_sed_replacement "$industry_value")"
    escaped_name="$(escape_sed_replacement "$name_value")"

    sed -e "s|\\\$industry|$escaped_industry|g" \
        -e "s|\\\$name|$escaped_name|g" \
        "$prompt_file" > "$output_dir/$prompt_name"
        echo "Generated prompt for $client at $output_dir/$prompt_name"

    gqp=$output_dir/$prompt_name

    echo "Switching to notebook $nb and adding $gqp"
    notebooklm use "$nb"
    #notebooklm source add-research "$gqp" --mode deep --import-all --no-wait
    if [[ "$gqp" == *"ask"* ]]; then
      research=$(cat "$gqp" )
      notebooklm source add-research --no-wait "$research"
      notebooklm research status
      notebooklm research wait --import-all
    else
      #notebooklm source add-research "$gqp" --import-all --no-wait
      question=$(cat "$gqp")
      notebooklm ask "$question" --save-as-note
    fi

    echo "Generated $output_dir/$prompt_name and created notebooks at notebooklm.google.com"
  done
done
