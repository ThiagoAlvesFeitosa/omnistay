# Contrato: porta MensageriaGateway e consumo da fila

Contrato interno (domínio ↔ adaptadores ↔ worker). Não é rota HTTP.

---

## `MensageriaGateway`

Porta em `app/portas/`. O domínio e o worker dependem **só** desta interface.

### Operação: enviar coleta

Entrada tipada (nomes ilustrativos; o plano de tasks fixa a assinatura Python):

| Campo | Semântica |
| --- | --- |
| `telefone_destino` | Canônico `55…` |
| `primeiro_nome` | Único dado pessoal permitido no template/corpo |
| `corpo` ou `template` + variáveis | Texto já montado **ou** identificador Utility + variáveis — o adaptador decide o que a Meta exige; a porta falsa grava o corpo observável |
| `id_mensagem` / `id_reserva` | Só para correlação de resultado; **não** logar PII |

Saída:

| Resultado | Efeito esperado no worker |
| --- | --- |
| Sucesso (+ `id_externo` opcional) | `mensagem.status_envio = enviada` |
| Falha (erro tipado, sem corpo de mensagem) | Incrementa tentativas / backoff ou `falha` definitiva |

### Implementações

| Adaptador | Uso |
| --- | --- |
| Falsa | Toda a suíte; pode injetar falha determinística |
| WhatsApp Cloud | Ambiente com credenciais; template Utility; número de teste no MVP |

Nenhum teste automatizado instancia o adaptador real nem abre rede à Meta.

---

## Fila `trabalho`

### Enfileirar (`enviar_coleta`)

- Chamado dentro da transação de criação da reserva.
- Exige `id_hotel`, `id_reserva`, `id_mensagem`.
- Viola unicidade se já existir coleta para a reserva → falha a transação (não deve ocorrer
  no caminho feliz de um único `POST`).

### Claim

- Seleciona elegíveis (`pendente`, `proxima_tentativa_em` nulo ou vencido).
- `FOR UPDATE SKIP LOCKED`.
- Marca `processando` + `processando_desde`.

### Concluir / falhar / reagendar

- Concluir: `concluido`.
- Reagendar: `pendente` + `proxima_tentativa_em` + `tentativas` + `erro_ultima_tentativa`
  (sem PII).
- Falha definitiva: `falha` + espelhar `mensagem.status_envio = falha`.

### Reclaim

Trabalhos `processando` com `processando_desde` além do prazo de bloqueio voltam a
`pendente` antes ou durante o claim.

---

## Texto da mensagem de coleta (conteúdo observável)

O corpo gravado em `mensagem.conteudo` e o que a porta falsa “envia” MUST conter:

1. Saudação com **apenas** o primeiro nome
2. Lista numerada: nome completo; profissão; data de nascimento; tipo de documento; número
   do documento; endereço; CEP; cidade; telefone
3. Que o preenchimento antecipado é opcional e serve para evitar espera na chegada
4. Finalidade da coleta
5. Contato do responsável pelos dados (`parametro_hotel.contato_responsavel_dados`)

MUST NOT conter telefone do hóspede, documento, endereço nem sobrenome completo além do que
o primeiro nome já expõe (o nome completo entra só como **rótulo do item 1 da lista**, não
como dado já preenchido do titular).
