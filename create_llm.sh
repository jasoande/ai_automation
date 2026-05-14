
#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/vars.sh"

escape_sed_replacement() {
  printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'
}

# Log into google notebooklm
notebooklm login

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


   if [[ -z "$(notebooklm list | grep "$name_value")" ]]; then
      notebooklm create "$name_value"
      echo "Created notebook for $client with name $name_value"
   fi
  done
done
exit 0
