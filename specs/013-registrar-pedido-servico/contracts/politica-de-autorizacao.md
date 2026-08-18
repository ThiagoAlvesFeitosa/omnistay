# Contrato: política de autorização — F3.4

Estende a matriz vigente (F0.3 … F3.3). **Nenhuma operação nova.** Esta fatia **liga**
`ler_solicitacao_atribuida` à primeira rota.

---

## Operações

| Superfície | recepcao | operacional (`staff`) | gestao |
| --- | --- | --- | --- |
| Worker registrando pedido | — (processo interno; sem sessão) | — | — |
| `GET /solicitacoes` (`ler_solicitacao_atribuida`) | vê a fila operacional, sem ficha | vê a fila operacional, sem ficha | vê a fila operacional, sem ficha |
| `GET /fila-do-dia` | inalterado (pedido **não** liga o flag humano) | recusa | recusa |
| `GET /reservas/{id}/ficha` | inalterado | recusa | recusa |
| Webhook | inalterado | — | — |
| Histórico da conversa via HTTP | fora desta fatia | — | — |

O item de `GET /solicitacoes` **não** carrega nome, telefone nem documento. A
descrição é o texto do pedido — necessário para a equipe saber o que levar; não
é ficha cadastral. Continua proibido em log.

A sessão longa do staff só permanece aceitável porque este é o alcance: chamados
e pedidos, nunca ficha (F0.3 / Artefato 5 §11.2).

`resolver_solicitacao` e `lancar_consumo` continuam na matriz **sem rota**.

---

## Regras

- Isolamento: `id_hotel` da sessão em `listar_abertas`; `id_hotel` do trabalho em
  `abrir_servico` (bate com `reserva.id_hotel`). Hotel B não vê solicitação do
  hotel A.
- Cookie de sessão não dispara registro de pedido; só o worker.
- Staff autenticado em `GET /solicitacoes` **não** autoriza `GET /fila-do-dia`.
- Conteúdo do pedido e da confirmação nunca em log.

---

## Fora desta fatia

- Operação nova na matriz
- Resolver / atribuir solicitação
- Rota autenticada de histórico
- Inferência de chegada (Artigo I)
