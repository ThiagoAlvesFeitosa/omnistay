# Contrato: política de autorização — F3.6

Estende a matriz vigente (F0.3 … F3.5). **Nenhuma operação nova.** Esta fatia
**liga** `resolver_solicitacao` à rota de resolução.

---

## Operações

| Superfície | recepcao | operacional (`staff`) | gestao |
| --- | --- | --- | --- |
| `POST /solicitacoes/{id}/resolucao` (`resolver_solicitacao`) | resolve, sem ficha na resposta | resolve, sem ficha na resposta | **recusa 403** |
| `GET /solicitacoes` (`ler_solicitacao_atribuida`) | vê só abertas / em andamento | o mesmo | o mesmo (consulta; não fecha) |
| `GET /fila-do-dia` | inalterado | recusa | recusa |
| `GET /reservas/{id}/ficha` | inalterado | recusa | recusa |
| Worker enviando confirmação | — (processo interno; sem sessão) | — | — |
| Histórico da conversa via HTTP | fora desta fatia | — | — |

O corpo `200` do POST **não** carrega nome, telefone, documento nem descrição.
`id_usuario_responsavel` é identificador operacional de quem clicou, não ficha
de hóspede.

A sessão longa do staff só permanece aceitável porque o alcance continua:
chamados e pedidos, nunca ficha (F0.3 / Artefato 5 §11.2). Fechar chamado é
exatamente a operação que a matriz reservou a esse perfil.

`lancar_consumo` continua na matriz **sem rota**.

---

## Regras

- Isolamento: `id_hotel` da sessão no `UPDATE` e no `SELECT` de recusa (join
  com `reserva`). Hotel B não resolve chamado do hotel A e recebe `404`.
- Gestão autenticada em `GET /solicitacoes` **não** autoriza o POST.
- Staff autenticado no POST **não** autoriza `GET /fila-do-dia` nem ficha.
- Conteúdo da confirmação e descrição do chamado nunca em log.
- Cookie de sessão do POST não dispara envio; só o worker envia.

---

## Fora desta fatia

- Operação nova na matriz
- Atribuir / cancelar solicitação
- Rota autenticada de histórico
- Inferência de chegada (Artigo I)
