# Contrato: log e segredo

Fábrica: [modo-e-fabrica-llm.md](./modo-e-fabrica-llm.md). Adaptador:
[adaptador-real.md](./adaptador-real.md).

---

## O que o log operacional MAY registrar

- `llm_modo` (`controlado` \| `real`)
- Nome da classe escolhida
- `id_hotel`, `id_mensagem`, `id_trabalho`, `id_reserva`
- Código de falha da porta (`llm_tempo_esgotado`, `llm_quota`, …)
- Código de configuração inválida **sem** o valor da chave

## O que o log NUNCA registra

- `GEMINI_API_KEY` (nem prefixo, nem sufixo, nem “key=…”)
- Conteúdo da mensagem do hóspede
- Prompt enviado ao serviço
- Corpo da resposta do serviço (`bruto` fica no JSONB da mensagem,
  fora do log — regra já da F3.2)
- Texto do recado de boas-vindas

---

## Arquivos versionados

Nenhum segredo. `.env.example` tem os **nomes** das chaves, linha
`GEMINI_API_KEY=` vazia.

Teste: a árvore versionada (exceto `.env`, que não é versionado) não
contém valor com formato típico de chave Gemini. O `.env` local
permanece no `.gitignore`.

---

## Exceção de configuração

`ConfiguracaoDeInteligenciaInvalida` pode citar o **modo** recebido
(para diagnosticar `LLM_MODO=foo`). Não cita a chave. Real sem chave:
código estável (`chave_ausente`), não o valor vazio interpolado como
segredo.
