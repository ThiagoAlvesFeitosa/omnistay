# Contrato — montagem do recado e porta de mensageria

---

## 1. Função pura

`app/modulos/conversa/texto_boas_vindas.py`

```python
def montar_texto_boas_vindas(
    *, nome_completo: str, cafe: str, wifi: str, checkout: str, convite: str
) -> str: ...
```

Sem I/O. Valores já validados. Sem parâmetros `aviso`, `tom`,
`personalidade`, `catalogo`.

**Estrutura obrigatória**, nesta ordem:

```text
Ola, {prenome}! Sua chegada esta confirmada, seja bem-vindo.
Cafe da manha: {cafe}
Wi-Fi: {wifi}
Checkout: {checkout}
O atendimento inicial e feito por uma assistente virtual. Uma pessoa da recepcao assume quando necessario.
{convite}
```

| Exigência | Verificação |
| --- | --- |
| Confirma a chegada | Texto contém a confirmação |
| Três fatos com rótulo fixo | `Cafe da manha:`, `Wi-Fi:`, `Checkout:` |
| Aviso intacto, imediatamente antes do convite | Constante de produto; sem parâmetro |
| Última linha = `convite` | Igualdade literal, sem rótulo `Convite:` |
| Frase antiga ausente | Não contém `Quer saber mais alguma coisa da sua estadia?` |
| Sem `?` obrigatório | A casa pode ou não interrogar |
| Sem catálogo, sem oferta, só o primeiro nome | Como na F2.2 |

A constante `AVISO_ASSISTENTE_VIRTUAL` **não muda**.

---

## 2. Agendamento

`CHAVES_SLOTS_BOAS_VINDAS` em `conversa/service.py` **e** o dict homônimo
em `propriedade/service.py` incluem `("convite", "boas_vindas_convite")`.

`agendar_boas_vindas` lê as quatro chaves. Qualquer uma ausente ou
inválida → log `boas_vindas_bloqueadas motivo=slot_invalido chave=<chave>`
(a chave, **não** o valor) e `"nao_enviada_slot_ausente"`. Nada gravado.

Os quatro válidos → monta com `convite=`, insere mensagem, enfileira.
`IntegrityError` → `"ja_agendada"`. Check-in nunca é desfeito.

---

## 3. Porta

```python
def enviar_boas_vindas(
    self,
    *,
    telefone_destino: str,
    variaveis: tuple[str, str, str, str, str],
    corpo: str,
    id_mensagem: int,
    id_reserva: int,
) -> ResultadoEnvio: ...
```

`variaveis` ordenada: `(prenome, cafe, wifi, checkout, convite)`.
`corpo` é o texto do histórico (simulador e `mensagem.conteudo`).
O adaptador WhatsApp **descarta** o `corpo` e manda o template.

`MensageriaFalsa` registra `convite` no dict do envio, além da tupla.

---

## 4. Template Meta `boas_vindas` (cinco parâmetros)

O POST para a Graph leva `template.name = "boas_vindas"` e cinco
parâmetros de corpo, na ordem da tupla. O operador submete na Meta:

```text
Ola, {{1}}! Sua chegada esta confirmada, seja bem-vindo.
Cafe da manha: {{2}}
Wi-Fi: {{3}}
Checkout: {{4}}
O atendimento inicial e feito por uma assistente virtual. Uma pessoa da recepcao assume quando necessario.
{{5}}
```

Texto congelado (saudação, rótulos, aviso) **não** viaja no JSON.
Unitário com `httpx.MockTransport`: o payload tem cinco
`{"type":"text","text":...}` na ordem; **nenhuma** chamada de rede.

Até a Meta aprovar esse corpo, o Graph recusa (contagem). Isso é
`FalhaDeEnvio`, não recado com a frase antiga.

---

## 5. Recuperação

`--verificar-boas-vindas` intocado. Completar o convite (com os outros
três já válidos) na janela de `checkin_em` dispara exatamente um recado
já com a linha da casa, porque `agendar_boas_vindas` passou a exigir os
quatro. Fora da janela: nenhum envio automático.
