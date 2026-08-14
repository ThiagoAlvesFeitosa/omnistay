# Contrato: política de autorização — F1.4

Estende a matriz vigente (F0.3 / F1.1–F1.3). **Nenhuma operação nova de painel.**

---

## Operações

| Operação | recepcao | operacional | gestao |
| --- | --- | --- | --- |
| `ler_fila_do_dia` (inclui `sem_cadastro_previo`) | sim | não | não* |
| `ler_ficha_de_hospede` | sim | não | não |
| Verificar cadastros pendentes / enviar lembrete | — (processo worker; sem sessão de painel) | — | — |

\*Gestão continua só com indicadores agregados.

---

## Regras

- A indicação “chegará sem cadastro prévio” é dado operacional da **fila nominada**: só
  recepção do hotel da reserva.
- Worker/agendador não autentica perfil; opera com `id_hotel` da própria reserva.
- Conteúdo de mensagem e dados pessoais nunca em log, qualquer caminho.

---

## Fora desta fatia

- Tela de parâmetros da propriedade
- Check-in
- Revogação de sessão / usuários (já existem)
