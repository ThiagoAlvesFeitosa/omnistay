# Contrato — fila, worker e roteamento da resposta

## Tipos novos em `trabalho`

Incluídos no `CHECK` e na allowlist de `reclamar_proximo` **na mesma
revisão** (`0017`). Consumir um tipo que o CHECK ainda não aceita, ou
aceitar no CHECK sem consumir, quebra o padrão das F3.1–F3.8.

| Tipo | Unicidade | Quem enfileira | Quem processa |
| --- | --- | --- | --- |
| `enviar_pesquisa_saida` | parcial por `id_reserva` | `hospedagem.confirmar_saida` → `conversa.agendar_pesquisa_saida` | `conversa.processar_trabalho_enviar_pesquisa_saida` |
| `interpretar_pesquisa_saida` | parcial por `id_mensagem` | webhook, ramo pesquisa | `conversa.processar_trabalho_interpretar_pesquisa_saida` |

`--uma-passagem` consome os tipos novos (são fila, não calendário). Nenhuma
flag nova no agendador.

Payload sem dado pessoal: só identificadores.

## Envio

Processador lê telefone da reserva, chama
`MensageriaGateway.enviar_pesquisa_saida`, espelha `status_envio`. Falha
(`FalhaDeEnvio`): reagenda o mesmo id; **não** reabre `encerrado`. Sucesso:
`concluido`. Índice impede segundo trabalho distinto.

## Webhook (`receber_evento_entrada`) — ordem

Depois de gravar o evento (idempotência `id_externo` inalterada):

1. Reserva `aguardando_cadastro` no telefone → `interpretar_ficha`
2. Reserva `hospedado` → `classificar_mensagem`
3. Reserva `encerrado` **e** existe `enviar_pesquisa_saida` **e** pesquisa
   incompleta **e** `agora - checkout_em` ≤ prazo da propriedade →
   `interpretar_pesquisa_saida`
4. Reserva `encerrado` mais recente no telefone, fora de (3) → INSERT da
   mensagem, **zero** trabalho, desfecho `fora_da_janela` se quiser
   auditoria, sem humano na fila
5. Senão → `sem_reserva` como hoje (evento fica; sem mensagem de reserva)

Passo 3 com prazo ausente/inválido: ainda enfileira a interpretação; o
**worker** recusa atribuir, loga `prazo_ausente`, marca desfecho
`prazo_ausente`, sinaliza humano, conclui o trabalho. Não inventa 24.

Reenvio do mesmo `id_externo`: `duplicado`, zero segundo trabalho.

## Worker de interpretação

1. Relê prazo e `checkout_em`. Fora da janela: conclui sem chamar a porta;
   não grava nota nem consentimento; **não** sinaliza humano (a atribuição
   simplesmente expirou — o clique esquecido já teve o destaque de vencida).
2. Chama `LLMProvider.interpretar_pesquisa_saida`.
3. Domínio valida nota ∈ [1, 5].
4. Nota válida → `feedback.gravar_avaliacao_checkout` (INSERT ou completa
   comentário da linha existente).
5. `aceite` booleano → `hospedagem.registrar_consentimento_pesquisa`
   (`origem=pesquisa_checkout`, titular). INSERT; unique não se aplica
   (histórico).
6. Irreconhecível / porta caída / formato inválido: preserva mensagem,
   desfecho correspondente, `pesquisa_saida_leitura_humana`, trabalho
   `concluido`. Zero nota inventada, zero consentimento inventado.
7. Parcial reconhecido: grava o que deu; **não** manda segunda pesquisa;
   **não** lembra.

`conversa` não faz SQL em `avaliacao` nem em `consentimento`.

## Allowlist

Os testes da F3.1 que listam tipos consumíveis são **estendidos**, não
revertidos: os dois tipos novos passam a ser reclamáveis. Tipos de estadia
continuam como estão. Encerrada **não** gera `classificar_mensagem`.
