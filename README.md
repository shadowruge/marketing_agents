# Agentes de Marketing

Equipe de agentes personalizados do OpenCode V2, criada com base na documentação: [https://opencode.ai/v2/docs/agents/](https://opencode.ai/v2/docs/agents/)

## Equipe

| Agente | Arquivo | Modo | Função |
| --- | --- | --- | --- |
| Diretor de Marketing | `agents/diretor-de-marketing.md` | `primary` | Orquestra a estratégia e delega aos especialistas |
| Copywriter | `agents/copywriter.md` | `subagent` | Textos de vendas, anúncios, e-mails e legendas |
| Estrategista de SEO | `agents/seo-estrategista.md` | `subagent` | Palavras-chave, conteúdo orgânico e SEO on-page |
| Gestor de Anúncios | `agents/gestor-de-anuncios.md` | `subagent` | Campanhas no Google Ads, Meta Ads etc. |
| Analista de Métricas | `agents/analista-de-metricas.md` | `subagent` | Dashboards, KPIs e leitura de resultados |

Os subagentes usam `model: opencode/deepseek-v4.1-flash-free` no frontmatter (ver [Modelo](#modelo)). O diretor não fixa modelo: ele usa o modelo da sessão, definido no `opencode.json`.

## Como instalar

Pelo script (recomendado — copia só os agentes, nunca sobrescreve seu `opencode.json`):

```sh
./install.sh            # instala no projeto atual: .opencode/agents/
./install.sh --global   # instala para todos os projetos: ~/.config/opencode/agents/
```

Manualmente, no projeto:

```sh
mkdir -p .opencode/agents
cp agents/*.md .opencode/agents/
```

Ou globalmente:

```sh
mkdir -p ~/.config/opencode/agents
cp agents/*.md ~/.config/opencode/agents/
```

> Copie **apenas** `agents/*.md`. O OpenCode transforma qualquer `.md` dentro de `agents/` em um agente; o `README.md` e o exemplo em `examples/` virariam agentes indesejados se fossem copiados junto.

> Nota: como os modos estão definidos no frontmatter, os `subagent` só rodam em sessões filhas (via ferramenta `subagent`). O `diretor-de-marketing` pode ser selecionado como agente principal da sessão.

### Configuração do projeto

O `opencode.json` deste repositório já traz o necessário:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "opencode/deepseek-v4.1-flash-free",
  "default_agent": "diretor-de-marketing"
}
```

`default_agent` faz o diretor ser o agente padrão de toda sessão nova — sem ele, você teria que selecioná-lo manualmente a cada vez. Se você já tem um `opencode.json`, copie as duas chaves em vez do arquivo inteiro (o `install.sh` não mexe nele de propósito).

## Modelo

Os subagentes fixam `model: opencode/deepseek-v4.1-flash-free` no frontmatter.

Motivo: o modelo padrão do ambiente (`big-pickle`) **corrompe texto em português** — insere caracteres CJK e palavras de outro idioma no meio das frases. Medido em teste: 4 de 4 agentes corrompidos com `big-pickle`, contra 0 de 9 execuções limpas com `deepseek-v4.1-flash-free`.

> Amostra pequena (9 execuções) e não reproduzível por terceiros: trate como indício, não como prova. Se for reproduzir, registre prompt, modelo e saída.

O `model` do frontmatter vale para **subagents**. Para o agente principal, vale o modelo da **sessão** — por isso o `opencode.json` do projeto define `model`. Sem ele, use a flag: `opencode run --agent diretor-de-marketing --model opencode/deepseek-v4.1-flash-free`.

> Se trocar o modelo, revalide: nem todo modelo alternativo é confiável. `glm-5.3-flash-free` também corrompeu em 1 de 6 execuções.

## Como usar

- Com o `default_agent` configurado, basta abrir o OpenCode no projeto e descrever a meta (ex.: "quero lançar um curso e preciso de um plano de marketing").
- Ou invoque um especialista diretamente: "Use o copywriter para criar 3 títulos de anúncio para o produto X".

Uma saída de referência do fluxo completo está em [`examples/plano-cafeteria-30dias.md`](examples/plano-cafeteria-30dias.md).

## Validação

`scripts/validate.py` confere o que o schema não pega:

- frontmatter obrigatório (`description`, `mode`, `color`) e `permissions` no formato V2 (`action`/`resource`/`effect`);
- `mode` coerente com o papel (subagente não fixa modelo de sessão; primary não deveria fixar `model`);
- `default_agent` do `opencode.json` aponta para um agente que existe;
- ausência de caracteres CJK nos textos;
- bloco "Revisão final" **idêntico** nos cinco agentes (ver manutenção).

Rode com `python3 scripts/validate.py`. O CI (`.github/workflows/validate.yml`) roda o mesmo script em cada push.

## Notas de manutenção

- O `diretor-de-marketing` só é confiável se delegar **um especialista por vez** e **aguardar** cada retorno. Sem isso, ele dispara chamadas em paralelo, o runtime encerra a sessão no meio e some com a entrega (já observado: 2 de 4 filhos sem saída, um duplicado, um nunca chamado). O frontmatter dele reforça essa regra e limita a delegação aos quatro especialistas (`subagent: "*"` negado, allow por ID) e a 12 passos.
- O bloco "Revisão final" é **repetido de propósito** nos cinco arquivos: cada agente precisa ser autocontido para instalação por cópia simples. O preço é manutenção em cinco lugares — por isso o validador falha se os blocos divergirem. Ao mudar uma regra, mude nos cinco.
- Se instalar nos dois lugares (projeto e global), mantenha os arquivos sincronizados — o do projeto tem precedência.

## Licença

MIT — ver [LICENSE](LICENSE).
