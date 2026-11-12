# Roteiro do vídeo — Zelo (até 5 min, um apresentador)

> Gravação: Gustavo Balbo (RM 561711), em nome do grupo Vinicius Araujo, Henry Gimenez e Gustavo Balbo.
> As falas são uma base: diga com as suas palavras. Ler palavra por palavra soa artificial e o professor
> avalia se você **entende** o código.

## Antes de gravar (checklist)

- [ ] App rodando **localmente com a IA real** (dois terminais: `uvicorn` e `streamlit`). A barra lateral mostra "classificação automática ativa".
- [ ] Abas abertas no navegador, nesta ordem:
  1. http://localhost:8501 (app local);
  2. https://zelo-web.onrender.com (aberto 5 min antes, para não "dormir");
  3. o repositório no GitHub;
  4. `docs/VALIDACAO.md` no GitHub.
- [ ] VS Code aberto no projeto, com estes arquivos já em abas:
  - `backend/app/providers/llm.py`
  - `backend/app/schemas/report.py`
  - `backend/app/pipelines/triage.py`
  - `frontend/state/session.py`
  - `frontend/providers/api_client.py`
  - `.gitignore`
- [ ] Relatos para colar (copie antes para um bloco de notas):
  - **Relato A:** `Caiu um fio do poste na calçada da minha rua e está soltando faísca, as crianças passam por ali para ir à escola. Meu telefone é 11 98765-4321.` (bairro: Centro · cidade: Osasco)
- [ ] Notificações do computador desligadas, zoom do navegador em 110–125%.
- [ ] Cronômetro: se passar de 5:00, corte nas partes marcadas com ✂️.

---

## 1. Problema, público e ODS — 0:00 a 0:35

**Tela:** README no GitHub, seção 1 (fontes) → depois o app local.

> "Oi, eu sou o Gustavo Balbo e vou apresentar o **Zelo**, o projeto do nosso grupo para a Global Solution de Front-end em Sistemas de IA.
>
> Em janeiro de 2025, São Paulo chegou a ter mais de 30 pontos de alagamento ao mesmo tempo, e a prefeitura já precisou de mutirão para zerar dezenas de milhares de pedidos de tapa-buraco. Quem sofre é o morador: ele vê o problema, mas não sabe como classificar, a quem recorrer nem o que fazer enquanto espera.
>
> O Zelo resolve isso: o cidadão conta o problema do jeito dele, a IA organiza, **ele confere**, e o app mostra o canal oficial da prefeitura. Isso conversa com o **ODS 11**, de cidades sustentáveis, e com o **ODS 13**, de ação climática, porque cruzamos o relato com a previsão de chuva."

## 2. Demonstração ponta a ponta — 0:35 a 2:20

**Tela:** app local, aba "Novo relato".

**Entrada e validação (0:35)**
- Clique em **Analisar** com o formulário vazio.
  > "Primeiro, a validação: se eu tentar enviar vazio, o app explica o que falta, em linguagem simples, antes de chamar qualquer coisa."
- Cole o **Relato A**, preencha "Centro" e "Osasco" e marque o consentimento.
  > "Agora um relato real. Repare que eu coloquei um telefone no texto, de propósito."

**Latência (0:55)**
- Clique em **Analisar** e deixe as etapas aparecerem.
  > "Enquanto a IA trabalha, o cidadão vê o que está acontecendo: remover dados pessoais, consultar dados públicos e classificar."

**Resposta (1:05)**
- Aponte, nesta ordem:
  1. o aviso de dado pessoal removido;
  2. o quadro de emergência;
  3. as etiquetas de categoria e urgência;
  4. o cartão "Onde registrar na prefeitura";
  5. a barra de confiança.

  > "O telefone foi apagado antes de chegar à IA, por causa da LGPD. Como é um fio soltando faísca, aparece o quadro de emergência com 199, 193 e 192, que no celular ligam com um toque. A urgência aparece com cor, ícone e texto, nunca só pela cor. E aqui está o canal oficial de Osasco, a Central 156, que vem de uma tabela verificada e não da IA. Já explico por quê."

**Human-in-the-loop (1:35)**
- Troque o **Tipo de problema** para "Outro problema" e mostre o campo que aparece. Depois volte para a categoria original.
- Mude a **Urgência** e clique em **Confirmar e registrar**.
  > "A IA sugere, mas quem decide é o cidadão. Ele pode corrigir categoria e urgência. Se escolher 'Outro', o app pede para ele dizer qual é o problema. A correção fica registrada e vira um indicador de qualidade da IA para o gestor."

**Protocolo (1:55)**
- Mostre o quadro "O que é o protocolo?" e o texto pronto para copiar. Clique em 🔊 por 2 segundos.
  > "O cidadão recebe o protocolo, com a explicação do que ele é, um texto pronto para colar no canal oficial e leitura em voz alta para acessibilidade."

## 3. Gráficos e filtros — 2:20 a 2:45

**Tela:** aba "Painel da cidade".
- Filtre por um **bairro** e por **urgência**, passe o mouse em uma barra e use o zoom da linha do tempo.
  > "No painel público, os dados são anônimos, sem texto nem endereço. Dá para filtrar por tipo, urgência, situação, bairro e período, e os gráficos em Plotly são interativos. Nas barras, a urgência também tem textura, para quem não distingue cores."

✂️ *Se estiver longo:* pule o zoom.

## 4. Cenário de erro tratado — 2:45 a 3:05

**Tela:** terminal do `uvicorn` ao lado do navegador.
- Aperte `Ctrl + C` no terminal da API. No app, volte em "Novo relato", escreva qualquer relato e clique em **Analisar**.
  > "E se a API cair? Eu desligo o back-end agora. O app não quebra: mostra uma mensagem clara, sem detalhes técnicos, e o texto que o cidadão digitou continua salvo."
- Religue com `uvicorn app.main:app --reload`, sem precisar mostrar.

## 5. Código — 3:05 a 4:15

**Tela:** VS Code. Mostre a árvore de pastas por 3 segundos e depois um arquivo por vez.

1. **Arquitetura (3:05).** Árvore `backend/` e `frontend/`.
   > "São dois serviços. O back-end em FastAPI tem routers, schemas, pipelines e providers. O front em Streamlit tem features, ui, state e providers. O front **nunca** fala com o provedor de IA."
2. **Chamada ao LLM (3:15).** `providers/llm.py`, método `complete`.
   > "A única chamada ao LLM está aqui, no back-end. Usamos a Groq com o modelo gpt-oss-120b."
3. **Saída estruturada (3:25).** `schemas/report.py`, classe `TriageResult`, e depois `pipelines/triage.py`, função `chamar_llm_estruturado`.
   > "A IA é obrigada a responder neste formato Pydantic, com categorias fechadas. Se vier fora do formato, devolvemos o erro para o modelo e ele tenta de novo."
4. **Regras de segurança (3:40).** Em `triage.py`, a função `remover_telefones_inventados`.
   > "Esta função nasceu da validação: no teste com a primeira pessoa, a IA inventou um telefone, '0800-xxxx', mesmo com o prompt proibindo. Aprendemos que regra no prompt não é garantia. Agora o código apaga qualquer telefone que não seja de emergência, e o canal oficial vem de uma tabela com fonte."
5. **Estado e cache (3:55).** `state/session.py` e, em `api_client.py`, os decorators `@st.cache_data` e `@st.cache_resource`.
   > "O estado da jornada fica centralizado no session_state. No cache, a mesma análise não gasta outra chamada à IA, e a conexão HTTP é reaproveitada."
6. **Chave protegida (4:05).** `.gitignore` com `.env` e o `.env.example`.
   > "A chave fica no .env, que está no .gitignore. No GitHub só existe o .env.example. No Render, ela é uma variável de ambiente. O CORS aceita só a origem do front."

✂️ *Se estiver longo:* junte os itens 5 e 6 em uma frase.

## 6. Validação e aprendizado — 4:15 a 4:50

**Tela:** `docs/VALIDACAO.md` no GitHub. Role pela tabela e pelo antes × depois. Depois mostre a seção 8.2 do README.

> "Testamos com três moradores de 19 e 20 anos, de Osasco, Taboão da Serra e da região oeste. Todos concluíram sem ajuda, dois pelo celular, e deram 4 de 5. Com o feedback deles, adicionamos o canal oficial da prefeitura, o campo para 'Outro problema', a explicação do protocolo, os botões de emergência e o aviso de quando o servidor está ligando, além de trocar 'Urgência Crítica', que assustava, por 'Urgência Máxima' com instrução clara.
>
> Nos casos de teste da IA, ela acertou 6 de 6 na rodada final, inclusive resistindo a uma tentativa de prompt injection. Antes disso, ajustamos o modelo, que tinha sido desativado pela Groq, e o limite de requisições."

## 7. Encerramento — 4:50 a 5:00

**Tela:** aba do deploy, https://zelo-web.onrender.com.

> "O Zelo está publicado no Render, e o link está no README. Obrigado!"

---

### Dicas de gravação

- Use o OBS ou o gravador do Windows (`Win + Alt + R`). Grave tela e voz juntas.
- Ensaie uma vez com o cronômetro antes de gravar valendo.
- Se errar uma parte, pare, respire e repita só aquela frase: dá para cortar depois no editor do YouTube ou no Clipchamp.
- Publique no YouTube como **Não listado** e cole o link no README (linha do 🎬 Vídeo).
