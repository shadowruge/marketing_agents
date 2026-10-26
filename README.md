# Agentes de Marketing

Equipe de agentes personalizados do OpenCode, criada com base na documentação:
<https://opencode.ai/v2/docs/agents/>

## Equipe

| Agente | Arquivo | Modo | Função |
| --- | --- | --- | --- |
| Diretor de Marketing | `diretor-de-marketing.md` | `primary` | Orquestra a estratégia e delega aos especialistas |
| Copywriter | `copywriter.md` | `subagent` | Textos de vendas, anúncios, e-mails e legendas |
| Estrategista de SEO | `seo-estrategista.md` | `subagent` | Palavras-chave, conteúdo orgânico e SEO on-page |
| Gestor de Anúncios | `gestor-de-anuncios.md` | `subagent` | Campanhas no Google Ads, Meta Ads etc. |
| Analista de Métricas | `analista-de-metricas.md` | `subagent` | Dashboards, KPIs e leitura de resultados |

Todos usam `model: opencode/deepseek-v4.1-flash-free` (ver [Modelo](#modelo)).

## Como instalar

Para usar em um projeto, copie os arquivos para a pasta `.opencode/agents/` do projeto:

```bash
mkdir -p .opencode/agents
cp agentes_marketing/{diretor-de-marketing,copywriter,seo-estrategista,gestor-de-anuncios,analista-de-metricas}.md .opencode/agents/
```

Ou instale globalmente para todos os projetos:

```bash
mkdir -p ~/.config/opencode/agents
cp agentes_marketing/{diretor-de-marketing,copywriter,seo-estrategista,gestor-de-anuncios,analista-de-metricas}.md ~/.config/opencode/agents/
```

> Não copie o `README.md` para a pasta de agentes: o OpenCode transforma
> qualquer `.md` em um agente, e o README viraria um agente inválido.

> Nota: como os modos estão definidos no frontmatter de cada arquivo, os agentes
> `subagent` só rodam em sessões filhas (via ferramenta `subagent`). O
> `diretor-de-marketing` pode ser selecionado como agente principal da sessão.

## Modelo

Os arquivos fixam `model: opencode/deepseek-v4.1-flash-free` no frontmatter.

Motivo: o modelo padrão do ambiente (`big-pickle`) **corrompe texto em
português** — insere caracteres CJK e palavras de outro idioma no meio das
frases. Medido em teste: 4 de 4 agentes corrompidos com `big-pickle`, contra
0 de 9 execuções limpas com `deepseek-v4.1-flash-free`.

O `model` do frontmatter vale para **subagents**. Para o agente principal
(`diretor-de-marketing`), o que vale é o modelo da **sessão** — por isso o
`opencode.json` do projeto:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "opencode/deepseek-v4.1-flash-free"
}
```

Sem isso, use a flag: `opencode run --agent diretor-de-marketing --model opencode/deepseek-v4.1-flash-free`.

> Se trocar o modelo, revalide: nem todo modelo alternativo é confiável.
> `glm-5.3-flash-free` também corrompeu em 1 de 6 execuções.

## Como usar

- Selecione o **diretor-de-marketing** como agente principal e descreva a meta
  (ex.: "quero lançar um curso e preciso de um plano de marketing").
- Ou invoque um especialista diretamente:
  "Use o copywriter para criar 3 títulos de anúncio para o produto X".

## Notas de manutenção

- O `diretor-de-marketing` só é confiável se delegar **um especialista por
  vez** e **aguardar** cada retorno. Sem isso, ele dispara chamadas em
  paralelo, o runtime encerra a sessão no meio e some com a entrega (já
  observado: 2 de 4 filhos sem saída, um duplicado, um nunca chamado). O
  frontmatter dele reforça essa regra.
- Os especialistas têm uma seção "Revisão final" que exige reler a própria
  entrega antes de responder. Sem ela, o copywriter devolvia rascunho e versão
  final lado a lado, com comentário interno no meio do texto.
- Se instalar nos dois lugares (projeto e global), mantenha os arquivos
  sincronizados — o do projeto tem precedência.
