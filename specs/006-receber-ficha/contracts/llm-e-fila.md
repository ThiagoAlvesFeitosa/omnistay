# Contrato: LLM e fila de interpretação

Modelo: [data-model.md](../data-model.md). Entrada: [webhook-e-entrada.md](./webhook-e-entrada.md).

---

## Porta `LLMProvider`

Interface mínima desta fatia (nomes exatos na implementação):

```text
extrair_ficha(texto) -> ResultadoExtracao
```

`ResultadoExtracao` carrega:

- mapa de campos opcionais (os nove da ficha; **sem idade**)
- desfecho sugerido: `completa` | `parcial` | `irreconhecivel`
- ou erro/indisponibilidade que o worker traduz em `falha_extrator`

Regras:

- Domínio e worker dependem só da porta.
- Testes usam implementação falsa com desfechos configuráveis.
- Nenhum teste chama rede de provedor de IA.
- Conteúdo do texto **não** é logado ao redor da chamada — só ids de mensagem/trabalho e
  código de desfecho.

Validação de formato (data, tipo de documento, etc.) pode ocorrer **depois** da porta, em
funções puras do módulo `conversa`, antes de pedir consolidação a `hospedagem`.

---

## Trabalho `interpretar_ficha`

| Campo | Valor |
| --- | --- |
| `tipo` | `interpretar_ficha` |
| `payload` | `id_reserva`, `id_mensagem`, `id_evento` |
| Claim | Mesmo mecanismo `FOR UPDATE SKIP LOCKED` da F1.2 |
| Sucesso | `status = concluido` após gravação de `classificacao_bruta` e consolidação (quando couber) |
| Falha transitória do LLM | Reagenda com backoff; mensagem permanece; sem descarte |
| Após esgotar tentativas | Marca trabalho em `falha`; grava desfecho `falha_extrator` na mensagem; sinaliza `leitura_humana`; **não** apaga mensagem |

### Unicidade

No máximo um `interpretar_ficha` por `id_mensagem` (índice único parcial).

### Proibições

- Enfileirar `enviar_coleta` ou qualquer envio ao hóspede como reação a parcial/irreconhecível
- Consolidar duas vezes a mesma mensagem por retry bem-sucedido (segundo claim encontra
  trabalho já `concluido` ou desfecho já gravado)

---

## Orquestração no worker

```text
claim interpretar_ficha
  → conversa: ler mensagem, chamar LLMProvider, validar campos, gravar classificacao_bruta
  → se completa/parcial: hospedagem.consolidar_ficha_titular(...)
  → se irreconhecivel/falha_extrator: não altera hospede/status (além do sinal na mensagem)
  → marcar trabalho concluido | reagendar | falha
```

`MensageriaGateway` **não** participa deste tipo de trabalho.
