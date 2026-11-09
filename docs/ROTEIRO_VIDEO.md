# Roteiro do vídeo (até 5 min)

| Tempo | O que mostrar | Dica |
|---|---|---|
| 0:00–0:40 | **Problema e público**: notícia de alagamento/buracos, quem sofre, ODS 11 e 13 | Abra com uma frase de impacto, ex.: "32 pontos de alagamento ao mesmo tempo em SP". |
| 0:40–2:10 | **Demo ponta a ponta** (cidadão): relato com telefone no texto → spinner/etapas → análise (cores + ícones, orientações, chuva) → **corrigir a urgência** → protocolo → ouvir em voz alta → "Meus relatos" e 👍 | Use um relato de alagamento ou fio caído para mostrar o banner de emergência. |
| 2:10–2:40 | **Gráficos e filtros**: Painel da cidade filtrando por tipo, bairro e período; hover e zoom | Mostre o padrão de textura nas barras (acessibilidade). |
| 2:40–3:00 | **Cenário de erro**: derrube a API (`docker compose stop api`) e tente analisar → mensagem amigável, texto preservado | Depois `docker compose start api`. |
| 3:00–3:20 | **Gestor**: login, fila priorizada, mudar status com mensagem; indicador "IA aceita sem correção" | |
| 3:20–4:20 | **Código**: árvore de pastas; `providers/llm.py` (único ponto que chama o LLM); `schemas/report.py::TriageResult`; `pipelines/triage.py` (retry + regras); `state/session.py`; `@st.cache_data` em `api_client.py`; `.env.example` + `.gitignore` (a chave nunca vai pro Git); `pytest` rodando | Cada integrante explica uma parte — prova de autoria. |
| 4:20–5:00 | **Validação**: tabela dos casos de teste da IA, resumo dos testes com 3 pessoas e o ajuste feito | Feche com o que aprenderam. |
