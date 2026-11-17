# Integração com o Gen AI: aba "Publicações oficiais"

A aba **Publicações oficiais** do Zelo consulta o assistente de **Generative AI** do grupo (RAG sobre publicações de saúde do Diário Oficial do DF, de Henry Gimenez). A integração é isolada:

```
Zelo (Streamlit) → API do Zelo (/publicacoes) → serviço integracao_citizentech (porta 8100) → Gen AI (BM25 + verificação) → LM Studio (Qwen3-8B, porta 1234)
```

- O Zelo **nunca** fala com o LM Studio, só com o serviço `integracao_citizentech`, que apenas **importa** o Gen AI (nenhum arquivo congelado do módulo foi alterado; `verificar_hashes.py` continua `TODOS CONFEREM: True`).
- O CPF, telefone e e-mail da pergunta são apagados no Zelo antes de sair dele, e de novo dentro do Gen AI.
- **No Render a aba fica desligada**, porque o modelo precisa de ~8 GB de RAM. Ela funciona só na demonstração local.

## Requisitos do computador

| Item | Mínimo |
|---|---|
| RAM | 16 GB (feche navegadores e IDEs antes de rodar) |
| Disco livre | 10 GB |
| Placa de vídeo | Opcional. Com vídeo integrado, cada resposta leva de 30 s a 1,5 min |

## Passo a passo (Windows)

### 1. LM Studio e modelo
1. Instale o **LM Studio** (lmstudio.ai).
2. Na aba de busca (🔍), procure **`bartowski/Qwen_Qwen3-8B-GGUF`** e baixe o arquivo **`Qwen_Qwen3-8B-Q4_K_M.gguf`** (≈ 5 GB).
3. Confira o arquivo (opcional, recomendado pelo módulo): SHA-256 `54fffa050078e984116639c83dfb64b5aa6d4cd474e018b076777c632bbccccd`.
4. Na aba **Developer**, carregue o modelo com o identificador **`qwen3-8b`** e contexto **8192**, e clique em **Start Server** (porta 1234). Pelo terminal, o equivalente é:
   ```powershell
   lms load qwen_qwen3-8b --identifier qwen3-8b --context-length 8192 -y
   lms server start
   ```
5. Teste: abra http://localhost:1234/v1/models no navegador. Precisa aparecer `"id": "qwen3-8b"`.

### 2. Serviço do Gen AI (terminal 1)
Na pasta do módulo (`01_RPA` do repositório GS-CitizenTech, a que tem `citizentech/` e `integracao_citizentech/`):
```powershell
pip install numpy scipy pandas pyarrow requests psutil fastapi "uvicorn[standard]"
python scripts/verificar_hashes.py .          # deve terminar com TODOS CONFEREM: True
uvicorn integracao_citizentech.api:app --port 8100
```
Espere aparecer `Application startup complete` (leva ~15 s para carregar o índice). Teste: http://localhost:8100/saude precisa mostrar `"modelo_disponivel": true`.

### 3. Zelo apontando para o serviço (terminais 2 e 3)
No `backend\.env` do Zelo, adicione:
```dotenv
GENAI_URL=http://localhost:8100
```
Depois suba o Zelo normalmente (`uvicorn app.main:app --reload` no `backend` e `streamlit run app.py` no `frontend`) e abra a aba **Publicações oficiais**.

> **Memória (computadores com 16 GB):** o servidor do LM Studio cresce a cada pergunta (de ~5,4 para ~7,6 GB, segundo o módulo). Faça no máximo **3 perguntas seguidas** e então **ejete e carregue o modelo de novo** no LM Studio. Se a resposta vier "Assistente indisponível" ou com falha técnica, é isso: recarregue o modelo.

## O que mostrar na demonstração
1. **Uma pergunta respondida:** "Qual é o serviço de alimentação hospitalar contratado para as unidades de saúde em Ceilândia?". Mostre o status, a publicação (edição e data do DODF) e o trecho literal.
2. **Uma abstenção:** "Qual é a capital da França?" → *Fora do escopo*.
3. **Uma ambiguidade:** "Qual é o valor autorizado para pagamento ao Hospital das Clínicas e Pronto Socorro de Fraturas?" → o assistente pede para indicar a publicação.
4. **Integridade do módulo:** rode `python scripts/verificar_hashes.py .` e mostre o `TODOS CONFEREM: True`.

As respostas do modelo **variam entre execuções** (temperatura 0,3, sem semente), então o status pode não ser o mesmo acima. Isso é esperado e documentado pelo módulo.

## Sem o modelo (testes)
`integracao_citizentech/simulador_lmstudio.py` imita o LM Studio copiando o começo do trecho recuperado. Serve só para testar o caminho técnico; **não usar no vídeo nem em métricas**.
```powershell
uvicorn integracao_citizentech.simulador_lmstudio:app --port 1234
```

## Para apagar tudo depois
1. Configurações → Aplicativos → **LM Studio** → Desinstalar.
2. Apague `C:\Users\<usuário>\.lmstudio` e, se existir, `C:\Users\<usuário>\.cache\lm-studio` (o modelo de 5 GB fica aí).
