# Contrato: API do comprovante de retenção

Um GET. Cookie de sessão `omnistay_sessao`. O hotel é **sempre** o da
sessão — corpo e query **não** carregam `id_hotel`.

Autorização: [politica-de-autorizacao.md](./politica-de-autorizacao.md).
Modelo: [data-model.md](../data-model.md).

Esta fatia **não** dispara a passagem pelo HTTP.

---

## Convenções

| Tema | Regra |
| --- | --- |
| Autenticação | Cookie; ausência → `401` |
| Autorização | Perfil sem `ler_retencao` → `403` |
| Escrita / disparo | Método inexistente → `405` |
| Logs | `id_hotel`, ação `comprovante`. Quantidades do comprovante podem ir ao log (não identificam o titular). Sem texto, nome, telefone, documento |
| `id_hotel` no JSON | Ausente |

Datas em ISO-8601 com fuso (`TIMESTAMPTZ`).

---

## `GET /retencao`

**Operação**: `ler_retencao`

Lista os comprovantes da propriedade da sessão, mais recente primeiro.

### Saída `200`

```json
{
  "execucoes": [
    {
      "id_execucao": 9,
      "executado_em": "2026-08-24T03:00:00+00:00",
      "mensagens_anonimizadas": 12,
      "comentarios_anonimizados": 2,
      "payloads_anonimizados": 12,
      "descricoes_anonimizadas": 3,
      "fichas_apagadas": 1,
      "prazo_conteudo_ausente": false,
      "prazo_ficha_ausente": false
    }
  ]
}
```

Hotel sem nenhuma passagem ainda: `"execucoes": []` — não é erro.

Passagem em que nada venceu: quantidades zero; a linha existe (cumprimento
também se demonstra assim).

Prazo ausente naquele tipo: flag `true` e quantidade daquele tipo 0.

---

## Métodos recusados

| Método | Caminho | Resposta |
| --- | --- | --- |
| `POST` / `PUT` / `PATCH` / `DELETE` | `/retencao` | `405` |
| `POST` | `/retencao/executar` (ou equivalente) | **não existe** — não cadastrar rota de disparo |

---

## Fora desta fatia

- Tela React
- Filtro por intervalo na query (a lista completa do hotel cabe no MVP)
- Edição das chaves de prazo pelo painel
