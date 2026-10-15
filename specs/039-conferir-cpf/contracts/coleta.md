# Contrato: coleta (WhatsApp / simulador)

Caminho já existente: extração → `refinar_resultado` →
`consolidar_ficha_titular`. Sem tipo novo de trabalho. Sem mensagem
nova.

## Quando o CPF é reprovado

- `numero_documento` **não** vai para `hospede`
- demais campos utilizáveis **permanecem**
- desfecho **não** é completa se o número era necessário
- reserva em `aguardando_cadastro` → `ficha_parcial` (como hoje
  quando falta campo)
- **zero** mensagem de correção ao hóspede
- fila do dia: distintivo de parcial já existente

## Quando o CPF é aceito

- grava onze dígitos
- se os nove campos utilizáveis fecham, `ficha_recebida` como hoje

## Log

Padrão já de `ficha_consolidada`: `id_reserva`, `id_hospede`,
status, contagem de campos. **Sem** número, nome, telefone.
