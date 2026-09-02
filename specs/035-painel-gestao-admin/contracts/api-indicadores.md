# Contrato: `GET /indicadores`

Rota **nova**. Cookie `omnistay_sessao`. Hotel só o da sessão.
Operação: `ler_indicadores` (já na matriz: recepção e gestão).
Staff → `403`.

A tela Painel é o único cliente desta fatia. Recepção **não**
dispara este GET pela casca.

`GET /indicadores/chegadas-do-dia` permanece como está (F1.1).

---

## Saída `200`

```json
{
  "chegadas_hoje": 4,
  "hospedados": 2,
  "chamados_abertos": 5,
  "consumo_a_lancar": 132.00
}
```

| Campo | Tipo | Recorte |
| --- | --- | --- |
| `chegadas_hoje` | inteiro ≥ 0 | mesma regra de `GET /indicadores/chegadas-do-dia` |
| `hospedados` | inteiro ≥ 0 | `reserva.status = 'hospedado'` |
| `chamados_abertos` | inteiro ≥ 0 | `solicitacao.tipo` ∈ {`reclamacao`,`servico`} e `status` ∈ {`aberta`,`em_andamento`} |
| `consumo_a_lancar` | número ≥ 0 (duas casas) | soma de `consumo.valor_praticado` com `status_lancamento = 'pendente'`; `0` se não houver |

**Proibido** no JSON: `itens`, nome, telefone, documento,
`id_reserva`, `id_solicitacao`, `id_hospede`.

Hotel sem movimento: os quatro campos em `0`. Não é erro.

---

## Erros

| Situação | Status |
| --- | --- |
| Sessão ausente/inválida | `401` |
| Perfil `staff` | `403` |

Escrita (`POST`/`PUT`/`PATCH`/`DELETE` em `/indicadores`): `405`.

---

## Log

`id_hotel`, ação de leitura. **Não** os quatro números se isso
exigir ecoar valor de consumo como texto livre em log de debug
descontrolado — identificador e código bastam. Nunca dado de
hóspede.
