# Quickstart — validar a entrega de Confirmar Chegada e Boas-vindas

Roteiro manual além da suíte. Contratos em [contracts/](./contracts/).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. A revisão `0008_confirmar_chegada` precisa estar aplicada:

```powershell
alembic current
```

Hotel e usuários como nos quickstarts anteriores (recepção, gestão, operação). API no ar.
Worker acionado manualmente nos cenários que enviam.

Uma reserva elegível exige estado de origem válido. Caminho mais curto: criar a reserva
(F1.1), deixar a ficha chegar (F1.3) ou rodar a varredura de silêncio (F1.4) para marcar
`sem_cadastro_previo`.

---

## Cenário 1 — Slots e prazo semeados na instalação

```powershell
curl.exe -s -b cookies-recepcao.txt http://127.0.0.1:8000/propriedade/boas-vindas
```

**Esperado**: `200` com `cafe`, `wifi` e `checkout` preenchidos (nenhum `null`, nenhum vazio).
É o que garante que a primeira confirmação não depende de alguém ter cadastrado.

O prazo da janela de recuperação não aparece nessa rota (não é texto de balcão). Confira no
banco:

```sql
SELECT valor FROM parametro_hotel WHERE chave = 'horas_validade_boas_vindas';
```

**Esperado**: `12`.

---

## Cenário 2 — Recepção grava; validação recusa na hora

```powershell
curl.exe -s -b cookies-recepcao.txt -H "Content-Type: application/json" -X PUT -d "{\"cafe\":\"Cafe das 7h as 10h30\",\"wifi\":\"Rede Hotel-Hospedes, senha 12345678\",\"checkout\":\"Ate as 12h\"}" http://127.0.0.1:8000/propriedade/boas-vindas
```

**Esperado**: `200` com os três valores.

Agora as recusas, uma por vez — em todas, `422` e os valores anteriores intactos no `GET`:

| Valor enviado em qualquer campo | Motivo |
| --- | --- |
| `""` ou `"   "` | Vazio |
| `"Cafe\nda manha"` | Quebra de linha |
| `"Cafe\tda manha"` | Tabulação |
| `"Cafe        7h"` | Mais de quatro espaços seguidos |

```powershell
curl.exe -s -o NUL -w "%{http_code}" -b cookies-recepcao.txt -H "Content-Type: application/json" -X PUT -d "{\"cafe\":\"   \",\"wifi\":\"ok\",\"checkout\":\"ok\"}" http://127.0.0.1:8000/propriedade/boas-vindas
```

Confirme com o `GET` que **nenhum** dos três mudou — a gravação é atômica.

---

## Cenário 3 — Gestão lê, não grava; operação recusada

Cookie de gestão: `GET` → `200`; `PUT` → `403`.
Cookie de `staff`: `GET` e `PUT` → `403`.

---

## Cenário 4 — Confirmar a chegada

```powershell
curl.exe -s -b cookies-recepcao.txt -X POST http://127.0.0.1:8000/reservas/1/chegada
```

**Esperado**: `200`, `status: "hospedado"`, `checkin_em` com o instante de agora (não a data
prevista), `boas_vindas: "agendada"`.

No banco:

```sql
SELECT status, checkin_em FROM reserva WHERE id_reserva = 1;
SELECT tipo, status, payload FROM trabalho WHERE tipo = 'enviar_boas_vindas';
SELECT direcao, status_envio FROM mensagem WHERE id_reserva = 1 ORDER BY id_mensagem;
```

Uma linha de trabalho `pendente` e uma mensagem `enviada`/`pendente`.

---

## Cenário 5 — Recusas de estado

Repita o `POST` na mesma reserva: **`409`**, `checkin_em` inalterado, e **nenhum** segundo
trabalho.

Com uma reserva ainda em `aguardando_cadastro`: `409`.
Com uma reserva `cancelada` ou `encerrado`: `409`.

Em todos os casos, confira que `trabalho` e `mensagem` não cresceram.

---

## Cenário 6 — Worker entrega

```powershell
python -m worker --uma-passagem
```

**Esperado**: log `boas_vindas_enviadas`, `mensagem.status_envio = 'enviada'` com
`enviada_em` e `id_externo`, `trabalho.status = 'concluido'`. O gateway falso registra o
envio; nenhuma chamada ao provedor real.

Confira o corpo gravado:

```sql
SELECT conteudo FROM mensagem WHERE id_reserva = 1 AND direcao = 'enviada';
```

Deve conter a confirmação da chegada, os três fatos com rótulo fixo, o convite final — e
**nenhum** item de catálogo, nenhuma oferta.

---

## Cenário 7 — Slot ausente: check-in ocorre, recado não sai

Apague um slot direto no banco (é o caminho que a rota impede, e por isso o teste manual usa
SQL):

```sql
DELETE FROM parametro_hotel WHERE chave = 'boas_vindas_wifi';
```

Confirme a chegada de outra reserva elegível.

**Esperado**: `200` com `boas_vindas: "nao_enviada_slot_ausente"`; `status = 'hospedado'` e
`checkin_em` gravados; **zero** trabalhos e zero mensagens novas; log
`boas_vindas_bloqueadas ... chave=boas_vindas_wifi` sem nenhum texto.

```powershell
curl.exe -s -b cookies-recepcao.txt http://127.0.0.1:8000/fila-do-dia
```

Aquela reserva vem com `boas_vindas_nao_enviadas: true` e `chegada_nao_confirmada: false`.

---

## Cenário 8 — Recuperação, e o limite de validade

Restaure o slot pelo `PUT` do cenário 2. Prepare uma segunda reserva `hospedado` sem
boas-vindas cujo check-in seja antigo:

```sql
UPDATE reserva SET checkin_em = now() - INTERVAL '3 days' WHERE id_reserva = <antiga>;
```

```powershell
python -m worker --verificar-boas-vindas
python -m worker --uma-passagem
```

**Esperado**: a reserva com check-in recente recebe exatamente um recado e passa a
`boas_vindas_nao_enviadas: false`. A de três dias atrás **não** recebe nada e continua
sinalizada.

Rode `--verificar-boas-vindas` de novo: nenhum segundo recado nasce.

---

## Cenário 9 — A virada de dia não engole ninguém

Este é o caso que a janela por data de calendário perderia em silêncio. Simule a chegada de
23h30 de "ontem", já com o dia civil virado:

```sql
UPDATE reserva
   SET data_checkin_prevista = CURRENT_DATE - 1,
       checkin_em = now() - INTERVAL '35 minutes'
 WHERE id_reserva = <recente>;
DELETE FROM trabalho WHERE tipo = 'enviar_boas_vindas'
   AND (payload->>'id_reserva')::bigint = <recente>;
```

```powershell
python -m worker --verificar-boas-vindas
python -m worker --uma-passagem
```

**Esperado**: a reserva recebe o recado, mesmo com `data_checkin_prevista` no passado. A janela
conta do `checkin_em`.

Agora o oposto — data prevista de hoje, check-in velho:

```sql
UPDATE reserva
   SET data_checkin_prevista = CURRENT_DATE,
       checkin_em = now() - INTERVAL '13 hours'
 WHERE id_reserva = <outra>;
```

**Esperado**: nenhum envio. O par de casos prova que o critério é o instante, não o calendário.

Para conferir que o prazo não está cravado no código:

```sql
UPDATE parametro_hotel SET valor = '1' WHERE chave = 'horas_validade_boas_vindas';
```

Com a janela de uma hora, a reserva de 35 minutos continua elegível e a de 13 horas segue fora.
Apagando a chave, o hotel inteiro deixa de receber recuperação e o log registra
`prazo_ausente` — nunca um prazo suposto.

---

## Cenário 10 — Isolamento e perfis

Com cookie de recepção do hotel B, `POST /reservas/<id do hotel A>/chegada` → `404` (não
`403`, não `409`): a resposta não revela que a reserva existe.

Com cookie de gestão e com cookie de `staff` no próprio hotel: `403`.

Em todos, o status da reserva permanece.

---

## Cenário 11 — Unicidade sob concorrência

```sql
INSERT INTO trabalho (id_hotel, tipo, payload, status)
VALUES (1, 'enviar_boas_vindas', '{"id_reserva": 1, "id_mensagem": 99}', 'pendente');
```

**Esperado**: violação de `uq_trabalho_enviar_boas_vindas_reserva`. A garantia é do banco, não
do código.

---

## Suíte

```powershell
pytest testes/unitarios -q
pytest testes/integracao/test_confirmar_chegada.py -q
pytest testes/integracao/test_boas_vindas_slots.py -q
pytest testes/integracao/test_boas_vindas_envio.py -q
pytest testes/integracao/test_garantias_do_banco.py -q
```

Unitários: validação dos slots, montagem do texto (fatos, convite único, sem oferta, sem
catálogo), política das duas operações novas, log sem conteúdo, elegibilidade da recuperação.
Integração: transições aceitas e recusadas, `409` versus `404`, perfis, isolamento, fila do
dia com as duas sinalizações, envio e falha pelo gateway falso, unicidade concorrente.
