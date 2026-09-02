# Contrato: POST resposta da recepção

Autenticação e hotel: iguais ao GET da conversa.

Operação `enviar_resposta_recepcao` (só `recepcao`).

---

## `POST /reservas/{id_reserva}/respostas`

```json
{ "texto": "Sim, temos berço no quarto." }
```

**201** — texto gravado como enviada `pendente`, trabalho
`enviar_resposta_recepcao` enfileirado. Corpo: o item da mensagem
(mesmo formato do GET) + `janela` atual. O HTTP **não** espera o
canal. `solicitacao` intocada.

**401** — sem sessão.

**403** — `staff` / `gestor`.

**404** — reserva inexistente ou de outro hotel.

**409** — janela fechada (`janela_fechada`) **ou** texto idêntico
ao da última resposta da recepção nesta reserva há menos de 5
segundos (`texto_repetido`). Nada gravado.

**422** — texto ausente, vazio, só espaços, ou maior que 4096
caracteres. Nada gravado.

Clique duplo: a tela deixa **Enviar** inerte até o POST voltar.
O servidor **não** usa UNIQUE por reserva. Texto diferente em
seguida é `201`. Texto igual depois de 5 s é `201`.

Não dispara recado de resolução. Não exige chamado aberto.
