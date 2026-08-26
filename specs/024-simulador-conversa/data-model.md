# Modelo de dados — Simulador de Conversa

Referência: `docs/04-schema.sql`. Decisões em [research.md](./research.md).
Esta fatia **não cria tabela**. O modo de canal não é linha de banco.
O fio da tela é a `mensagem` já existente; a idempotência da entrada é
o `evento_webhook.id_externo` já existente.

---

## Entidades novas (só de configuração / superfície)

### Modo de canal

Não é tabela. É configuração do processo (`MENSAGERIA_MODO`).

| Valor | Adaptador de saída | Tela como canal |
| --- | --- | --- |
| `demonstracao` | `MensageriaSimulada` (sucesso local, sem rede) | Opera (GET + POST autenticados) |
| `real` | `MensageriaWhatsapp` | Recusa `409 modo_real` |

Um valor por processo. Ausente ou outro texto: o processo não sobe a
fábrica. Não há coluna em `reserva` nem em `hotel`.

---

## Entidades reusadas — o que a tela lê e escreve

### `mensagem`

Fonte da verdade do fio. A tela **não** tem cópia.

| Campo | Papel na tela |
| --- | --- |
| `id_mensagem` | Identidade do turno |
| `id_reserva` | Conversa escolhida (sempre filtrada pelo hotel da sessão via reserva) |
| `direcao` | `enviada` = hotel → hóspede; `recebida` = hóspede → hotel |
| `conteudo` | Texto visível. **Não** vai para log |
| `status_envio` | Só em `enviada`: `pendente` / `enviada` / `falha` (e `entregue` se um dia existir). A tela mostra o status; não inventa um quarto valor |
| `enviada_em` | Ordem cronológica (desempate: `id_mensagem`) |
| `id_externo` | No turno do hóspede, ecoa o id da entrada (idempotência) |

Consultas: `WHERE id_reserva = :id` com join/filtro `reserva.id_hotel =
:sessao`. Hotel B não lê mensagem de A.

`pendente` aparece: o worker ainda não “entregou” na tela. Isso é
visibilidade da ausência, não um buffer paralelo.

### `evento_webhook`

Entrada simulada **grava evento** com o `id_externo` enviado pelo
cliente, depois a mensagem e o trabalho — o mesmo `receber_evento_entrada`
do webhook. UNIQUE de `id_externo` impede o segundo processamento.

Prefixo recomendado ao gerar no cliente: `sim:` + UUID, para não colidir
com id da Meta se alguém misturar túnel e demo (limitação da pesquisa
§4). Não é CHECK no banco.

Payload do evento: identificadores e flags, **sem** copiar o texto da
conversa para log. O texto mora só em `mensagem.conteudo`.

### `reserva`

A lista da tela é reservas da propriedade da sessão. Não cria reserva
de palco.

| Campo | Papel |
| --- | --- |
| `id_reserva` | Escolha da conversa |
| `status` | Exibido para o apresentador saber se é ficha ou estadia |
| `telefone_contato` | Identidade de canal (normalizado). Entra em `EventoEntrada.telefone_origem` |
| titular (nome) | Rótulo na lista — leitura via serviço de hospedagem, sem o módulo `conversa` consultar tabela de hóspede direto |

O INSERT da mensagem **não** usa `id_reserva` para furar o resolver.
O telefone da reserva escolhida alimenta o mesmo resolver do webhook
(`aguardando_cadastro` vence `hospedado`, etc.).

Reserva inexistente ou de outro hotel: a API responde `404` antes de
montar o evento.

### `trabalho`

Nenhum tipo novo. Entrada simulada enfileira `interpretar_ficha` ou
`classificar_mensagem` (e os ramos já existentes) como o webhook.
Saída continua `enviar_*` já existentes; o adaptador é que muda.

---

## O que não nasce

- Coluna `origem` / `canal` em `mensagem`
- Tabela `conversa_simulada` ou buffer de tela
- Chave em `parametro_hotel`
- Revisão Alembic
- Tipo novo em `trabalho`

---

## Regras de validação (aplicação)

| Situação | Efeito |
| --- | --- |
| Modo `real` | Nenhuma leitura/escrita da tela como canal |
| Texto vazio ou só branco | Recusa; zero INSERT |
| Sem `id_externo` no POST | Recusa; zero INSERT |
| `id_externo` repetido | Sem segunda mensagem; desfecho já conhecido |
| Telefone da reserva inválido | Recusa alinhada ao webhook (`telefone_invalido`); não inventa hóspede |
| Duas reservas, mesmo telefone | Ordem do resolver do webhook, não a da linha clicada |

---

## Relacionamentos

```text
hotel 1 ──< reserva 1 ──< mensagem
                │
                └── telefone_contato → EventoEntrada → evento_webhook (UNIQUE id_externo)
                                              └── trabalho (tipos já existentes)
```

O modo de canal não aparece neste diagrama: ele escolhe o adaptador de
*saída* e se a tela pode *entrar*.
