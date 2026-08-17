# Contrato — recado de boas-vindas: texto, fila e porta de mensageria

---

## 1. Montagem do texto (função pura)

`app/modulos/conversa/texto_boas_vindas.py`

```python
def montar_texto_boas_vindas(
    *, nome_completo: str, cafe: str, wifi: str, checkout: str
) -> str: ...
```

Sem I/O, sem banco, sem relógio. Recebe valores já validados.

**Estrutura obrigatória**, na ordem, com rótulo fixo imediatamente antes de cada variável:

```text
Ola, {prenome}! Sua chegada esta confirmada, seja bem-vindo.
Cafe da manha: {cafe}
Wi-Fi: {wifi}
Checkout: {checkout}
Quer saber mais alguma coisa da sua estadia? Pode perguntar por aqui.
```

| Exigência | Verificação no teste |
| --- | --- |
| Confirma a chegada | Texto contém a confirmação |
| Exatamente três fatos | Os três valores aparecem; nenhum outro fato |
| Rótulo fixo antes de cada variável | `Cafe da manha:`, `Wi-Fi:`, `Checkout:` |
| Um único convite ao final | Exatamente uma interrogação, na última linha |
| Sem catálogo | Nenhum item de `catalogo_item` é lido — a função não recebe catálogo |
| Sem oferta | Nenhum termo de desconto, promoção ou compra |
| Um dado pessoal | Só o primeiro nome (`primeiro_nome` já existe em `texto_coleta`) |

Os `\n` do corpo montado existem no **histórico** (`mensagem.conteudo`), não nas variáveis do
template. As variáveis enviadas ao canal são os quatro valores isolados, cada um sem quebra de
linha — é essa a razão de a validação recusar `\n` nos slots.

## 2. Agendamento na confirmação

`app/modulos/conversa/service.py`

```python
def agendar_boas_vindas(
    conexao,
    *,
    id_hotel: int,
    id_reserva: int,
    nome_completo: str,
    repositorio=...,
    repositorio_propriedade=...,
    enfileirar=...,
) -> str: ...
```

Devolve `"agendada"`, `"nao_enviada_slot_ausente"` ou `"ja_agendada"`.

**Sequência:**

1. Lê as três chaves com `id_hotel`. Falta ou valor inválido → log
   `boas_vindas_bloqueadas motivo=slot_invalido chave=<chave>` e retorna
   `nao_enviada_slot_ausente`. **Nada é gravado.**
2. Monta o texto e insere a mensagem pendente (reusa
   `inserir_mensagem_enviada_pendente`).
3. Insere o trabalho dentro de `conexao.begin_nested()`. `IntegrityError` do índice único →
   volta o savepoint, log `boas_vindas_ja_agendadas`, retorna `ja_agendada`.
4. Log `boas_vindas_agendadas id_reserva id_mensagem id_hotel` e retorna `agendada`.

**A confirmação da chegada nunca falha por causa deste passo.** O savepoint existe para que a
violação do índice não aborte a transação que já gravou o check-in.

## 3. Fila de trabalho

`app/fila/repository.py` e `app/fila/service.py`

```python
def enfileirar_enviar_boas_vindas(
    conexao, *, id_hotel: int, id_reserva: int, id_mensagem: int
) -> int: ...
```

| Item | Valor |
| --- | --- |
| `tipo` | `enviar_boas_vindas` |
| `payload` | `{"id_reserva": ..., "id_mensagem": ...}` |
| Unicidade | `uq_trabalho_enviar_boas_vindas_reserva` (índice parcial por reserva) |
| Retentativa | `registrar_falha_de_envio` já existente: backoff e teto de `tentativas_max_envio_mensagem` |

Nenhuma função nova de retentativa, nenhum parâmetro novo de prazo.

## 4. Consumo no worker

`app/modulos/conversa/service.py`

```python
def processar_trabalho_enviar_boas_vindas(
    conexao, *, trabalho: dict, gateway: MensageriaGateway, repositorio=...
) -> None: ...
```

`worker/consumidor.py` ganha o ramo `tipo == "enviar_boas_vindas"`. Comportamento igual aos
outros envios: mensagem ausente → `falha` técnica; telefone ausente → `falha`; `FalhaDeEnvio`
→ reagenda ou marca falha conforme o teto; sucesso → `mensagem.status_envio = 'enviada'` com
`enviada_em` e `id_externo`, e `trabalho` concluído.

Diferença única: antes de chamar o gateway, lê os três slots com o `id_hotel` do trabalho e
monta a tupla de variáveis. Slot inválido no momento do envio (cenário de valor entrado fora
da rota) → `falha` com código `slot_invalido`, e a mensagem fica `falha`. O check-in permanece.

## 5. Porta de mensageria

`app/portas/mensageria.py`

```python
class MensageriaGateway(Protocol):
    def enviar_boas_vindas(
        self,
        *,
        telefone_destino: str,
        variaveis: tuple[str, str, str, str],
        corpo: str,
        id_mensagem: int,
        id_reserva: int,
    ) -> ResultadoEnvio: ...
```

`variaveis` é ordenada: `(prenome, cafe, wifi, checkout)`. `corpo` é o texto do histórico,
usado pelo falso e ignorado pelo adaptador real (o canal envia template, não texto livre).

| Implementação | Comportamento |
| --- | --- |
| `MensageriaFalsa` | Registra `{"tipo": "boas_vindas", ...}` em `self.envios`; respeita `falhar_sempre` e `falhas_restantes` |
| `MensageriaWhatsapp` | Template `boas_vindas`, quatro parâmetros de corpo na ordem da tupla. Não exercitado pela suíte |

Nenhum teste desta fatia chama `MensageriaWhatsapp`.

## 6. Log — o que é permitido registrar

| Evento | Campos |
| --- | --- |
| `chegada_confirmada` | `id_reserva`, `id_hotel` |
| `chegada_recusada` | `id_reserva`, `id_hotel`, `status` atual |
| `boas_vindas_agendadas` | `id_reserva`, `id_mensagem`, `id_hotel` |
| `boas_vindas_bloqueadas` | `id_reserva`, `id_hotel`, `chave` do slot |
| `boas_vindas_ja_agendadas` | `id_reserva`, `id_hotel` |
| `boas_vindas_enviadas` | `id_mensagem`, `id_externo` |
| `boas_vindas_recuperadas` | `id_reserva`, `id_hotel` |

**Nunca** aparecem em log: conteúdo da mensagem, valor de slot, nome do hóspede, telefone. O
nome da chave é identificador de configuração, não texto ao hóspede — é o que permite à
recepção saber *qual* campo preencher sem vazar conteúdo.
