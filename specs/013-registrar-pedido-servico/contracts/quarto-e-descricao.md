# Contrato: quarto e descrição da solicitação

Modelo: [data-model.md](../data-model.md). Serviço:
[api-de-atendimento.md](./api-de-atendimento.md).

---

## Descrição

`solicitacao.descricao` = `mensagem.conteudo` da recebida que originou o pedido.
Não é resumida por modelo. Não é reescrita com conhecimento geral sobre o hotel.

Teste: a descrição gravada é igual ao texto que o hóspede enviou.

---

## Quarto

Função pura `extrair_numero_quarto(texto) -> str | None`.

| Entrada (exemplos) | Saída |
| --- | --- |
| `pode mandar uma toalha extra no quarto 402` | `402` |
| `travesseiro, apto 12` | `12` |
| `cobertor no apartamento 8B` | `8B` |
| `uh 15 precisa de toalha` | `15` |
| `toalha extra` | nulo |
| `estou no 402` (sem palavra-chave) | nulo |
| texto de outra reserva / outro hotel | não se consulta; só o texto desta mensagem |

Normalização: `casefold` na busca; valor gravado preserva o token numérico (dígitos
+ letra opcional), até 10 caracteres. Primeiro match vence.

**Proibido:** completar quarto a partir da reserva, do PMS, de pedido anterior ou
de outro hóspede. Pedido sem quarto **ainda** gera solicitação e confirmação.

Testes unitários cobrem os exemplos da tabela. Teste de serviço: mensagem sem
quarto → `numero_quarto` nulo e linha mesmo assim; mensagem com `quarto 402` →
campo igual a `402`.
