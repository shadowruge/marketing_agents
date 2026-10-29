#!/usr/bin/env python3
"""Valida os agentes e a configuração do repositório.

Confere o que o schema do OpenCode não cobre: coerência entre modo e modelo,
formato V2 das permissões, default_agent existente, vazamento de CJK e
divergência do bloco de revisão final entre os agentes.

Uso: python3 scripts/validate.py
Requer PyYAML (pip install pyyaml).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("erro: PyYAML não instalado (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
CONFIG = ROOT / "opencode.json"

REVIEW_HEADING = "## Revisão final (obrigatória)"
MODES = {"primary", "subagent", "all"}
EFFECTS = {"allow", "ask", "deny"}
MODEL_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*(#[A-Za-z0-9._-]+)?$")
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")

errors: list[str] = []
warnings: list[str] = []


def err(path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def warn(path: Path, message: str) -> None:
    warnings.append(f"{path.relative_to(ROOT)}: {message}")


def split_frontmatter(text: str, path: Path) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        err(path, "sem frontmatter YAML (precisa começar com '---')")
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        err(path, "frontmatter não fechado com '---'")
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        err(path, f"YAML inválido no frontmatter: {exc}")
        return {}, parts[2]
    if not isinstance(meta, dict):
        err(path, "frontmatter precisa ser um mapa de chaves")
        return {}, parts[2]
    return meta, parts[2]


def check_permissions(path: Path, permissions: object) -> None:
    if not isinstance(permissions, list):
        err(path, "'permissions' precisa ser uma lista de regras")
        return
    for index, rule in enumerate(permissions, start=1):
        if not isinstance(rule, dict):
            err(path, f"permissions[{index}] precisa ser um mapa com action/resource/effect")
            continue
        missing = {"action", "resource", "effect"} - rule.keys()
        if missing:
            err(path, f"permissions[{index}] sem {', '.join(sorted(missing))}")
        if rule.get("effect") not in EFFECTS:
            err(path, f"permissions[{index}] effect inválido: {rule.get('effect')!r}")
        if not isinstance(rule.get("resource"), str) or not rule.get("resource"):
            err(path, f"permissions[{index}] resource precisa ser string não vazia")


def check_agent(path: Path) -> tuple[str, str] | None:
    meta, body = split_frontmatter(path.read_text(encoding="utf-8"), path)
    if not meta:
        return None

    agent_id = path.stem
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        err(path, "'description' ausente ou vazia")
    elif len(description) > 120:
        warn(path, "description longa (a UI mostra pouco texto)")

    mode = meta.get("mode")
    if mode not in MODES:
        err(path, f"mode inválido: {mode!r} (use {', '.join(sorted(MODES))})")

    color = meta.get("color")
    if not isinstance(color, str) or not COLOR_RE.match(color):
        err(path, f"color precisa ser hex de 6 dígitos (ex.: \"#e63946\"), recebido {color!r}")

    if "permissions" not in meta:
        err(path, "'permissions' ausente (negue edit/shell em agentes de conteúdo)")
    else:
        check_permissions(path, meta["permissions"])

    model = meta.get("model")
    if mode == "subagent" and not model:
        warn(path, "subagent sem 'model' — herda o modelo da sessão pai")
    if model is not None:
        if not isinstance(model, str) or not MODEL_RE.match(model):
            err(path, f"model deve ser 'provider/model' (opcional #variant), recebido {model!r}")
        if mode == "primary":
            warn(path, "agente primary fixando 'model': o modelo vale para a sessão, não para o agente")

    steps = meta.get("steps")
    if steps is not None and (not isinstance(steps, int) or steps < 1):
        err(path, f"steps precisa ser inteiro positivo, recebido {steps!r}")

    if CJK_RE.search(path.read_text(encoding="utf-8")):
        err(path, "contém caracteres CJK no texto")

    return body, agent_id


def main() -> int:
    if not AGENTS_DIR.is_dir():
        print(f"erro: pasta {AGENTS_DIR} não encontrada", file=sys.stderr)
        return 1

    agent_files = sorted(AGENTS_DIR.glob("*.md"))
    if not agent_files:
        print("erro: nenhum agente em agents/", file=sys.stderr)
        return 1

    ids: set[str] = set()
    review_blocks: dict[str, str] = {}

    for path in agent_files:
        result = check_agent(path)
        if result is None:
            continue
        body, agent_id = result
        ids.add(agent_id)

        marker = body.find(REVIEW_HEADING)
        if marker == -1:
            err(path, "bloco '## Revisão final (obrigatória)' ausente")
            continue
        review_blocks[agent_id] = body[marker:].strip()

    if len(set(review_blocks.values())) > 1:
        reference = review_blocks[sorted(review_blocks)[0]]
        for agent_id, block in sorted(review_blocks.items()):
            if block != reference:
                err(
                    AGENTS_DIR / f"{agent_id}.md",
                    "bloco de revisão final diverge dos demais — mantenha idêntico nos cinco agentes",
                )

    if not CONFIG.exists():
        err(CONFIG, "arquivo de configuração ausente")
    else:
        try:
            config = json.loads(CONFIG.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            err(CONFIG, f"JSON inválido: {exc}")
            config = {}
        if isinstance(config, dict):
            if config.get("$schema") != "https://opencode.ai/config.json":
                err(CONFIG, "'$schema' deve apontar para https://opencode.ai/config.json")
            default_agent = config.get("default_agent")
            if not default_agent:
                warn(CONFIG, "'default_agent' ausente — o diretor não será o agente padrão")
            elif default_agent not in ids:
                err(CONFIG, f"default_agent {default_agent!r} não corresponde a nenhum arquivo em agents/")
            model = config.get("model")
            if model is not None and (not isinstance(model, str) or not MODEL_RE.match(model)):
                err(CONFIG, f"model inválido: {model!r}")

    for path in sorted(ROOT.rglob("*.md")):
        if CJK_RE.search(path.read_text(encoding="utf-8")):
            err(path, "contém caracteres CJK no texto")

    for message in warnings:
        print(f"aviso: {message}")
    for message in errors:
        print(f"erro:  {message}")

    print(f"\n{len(agent_files)} agentes verificados — {len(errors)} erro(s), {len(warnings)} aviso(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
