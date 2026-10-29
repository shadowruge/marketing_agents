#!/usr/bin/env bash
# Instala os agentes de marketing do OpenCode.
# Uso: ./install.sh [--global]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$REPO_DIR/agents"

if [[ ! -d "$SRC_DIR" ]]; then
  echo "erro: pasta $SRC_DIR não encontrada. Rode o script a partir do repositório." >&2
  exit 1
fi

case "${1:-}" in
  ""|--project)
    DEST_DIR="$PWD/.opencode/agents"
    SCOPE="projeto"
    ;;
  --global)
    DEST_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode/agents"
    SCOPE="global"
    ;;
  -h|--help)
    echo "Uso: ./install.sh [--global]"
    exit 0
    ;;
  *)
    echo "erro: opção desconhecida '$1' (use --global ou nada para instalar no projeto)" >&2
    exit 1
    ;;
esac

mkdir -p "$DEST_DIR"

# Nunca copia README.md nem examples/: qualquer .md em agents/ vira um agente.
# Preserva nomes e sobrescreve apenas os cinco arquivos de agente.
count=0
for file in "$SRC_DIR"/*.md; do
  name="$(basename "$file")"
  if [[ -e "$DEST_DIR/$name" ]]; then
    echo "substituindo $DEST_DIR/$name"
  else
    echo "instalando  $DEST_DIR/$name"
  fi
  cp "$file" "$DEST_DIR/$name"
  count=$((count + 1))
done

echo
echo "$count agentes instalados (escopo: $SCOPE) em $DEST_DIR"

if [[ "$SCOPE" == "projeto" ]]; then
  echo
  echo "Para o diretor ser o agente padrão, garanta no opencode.json do projeto:"
  echo '  "default_agent": "diretor-de-marketing"'
  echo '  "model": "opencode/deepseek-v4.1-flash-free"'
else
  echo
  echo "Instalação global não altera ~/.config/opencode/opencode.json."
  echo "Adicione lá, se quiser o diretor como padrão:"
  echo '  "default_agent": "diretor-de-marketing"'
fi
