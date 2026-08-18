# Contrato: API de atendimento — resolver (delta F3.6)

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md). Modelo:
[data-model.md](../data-model.md). Fila: [fila-e-worker.md](./fila-e-worker.md).

`GET /solicitacoes` **não muda o JSON**. Continua listando só `aberta` /
`em_andamento`. Depois de um `200` neste POST, o item some da lista. `POST /webhook`
e `GET /fila-do-dia` intocados.

---

## `POST /solicitacoes/{id_solicitacao}/resolucao`

Marca a pendência como resolvida e agenda a confirmação ao hóspede. Operação:
`resolver_solicitacao` (já na matriz; recepção e staff).

**Corpo da requisição:** vazio.

**Resposta `200`:**

```json
{
  "id_solicitacao": 7,
  "tipo": "reclamacao",
  "status": "resolvida",
  "resolvida_em": "2026-08-18T14:32:07.481Z",
  "id_usuario_responsavel": 3,
  "confirmacao": "agendada"
}
```

| Campo | Valores |
| --- | --- |
| `tipo` | `reclamacao` \| `servico` |
| `status` | Sempre `resolvida` numa resposta `200` |
| `resolvida_em` | Instante da resolução, com fuso |
| `id_usuario_responsavel` | Usuário da sessão que clicou |
| `confirmacao` | `agendada` \| `ja_agendada` |

`confirmacao` é o desfecho do **registro** da enviada + trabalho, não da
entrega: a entrega é do worker. `ja_agendada` só aparece na corrida em que
outra execução registrou o trabalho no mesmo instante — a resolução seguiu
válida.

**Campos que este contrato proíbe** no corpo `200` e em qualquer envelope de
erro:

- nome do hóspede, telefone, documento, endereço
- `descricao` do chamado (o staff já a viu na lista; não se copia de novo)
- texto da confirmação

**Erros:**

| Código | Quando | Corpo |
| --- | --- | --- |
| `401` | Sessão ausente ou inválida | `{"detail": "Sessao ausente ou invalida."}` |
| `403` | Perfil sem a operação (gestão) | `{"detail": "Perfil sem permissao para esta operacao."}` |
| `404` | Solicitação inexistente **ou** de outro hotel | `{"detail": "Solicitacao nao encontrada."}` |
| `409` | Já resolvida, tipo `consumo`, cancelada, ou outro estado que esta operação não fecha | `{"detail": "<motivo legível>"}` |

`404` para item de outro hotel é deliberado (FR-010): a resposta não distingue
"não existe" de "não é sua".

Motivos de `409` (português, sem dado cadastral):

| Situação | Detalhe (estável para teste) |
| --- | --- |
| Já `resolvida` | `Esta solicitacao ja foi resolvida.` |
| `tipo = consumo` | `Solicitacao deste tipo nao pode ser resolvida nesta operacao.` |
| `cancelada` | `Solicitacao cancelada nao pode ser resolvida.` |
| Outro status | `O estado atual da solicitacao nao admite resolucao.` |

**Efeitos de uma resposta `200`, na mesma transação:**

1. `solicitacao.status = 'resolvida'`, `resolvida_em` e
   `id_usuario_responsavel` preenchidos
2. `mensagem` (`enviada` / `pendente`) com o recado padrão do tipo
3. `trabalho` (`enviar_confirmacao_resolucao`) com
   `{id_reserva, id_solicitacao, id_mensagem}`

**Efeitos de `403`, `404` e `409`:** nenhum. Nada é gravado. Autor e instante
da primeira resolução, se existirem, permanecem.

---

## `GET /solicitacoes` (inalterado, asserção nova)

Mesmo JSON da F3.5. Asserção desta fatia: item com `status = resolvida` **não**
aparece. Passagem de turno = esta lista.

Staff / gestão / recepção da propriedade A não vêem item resolvido nem item do
hotel B. Destaque por tempo continua só nas que ainda estão abertas.

---

## Superfícies que esta fatia não cria

- `GET /solicitacoes/{id}`
- `POST` / `PATCH` de atribuir ou cancelar
- Rota de `consumo` / lançamento (F3.7)
- `GET /reservas/{id}/mensagens`
- Campo novo em `GET /fila-do-dia`
- Notificação push ao staff
- Tela React / passagem de turno agregada com ficha parcial
