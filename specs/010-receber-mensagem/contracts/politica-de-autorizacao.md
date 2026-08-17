# Contrato: política de autorização — F3.1

Estende a matriz vigente (F0.3 … F2.2). **Nenhuma operação nova.**

---

## Operações

| Superfície | recepcao | operacional | gestao |
| --- | --- | --- | --- |
| Webhook (`GET`/`POST /webhook`) | — (canal público: assinatura / token de posse; sem sessão) | — | — |
| Histórico da conversa via HTTP | fora desta fatia | — | — |

O conteúdo da mensagem recebida é dado da conversa da reserva. Quando uma fatia futura
expor `GET` de histórico, a leitura será no mínimo tão restrita quanto
`ler_dado_cadastral_de_hospede` (só recepção do mesmo hotel). Nesta fatia a suíte lê o
banco de teste, não uma rota de painel.

---

## Regras

- Perfil de painel **não** autoriza o webhook. Cookie de sessão não substitui assinatura.
- Assinatura inválida, ausente ou segredo vazio: recusa sem efeito, qualquer origem.
- Isolamento: telefone resolve reserva só no `id_hotel` do canal. Hotel B não recebe
  conversa do hotel A.
- Conteúdo de mensagem, telefone em claro e payload bruto nunca em log, qualquer caminho.

---

## Fora desta fatia

- Rota autenticada de histórico
- Inferência de chegada por mensagem (não é permissão: é Artigo I)
- Classificação e abertura de chamado (F3.2+)
