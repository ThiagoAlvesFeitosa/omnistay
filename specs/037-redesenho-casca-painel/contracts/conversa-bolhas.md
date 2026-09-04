# Contrato: bolhas da conversa

Componente compartilhado (ex.: `frontend/src/painel/BolhaConversa.tsx`).
Dois lados, nunca três. API de conversa e de simulador **não mudam**.

---

## Lados

| Lado | Simulador | Estadia |
| --- | --- | --- |
| Hóspede | `direcao = "recebida"` | `origem = "hospede"` |
| Hotel | `direcao = "enviada"` | `origem` = `recepcao` ou `automatico` |

Na Estadia o rótulo **Hóspede / Automático / Recepção** (F7.6)
permanece visível. Entrega (`enviando` / `enviada` / `falhou`)
permanece só na resposta da recepção.

Simulador: rótulos atuais de envio (`hóspede`, `hotel · …`) podem
permanecer como texto; o **lado** segue a direção.

---

## Horário

Campo: `enviada_em` no simulador; `em` na Estadia.
Formato: `formatarHorarioBolha` em
[apresentacao-br.md](./apresentacao-br.md).

---

## Gesto de envio

| Tela | Enter | Shift+Enter |
| --- | --- | --- |
| Simulador | envia (o mesmo do botão) | quebra linha, não envia |
| Estadia | **não** envia (já F7.6) | quebra linha |

Campo vazio + Enter no simulador: não inventa mensagem.

---

## Visual do simulador

Tipografia da família do painel autenticado (Tailwind da casca).
**Sem** `Georgia, serif` na página. Lista de reservas em cartão no
espírito das outras listas (borda, padding, um bloco por reserva).

---

## Fora

- Terceiro estilo de balão para origem.
- Relativo de urgência na bolha.
- Unificar Enter entre as duas telas.
- Mudar JSON de `GET /reservas/{id}/conversa` ou do simulador.
