# Contrato: política de autorização — F3.2

Estende a matriz vigente (F0.3 … F3.1). **Nenhuma operação nova.**

---

## Operações

| Superfície | recepcao | operacional | gestao |
| --- | --- | --- | --- |
| Worker classificando (`classificar_mensagem`) | — (processo interno; sem sessão) | — | — |
| `GET /fila-do-dia` (`ler_fila_do_dia`) | vê `precisa_atendimento_humano` | recusa | recusa |
| Histórico da conversa via HTTP | fora desta fatia | — | — |
| Webhook | inalterado (público: assinatura; sem sessão) | — | — |

O booleano **não** carrega texto da mensagem nem dado cadastral extra. Continua
atrás de `ler_fila_do_dia`: só recepção do mesmo hotel. Perfil operacional **não**
passa a ver fila do dia para “pegar o encaminhamento” — o Alert Center é F3.5.

Quando uma fatia futura expor histórico HTTP, a leitura do conteúdo permanece no
mínimo tão restrita quanto `ler_dado_cadastral_de_hospede`. Nesta fatia a suíte lê
`mensagem` no banco de teste.

---

## Regras

- Classificar não autoriza envio ao hóspede nem criação de chamado.
- Isolamento: `id_hotel` do trabalho em toda leitura/gravação de mensagem. Hotel B
  não recebe eixos nem sinal do hotel A.
- Conteúdo de mensagem, telefone em claro e `bruto` do classificador nunca em log,
  qualquer caminho (inclusive indisponível / inválido).
- Cookie de sessão não dispara classificação; só o worker.

---

## Fora desta fatia

- Operação nova na matriz
- Rota autenticada de histórico
- Alert Center / `solicitacao` visível ao perfil operacional
- Inferência de chegada (Artigo I)
