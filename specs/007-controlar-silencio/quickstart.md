# Quickstart — validar a entrega de Controlar o Silêncio

Roteiro manual além da suíte. Contratos em [contracts/](./contracts/).

Comandos em PowerShell, na raiz do repositório. Use `curl.exe`.

---

## Pré-requisitos

```powershell
docker compose up -d
alembic upgrade head
```

`DATABASE_URL` no ambiente. Hotel + recepção como no quickstart da F1.1.
Mensageria em **porta falsa**. API no ar; worker só quando o roteiro pedir.

Fluxo prévio: reserva do dia (ou com check-in futuro conhecido) em `aguardando_cadastro`,
coleta com `status_envio = enviada`. Prazos do hotel: `horas_ate_reenvio` e
`horas_corte_antes_checkin` (defaults 24 e 12 após bootstrap/migração).

Para não esperar 24 h de verdade, a suíte congela o relógio. Neste roteiro manual, reduza
os prazos no banco **desta** propriedade de teste:

```powershell
docker compose exec db psql -U postgres -d omnistay -c "SELECT chave, valor FROM parametro_hotel WHERE chave IN ('horas_ate_reenvio','horas_corte_antes_checkin');"
```

---

## Cenário 0 — Esquema: tipo `enviar_lembrete` e fila

```powershell
alembic current
docker compose exec db psql -U postgres -d omnistay -c "\d trabalho"
docker compose exec db psql -U postgres -d omnistay -c "\d+ vw_fila_do_dia"
```

**Esperado**: `trabalho.tipo` admite `enviar_lembrete`; visão lista `estado_cadastro` com
`sem_cadastro_previo`.

---

## Cenário 1 — Um único lembrete após o primeiro prazo

Com coleta enviada, **sem** mensagem recebida, avance o relógio (teste) ou o prazo até
vencer `horas_ate_reenvio`, ainda fora da janela de corte.

```powershell
python -m worker --verificar-cadastros
python -m worker --uma-passagem
```

**Esperado**:

- 1 `mensagem` de saída nova (lembrete) com opcionalidade e “preenchimento na recepção”
- 1 `trabalho` `enviar_lembrete` concluído (após a passagem)
- `reenvio_realizado = true`
- `reserva.status` ainda `aguardando_cadastro`
- corpo só com primeiro nome como dado pessoal

Rode `--verificar-cadastros` de novo.

**Esperado**: nenhuma segunda mensagem de lembrete.

---

## Cenário 2 — Resposta cancela o lembrete

Nova reserva: coleta enviada, **antes** do primeiro prazo o hóspede responde (webhook F1.3).
Depois vença o prazo e verifique.

**Esperado**: 0 lembretes; status o da interpretação (completa / parcial / aguardando+leitura
humana); `reenvio_realizado` permanece falso.

---

## Cenário 3 — Janela de corte marca a fila

Reserva silenciosa, lembrete já tratado **ou** entrada tão próxima que o corte vem primeiro.
Vença `horas_corte_antes_checkin` (ou use data de entrada já passada).

```powershell
python -m worker --verificar-cadastros
$sessao = "omnistay_sessao=<token-da-recepcao>"
curl.exe -i http://localhost:8000/fila-do-dia -H "Cookie: $sessao"
```

**Esperado**:

- `status = sem_cadastro_previo`
- `estado_cadastro = sem_cadastro_previo`
- nenhuma mensagem nova cobrando cadastro
- reserva **não** cancelada

---

## Cenário 4 — Check-in continua possível (banco)

Com a reserva do cenário 3, um `UPDATE` de teste para `hospedado` (ou o teste de transição
permitida da suíte) deve ser **aceito** pela trigger. Esta fatia não entrega o botão.

---

## Cenário 5 — Coleta nunca enviada

Reserva com coleta em `falha`/`pendente`. Vença o intervalo de reenvio.

**Esperado**: 0 lembretes. Na janela de corte, ainda pode marcar `sem_cadastro_previo`.

---

## Cenário 6 — Privacidade no log

Dispare lembrete ou marcação e inspecione logs.

**Esperado**: só identificadores e códigos; sem corpo, telefone ou nome.

---

## Suíte automatizada (smoke)

```powershell
pytest testes/unitarios -q
pytest testes/integracao -k "silencio or lembrete or sem_cadastro or fila_do_dia" -q
```

**Esperado**: verde, sem rede Meta. Relógio falso; sem esperar 24 h reais.
