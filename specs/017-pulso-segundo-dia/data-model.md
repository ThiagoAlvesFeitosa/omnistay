# Modelo de dados — F3.8 Pulso do Segundo Dia

Nenhuma tabela nova. `avaliacao` já existe na `0001` e passa a ter o primeiro
escritor. Revisão `0016_pulso_segundo_dia`.

---

## Entidades

### Avaliação de pulso (`avaliacao`)

| Campo | Uso nesta fatia |
| --- | --- |
| `id_reserva` | Estadia que recebeu o pulso |
| `origem` | Sempre `pulso_segundo_dia` aqui (`checkout` é F4.1) |
| `nota` | Sempre nula nesta fatia (a pergunta não pede 1–5) |
| `comentario` | Texto da resposta do hóspede; nulo só se não houver corpo |
| `respondida_em` | Instante do encerramento |

`uq_avaliacao_reserva_origem` = no máximo um pulso respondido (ou desviado a
humano) por reserva. INSERT duplicado é recusado pelo banco.

Hotel chega por junção com `reserva` (Artigo XIV). Sem `id_hotel` na tabela.

### Trabalho `enviar_pulso`

| Campo | Valor |
| --- | --- |
| `tipo` | `enviar_pulso` |
| `payload` | `{id_reserva, id_mensagem}` |
| Unicidade | parcial por reserva — um pulso gravado |

Status: `pendente` → envio; `concluido` após sucesso **ou** após desistir porque
a janela fechou; `falha` / reagendar só enquanto ainda elegível.

### Trabalho `registrar_resposta_pulso`

| Campo | Valor |
| --- | --- |
| `tipo` | `registrar_resposta_pulso` |
| `payload` | `{id_reserva, id_mensagem}` |
| Unicidade | parcial por `id_mensagem` |

Só existe quando o pulso é dono do turno (intenção fora de dúvida / pedido /
reclamação técnica).

### Parâmetro `horas_minimas_para_pulso`

| | |
| --- | --- |
| Chave | `horas_minimas_para_pulso` |
| Valor semeado | `24` (inteiro ≥ 1) |
| Ausência / inválido | zero pulsos naquele hotel; log `prazo_ausente` |

Bootstrap e revisão `0016` (idempotente, padrão `0007`/`0008`).

### Reclamação que suprime

`solicitacao` da reserva com `tipo = reclamacao` e `status IN ('aberta',
'em_andamento')`. Serviço e consumo **não** entram. Leitura só pelo módulo
`atendimento`.

### Mensagem da pergunta

`tipo` de conteúdo operacional `pulso` (espelho de `boas_vindas` / coleta):
gravada **antes** do envio; `enviada_em` no sucesso. Recados de reconhecimento
e de confirmação negativa são mensagens `enviada` de sessão, no mesmo histórico
da reserva.

---

## Regras de elegibilidade (varredura)

A reserva entra na passagem quando **todas** valem:

| Condição | Onde |
| --- | --- |
| `status = hospedado` e `checkin_em IS NOT NULL` | SQL (`hospedagem`) |
| Não existe `enviar_pulso` para a reserva | SQL |
| Data UTC de `agora` > data UTC de `checkin_em` | Python |
| `24 * (data_checkout_prevista − hoje UTC)` ≥ prazo do hotel | Python |
| Sem reclamação aberta/em andamento | `atendimento` |
| Prazo do hotel presente e inteiro ≥ 1 | `parametro_hotel` |

Fora: ainda no dia do check-in; estadia de uma noite (no segundo dia a saída
prevista **é hoje** → 0 h); já encerrada/cancelada.

---

## Transições

```text
(sem pulso gravado, elegível)
    → INSERT mensagem pendente + trabalho enviar_pulso
    → envio ok: mensagem enviada
    → envio falha e ainda elegível: retoma o mesmo trabalho
    → já inelegível na retomada: conclui sem enviar

(pulso enviado, sem avaliacao)
    primeira mensagem do hóspede
        → classificar
        → operacional (dúvida/pedido/reclamação) + encerrar pulso em silêncio
          OU registrar_resposta_pulso (dono do turno)
        → INSERT avaliacao origem pulso_segundo_dia
        → se negativo e ainda sem reclamação desta mensagem: INSERT solicitacao reclamacao
```

Não há máquina de estados nova em `reserva`.

---

## Delta DDL (documental; a revisão congela a cópia)

```sql
ALTER TABLE trabalho DROP CONSTRAINT ck_trabalho_tipo;
ALTER TABLE trabalho ADD CONSTRAINT ck_trabalho_tipo
    CHECK (tipo IN ( /* vigentes + */ 'enviar_pulso', 'registrar_resposta_pulso'));

CREATE UNIQUE INDEX uq_trabalho_enviar_pulso_reserva
    ON trabalho ( ((payload->>'id_reserva')::bigint) )
    WHERE tipo = 'enviar_pulso';

CREATE UNIQUE INDEX uq_trabalho_registrar_resposta_pulso_mensagem
    ON trabalho ( ((payload->>'id_mensagem')::bigint) )
    WHERE tipo = 'registrar_resposta_pulso';
```

Semeadura idempotente de `horas_minimas_para_pulso = '24'`.
Atualizar o `COMMENT` de `parametro_hotel` (lista de chaves) e `docs/04-schema.sql`.

`avaliacao` e `uq_avaliacao_reserva_origem` **não** mudam.

---

## Relacionamentos

```text
reserva 1 — 0..1 avaliacao (origem pulso_segundo_dia)
reserva 1 — 0..1 trabalho enviar_pulso
mensagem (pergunta) 1 — 1 trabalho enviar_pulso (payload)
mensagem (resposta do hóspede) 0..1 trabalho registrar_resposta_pulso
mensagem (resposta) 0..1 solicitacao reclamacao (recuperação)
```
