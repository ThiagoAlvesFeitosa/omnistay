# Modelo de Dados — F2.2 Confirmar Chegada e Boas-vindas

Nenhuma tabela nova. Nenhuma coluna nova. O que muda é uma restrição, um índice, uma visão e
três linhas de configuração por propriedade.

---

## 1. `reserva` — sem alteração de esquema

Colunas usadas nesta fatia:

| Coluna | Papel nesta fatia |
| --- | --- |
| `status` | `hospedado` é o estado destino |
| `checkin_em` | `TIMESTAMPTZ` já existente. Recebe `now()` na confirmação e **é o eixo da janela de recuperação** |
| `data_checkin_prevista` | Só apoia a fila do dia. **Não** define elegibilidade de envio |
| `telefone_contato` | Destino do recado |
| `id_hotel` | Filtro obrigatório em toda operação |

### Transições relevantes

A trigger `tg_valida_transicao_reserva` já vigente admite para `hospedado` **apenas**:

```text
ficha_recebida      → hospedado
ficha_parcial       → hospedado
sem_cadastro_previo → hospedado
```

Logo, são recusados por construção: `aguardando_cadastro → hospedado`,
`cancelada → hospedado`, `encerrado → hospedado`, e `hospedado → hospedado` (a trigger
retorna sem erro quando o status não muda, mas o `UPDATE` da aplicação já não alcança a linha).

### Regra de escrita

```sql
UPDATE reserva
   SET status = 'hospedado', checkin_em = now()
 WHERE id_reserva = :id_reserva
   AND id_hotel   = :id_hotel
   AND status IN ('ficha_recebida', 'ficha_parcial', 'sem_cadastro_previo')
```

`rowcount = 1` → confirmação aceita. `rowcount = 0` → recusada, e a distinção entre "não
existe / é de outro hotel" (`404`) e "estado não admite" (`409`) vem de uma leitura prévia da
reserva **no hotel da sessão**. Duas confirmações concorrentes: a segunda encontra
`rowcount = 0` e é recusada — o estado já não é de origem válida.

`checkin_em` não é sobrescrito em confirmação repetida, porque o `UPDATE` não alcança reserva
já `hospedado`.

## 2. `parametro_hotel` — quatro chaves novas

Esquema inalterado (`valor VARCHAR(255) NOT NULL`, `UNIQUE (id_hotel, chave)`).

| Chave | Conteúdo | Origem |
| --- | --- | --- |
| `boas_vindas_cafe` | Informação de café da manhã, uma linha | Semeada na instalação, editada pela recepção |
| `boas_vindas_wifi` | Informação de wi-fi, uma linha | idem |
| `boas_vindas_checkout` | Informação de horário de saída, uma linha | idem |
| `horas_validade_boas_vindas` | Duração da janela de recuperação, em horas. Padrão `12` | Semeada na instalação; **não** editável pela recepção |

As três primeiras são texto que vai ao hóspede e seguem a validação do canal abaixo. A quarta é
prazo: validada como inteiro positivo, no formato de `horas_ate_reenvio`, e fora do alcance da
permissão da recepção — é parâmetro de comportamento, não texto de balcão.

### Validação (aplicada na gravação)

| Regra | Recusa | Motivo |
| --- | --- | --- |
| Vazio ou só espaços após `strip` | Sim | Variável vazia é recusada pelo canal |
| Contém `\n` ou `\r` | Sim | Parâmetro de template não aceita quebra de linha |
| Contém `\t` | Sim | Não aceita tabulação |
| Contém 5 ou mais espaços seguidos | Sim | O limite do canal é 4 consecutivos |
| Mais de 255 caracteres | Sim | Limite da coluna; recusa antes do banco, com mensagem legível |

O valor gravado é o texto após `strip`. A mesma função pura é reusada na montagem do recado
como verificação defensiva — valor entrado por SQL direto ou semeadura malfeita não vira
mensagem, vira omissão sinalizada.

### Escrita

`INSERT INTO parametro_hotel (id_hotel, chave, valor) VALUES (...)
ON CONFLICT (id_hotel, chave) DO UPDATE SET valor = EXCLUDED.valor, atualizado_em = now()`.
Os três valores são gravados na mesma transação: ou os três passam, ou nenhum muda.

### Semeadura

Bootstrap (propriedade nova) e revisão `0008` (propriedades existentes, idempotente pelo
padrão `WHERE NOT EXISTS` da `0007`). As quatro chaves.

### Consulta de elegibilidade da recuperação

```sql
SELECT r.id_reserva, r.id_hotel, r.checkin_em, h.nome_completo
  FROM reserva r
  JOIN reserva_hospede rh ON rh.id_reserva = r.id_reserva AND rh.titular
  JOIN hospede h ON h.id_hospede = rh.id_hospede
 WHERE r.status = 'hospedado'
   AND r.checkin_em IS NOT NULL
   AND NOT EXISTS (
         SELECT 1 FROM trabalho t
          WHERE t.tipo = 'enviar_boas_vindas'
            AND (t.payload->>'id_reserva')::bigint = r.id_reserva
       )
 ORDER BY r.id_reserva ASC
```

A **janela não entra neste SQL**: o prazo é por propriedade, e a comparação
`checkin_em >= agora - horas_validade_boas_vindas` acontece em Python, com cache de prazo por
hotel — o mesmo desenho de `verificar_cadastros_pendentes`. `checkin_em IS NOT NULL` impede que
uma linha inconsistente (`hospedado` sem instante, alcançável só por escrita direta) seja
tratada como chegada recente.

**O eixo é o instante, não o calendário.** `data_checkin_prevista` não aparece aqui: medir por
data faria a chegada das 23h30 sair da elegibilidade às 00h00, e o pacote nunca sairia, sem erro
nenhum.

## 3. `trabalho` — tipo novo e unicidade

```sql
ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho
    ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN ('enviar_coleta', 'interpretar_ficha', 'enviar_lembrete',
                    'enviar_boas_vindas'));

CREATE UNIQUE INDEX uq_trabalho_enviar_boas_vindas_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_boas_vindas';
```

**Este índice é a garantia de FR-008.** Não há verificação prévia em código: a segunda
inserção para a mesma reserva viola o índice, independentemente de quantas execuções
concorrentes tentem.

| Campo | Valor |
| --- | --- |
| `tipo` | `enviar_boas_vindas` |
| `payload` | `{"id_reserva": <int>, "id_mensagem": <int>}` — só identificadores |
| `status` | `pendente` → `processando` → `concluido` \| `falha` (já existente) |

O `payload` **não** carrega o texto dos slots: a fonte de verdade é `parametro_hotel`.

## 4. `mensagem` — sem alteração de esquema

O recado nasce como `direcao='enviada'`, `status_envio='pendente'`, `conteudo` com o texto
montado. O worker atualiza para `enviada` (com `enviada_em` e `id_externo`) ou `falha`,
usando as funções já existentes. Isso atende FR-016 sem campo novo.

## 5. `vw_fila_do_dia` — coluna derivada nova

Recriada na `0008` com todas as colunas da `0007` mais:

```sql
(r.status = 'hospedado'
 AND NOT EXISTS (
       SELECT 1 FROM trabalho t
        WHERE t.tipo = 'enviar_boas_vindas'
          AND (t.payload->>'id_reserva')::bigint = r.id_reserva
     )) AS boas_vindas_nao_enviadas
```

| Coluna | Significado | Exclusividade |
| --- | --- | --- |
| `chegada_nao_confirmada` | Entrada prevista venceu e `status <> 'hospedado'` | Exige **não** hospedado |
| `boas_vindas_nao_enviadas` | Está `hospedado` e nenhum recado foi registrado | Exige hospedado |

As duas nunca são verdadeiras ao mesmo tempo — é assim que FR-030 obtém indicação
distinguível. O `NOT EXISTS` usa o índice único parcial criado na mesma revisão.

Cláusulas mantidas: `status NOT IN ('encerrado','cancelada')` e
`data_checkin_prevista <= CURRENT_DATE`. Consequência aproveitada: reserva `hospedado` de dia
anterior continua na visão, então a sinalização de FR-032 persiste sem trabalho extra;
reserva encerrada sai da visão, como a spec descreve.

Consequência assumida: reserva com **chegada antecipada** (check-in confirmado antes da data
prevista) é elegível ao envio, mas ainda não aparece na visão. Se o slot estiver vazio nesse
caso, a sinalização só se torna visível quando a data prevista alcança o dia corrente. Alargar
a cláusula da visão afetaria a fila do turno inteira e não é escopo desta fatia.

## 6. Entidades da spec e onde cada uma mora

| Entidade da spec | Onde vive |
| --- | --- |
| Reserva | `reserva` |
| Momento real de entrada | `reserva.checkin_em` |
| Pacote de boas-vindas | `mensagem` (`direcao='enviada'`) |
| Pendência de envio | `trabalho` (`tipo='enviar_boas_vindas'`) |
| Slots de entrada | `parametro_hotel` (três chaves) |
| Chegada não confirmada | `vw_fila_do_dia.chegada_nao_confirmada` |
| Boas-vindas não enviadas | `vw_fila_do_dia.boas_vindas_nao_enviadas` |
| Catálogo ativo | `catalogo_item` — **não lido nesta fatia** |

## 7. Revisão Alembic

`0008_confirmar_chegada`, `down_revision = "0007_controlar_silencio"`. Aplica
`sql/0008_confirmar_chegada.sql` e traz `downgrade()` explícito (remove o índice, restaura o
`CHECK` sem `enviar_boas_vindas`, recria a visão da `0007`), no mesmo formato da `0007`.

`docs/04-schema.sql` recebe o mesmo delta na mesma tarefa — banco e documento divergentes é
pior do que documento inexistente.
