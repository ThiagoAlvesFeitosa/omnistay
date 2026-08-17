# Contrato: política de autorização — F3.3

Estende a matriz vigente (F0.3 … F3.2). **Nenhuma operação nova.**

---

## Operações

| Superfície | recepcao | operacional | gestao |
| --- | --- | --- | --- |
| Worker respondendo (`responder_duvida`) | — (processo interno; sem sessão) | — | — |
| `GET /fila-do-dia` (`ler_fila_do_dia`) | vê o booleano (agora também por `duvida_nao_coberta`) | recusa | recusa |
| Manutenção / ativo do catálogo | inalterado (F2.1) | recusa | lê, não altera |
| Histórico da conversa via HTTP | fora desta fatia | — | — |
| Webhook | inalterado | — | — |

O booleano **não** carrega texto da pergunta nem da resposta. Perfil operacional
**não** passa a ver fila do dia nem dado cadastral — o Alert Center operacional é
F3.5. O chamado desta fatia é da recepção.

Quando uma fatia futura expor histórico HTTP, a leitura do conteúdo permanece no
mínimo tão restrita quanto `ler_dado_cadastral_de_hospede`. Nesta fatia a suíte lê
`mensagem` no banco de teste.

---

## Regras

- Isolamento: `id_hotel` do trabalho em toda leitura de catálogo, gravação de
  mensagem e sinal na fila. Hotel B não recebe resposta nem chamado do hotel A.
- Conteúdo de pergunta, resposta, trechos e itens de catálogo nunca em log.
- Cookie de sessão não dispara conversação; só o worker.
- Esta fatia não autoriza criar `solicitacao`.

---

## Fora desta fatia

- Operação nova na matriz
- Rota autenticada de histórico
- Alert Center / `solicitacao` visível ao perfil operacional
- Inferência de chegada (Artigo I)
