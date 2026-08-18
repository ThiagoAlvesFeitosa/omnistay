# Contrato: política de autorização — F3.5

Estende a matriz vigente (F0.3 … F3.4). **Nenhuma operação nova.** Esta fatia
continua ligando `ler_solicitacao_atribuida` à mesma rota.

---

## Operações

| Superfície | recepcao | operacional (`staff`) | gestao |
| --- | --- | --- | --- |
| Worker abrindo chamado | — (processo interno; sem sessão) | — | — |
| `GET /solicitacoes` (`ler_solicitacao_atribuida`) | vê serviço **e** reclamação, sem ficha | vê serviço **e** reclamação, sem ficha | vê serviço **e** reclamação, sem ficha |
| `GET /fila-do-dia` | inalterado (reclamação **não** liga o flag humano) | recusa | recusa |
| `GET /reservas/{id}/ficha` | inalterado | recusa | recusa |
| Webhook | inalterado | — | — |
| Histórico da conversa via HTTP | fora desta fatia | — | — |
| Alterar `horas_destaque_chamado_aberto` | recusa (sem rota) | recusa | sem rota nesta fatia |

O item de `GET /solicitacoes` **não** carrega nome, telefone nem documento. A
descrição é o relato do problema — necessário para a manutenção saber o que
consertar; não é ficha cadastral. Continua proibido em log. A janela de
preferência é operacional e também **não** vai para log.

A sessão longa do staff só permanece aceitável porque este é o alcance: chamados
e pedidos, nunca ficha (F0.3 / Artefato 5 §11.2).

`resolver_solicitacao` e `lancar_consumo` continuam na matriz **sem rota**.

---

## Regras

- Isolamento: `id_hotel` da sessão em `listar_abertas`; `id_hotel` do trabalho em
  `abrir_reclamacao` e `completar_janela_se_resposta` (bate com `reserva.id_hotel`).
  Hotel B não vê chamado do hotel A nem completa janela dele.
- Cookie de sessão não dispara abertura de chamado; só o worker.
- Staff autenticado em `GET /solicitacoes` **não** autoriza `GET /fila-do-dia`.
- Conteúdo da reclamação, da confirmação e da janela nunca em log.
- Reclamação técnica **não** reutiliza o sinal de atendimento humano da fila do
  dia.

---

## Fora desta fatia

- Operação nova na matriz
- Resolver / atribuir solicitação
- Rota autenticada de histórico
- Tela para o prazo de destaque (gestão)
- Inferência de chegada (Artigo I)
