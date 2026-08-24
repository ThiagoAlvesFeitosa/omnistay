# Contrato: anonimização e exclusão

O que a passagem escreve nas tabelas operacionais. Constantes em
`app/comum/retencao.py`. SQL só no módulo dono da tabela.

---

## Marcas

| Constante | Valor | Uso |
| --- | --- | --- |
| `MARCA_TEXTO` | `[anonimizado]` | `mensagem.conteudo`, `solicitacao.descricao`, `avaliacao.comentario` |
| `MARCA_PAYLOAD` | `{"anonimizado": true}` | `evento_webhook.payload` |
| `MARCA_TELEFONE` | `anonimizado` | `reserva.telefone_contato` após a última ficha da reserva sair |

`classificacao_bruta` não ganha marca: vira `NULL` (retirar o eco do
texto). Eixos estruturados permanecem.

---

## Conteúdo livre (prazo em meses)

Reserva do hotel com `checkout_em IS NOT NULL` e
`checkout_em + make_interval(months => N) <= agora`.

| UPDATE | Condição extra | Conta no comprovante |
| --- | --- | --- |
| `mensagem.conteudo = MARCA_TEXTO`, `classificacao_bruta = NULL` | `conteudo IS DISTINCT FROM MARCA_TEXTO` (ambas as direções) | `mensagens_anonimizadas` = linhas desse UPDATE |
| `evento_webhook.payload = MARCA_PAYLOAD` | `id_externo` igual ao de uma `mensagem` da reserva elegível **e** payload distinto da marca | `payloads_anonimizados` |
| `solicitacao.descricao = MARCA_TEXTO` | `btrim(descricao) <> ''` e descrição distinta da marca | `descricoes_anonimizadas` |
| `avaliacao.comentario = MARCA_TEXTO` | comentário `IS NOT NULL` e `btrim(comentario) <> ''` e distinto da marca | `comentarios_anonimizados` |

Linha **não** é apagada. Status de chamado **não** muda. Nota **não**
vira nula. Comentário que já era vazio **não** recebe marca.

Segunda passagem: os `WHERE` devolvem 0 linhas; comprovante do **outro
dia** registra zeros nesses tipos.

---

## Ficha (prazo em anos)

Hóspede visível neste hotel (existe `reserva_hospede` → `reserva` com
`id_hotel` da passagem) **e**, considerando **todas** as reservas
vinculadas a ele:

- nenhuma tem `checkout_em` nulo;
- `MAX(checkout_em) + make_interval(years => A) <= agora`.

Ordem, por hóspede elegível:

1. DELETE `consentimento`
2. DELETE `reserva_hospede`
3. DELETE `hospede`
4. Se a reserva ficou sem nenhum vínculo: `telefone_contato = MARCA_TELEFONE`

`fichas_apagadas` = quantos `hospede` foram excluídos.

Reserva permanece. Mensagens/solicitações já anonimizadas (ou ainda
dentro dos doze meses — não se mistura o relógio) permanecem.

---

## Isolamento

Todo UPDATE/DELETE de conteúdo livre junta `reserva.id_hotel`. Exclusão
de ficha só é disparada na passagem do hotel que tem vínculo, mas a
elegibilidade olha a última saída em **qualquer** hotel daquela ficha —
para não apagar quem ainda tem estadia recente noutro.

Hotel B nunca tem linha de `mensagem`/`solicitacao`/`avaliacao` do hotel
A alterada.

---

## O que esta passagem não toca

- `usuario`, `sessao`, `catalogo_item`, `concorrente`, `coleta_mercado`
- `trabalho.payload` (já só identificadores, pelo comentário do esquema)
- `consumo.descricao_item`, `solicitacao.numero_quarto`, `solicitacao.janela_preferencia`
- Payload de webhook cujo `id_externo` não casa com nenhuma mensagem
