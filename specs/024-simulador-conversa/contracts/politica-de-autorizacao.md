# Contrato: política de autorização — F6.2

Estende a matriz vigente. Acrescenta **uma** operação nova e a liga às
três rotas da tela. Não altera webhook, fila do dia, catálogo, mercado
nem retenção.

A política continua decisão pura: perfil × operação, sem HTTP e sem
banco. Isolamento por hotel é ortogonal (`id_hotel` da sessão; alvo
alheio → `404`). Modo `real` é recusa de **canal**, não de perfil
(`409`, não `403`).

---

## Operações desta fatia

| Operação | `recepcao` | `staff` | `gestor` | Rotas |
| --- | :---: | :---: | :---: | --- |
| `usar_simulador` | ✅ | ❌ | ✅ | `GET /simulador/conversas`, `GET /simulador/conversas/{id}`, `POST .../mensagens` |

Não reutilizar:

| Operação existente | Por que não |
| --- | --- |
| `ler_dado_cadastral_de_hospede` | Só recepção; a spec entrega a tela também à gestão. Além disso, a ficha completa não é esta superfície |
| `ler_fila_do_dia` | Só recepção; só o turno. A banca escolhe qualquer reserva da casa |
| `ler_indicadores` | Contagem, não conversa |
| Webhook (sem operação) | Canal público com HMAC; cookie **não** substitui assinatura e assinatura **não** abre a tela |

`POST /webhook` **não ganha** operação de painel. Continua F3.1.

---

## Regras

- Recepção e gestão da **própria** propriedade usam a tela em modo
  `demonstracao`.
- Staff: `403`. Alert Center não é palco.
- Sem sessão: `401`.
- Modo `real`: `409 modo_real` mesmo com perfil permitido — a tela não
  é canal.
- Gestão nesta superfície vê nome do titular e telefone de contato da
  **lista/fio**, o mínimo para escolher a conversa. Não abre
  `GET /reservas/{id}/ficha` nem `alterar_reserva`. A recusa genérica
  da F0.3 sobre cadastro permanece nas rotas de hospedagem.
- Isolamento: reserva de outro hotel → `404`.
- Cookie de sessão **não** autoriza `POST /webhook`. HMAC **não**
  autoriza `POST /simulador/...`.

---

## Recusa visível

| Situação | Resposta |
| --- | --- |
| Sem sessão válida | `401` |
| Sessão válida, perfil sem permissão | `403` |
| Sessão válida, modo `real` | `409` |
| Sessão válida, reserva de outro hotel ou id inexistente | `404` |
| Texto vazio / `id_externo` ausente | `400` |

---

## Fora desta fatia

- Staff “só lendo” a tela
- Tela anônima para a banca sem login
- Recepção usando a tela em produção com hóspede real (modo deve ser
  `real`; a tela recusa)
