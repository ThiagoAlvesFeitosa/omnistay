# Contrato: destinos e perfis — F8.7

Esta fatia **não acrescenta operação** à matriz. Recusa permanece
nas rotas (`ler_indicadores`, `ler_mercado`, `administrar_usuario`,
`ler_retencao`).

O mapa da casca **não muda os `perfis`**: Painel, Mercado,
Usuários e Retenção **já** são só `gestor` (F8.1). O que muda é o
conteúdo: deixam de ser título sozinho.

Isolamento por hotel: `id_hotel` da sessão.

---

## Operações que estas telas disparam

| Operação existente | `recepcao` | `staff` | `gestor` | Onde |
| --- | :---: | :---: | :---: | --- |
| `ler_indicadores` | ❌ zero fetch | ❌ | ✅ `GET /indicadores` | Painel |
| `ler_mercado` | ❌ | ❌ | ✅ dois GET | Mercado |
| `administrar_usuario` | ❌ | ❌ | ✅ GET/POST/DELETE | Usuários |
| `ler_retencao` | ❌ | ❌ | ✅ GET | Retenção |

Sessão (`GET/DELETE /sessoes/atual`) continua a da F8.1.

---

## Menu (sem delta de visibilidade)

| Destino | Título | `recepcao` | `staff` | `gestor` |
| --- | --- | :---: | :---: | :---: |
| `indicadores` | Painel | ❌ | ❌ | ✅ casa do papel |
| `mercado` | Mercado | ❌ | ❌ | ✅ |
| `usuarios` | Usuários | ❌ | ❌ | ✅ |
| `retencao` | Retenção de dados | ❌ | ❌ | ✅ |

Casa dos três perfis **não** muda.

---

## Regras da superfície

- Sem sessão: estes paths não mostram conteúdo — tela de entrada.
- Recepção ou staff nesses endereços: a casca não renderiza o
  conteúdo e **não** dispara os GET/POST/DELETE acima.
- Gestão: monta, dispara o GET de cada tela; POST/DELETE só em
  Usuários, só nos botões.
- Compacto da equipe: estas telas **não** usam `compacto`.

---

## Não chamar nesta fatia

| Operação / rota | Por que não |
| --- | --- |
| `GET /fila-do-dia`, `GET /solicitacoes`, `GET /consumos/pendentes` | Lista nominada; o Painel usa números |
| `GET /indicadores/chegadas-do-dia` | Painel usa o envelope de quatro campos |
| `POST`/`PATCH /concorrentes` | Comparativo só |
| `GET /sessoes`, `revogar_sessao` | Da recepção |
| `PATCH` reativar usuário | Fora na clarificação |
| Personalidade / módulos | Fora |
