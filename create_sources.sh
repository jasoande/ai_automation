
#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/vars.sh"

escape_sed_replacement() {
  printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'
}
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
    mkdir -p $SCRIPT_DIR/$client
    nb="$(notebooklm list | grep "$name_value" | awk '{print $2}')"
    notebooklm use "$nb"
    echo "Using notebook $nb for client $client"

    escaped_industry="$(escape_sed_replacement "$industry_value")"
    escaped_name="$(escape_sed_replacement "$name_value")"

    sed -e "s|\\\$industry|$escaped_industry|g" \
        -e "s|\\\$name|$escaped_name|g" \
        "$prompt_file" > "$output_dir/$prompt_name"
        echo "Generated prompt for $client at $output_dir/$prompt_name"

    gqp=$output_dir/$prompt_name

    #notebooklm source add-research "$gqp" --mode deep --import-all --no-wait
    if [[ "$gqp" == *"ask"* ]]; then
      research=$(cat "$gqp" )
      notebooklm source add-research "$research" --import-all
    else
      question=$(cat "$gqp")
      notebooklm ask "$question" --save-as-note
    fi

    echo "Generated $output_dir/$prompt_name and created notebooks at notebooklm.google.com"
  done
done
