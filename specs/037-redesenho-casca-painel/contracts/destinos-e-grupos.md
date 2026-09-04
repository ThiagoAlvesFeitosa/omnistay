# Contrato: destinos, grupos e menu

Fonte: `frontend/src/painel/destinos.ts`. A matriz HTTP **não**
duplica este mapa.

Perfis no código: `recepcao` · `staff` · `gestor`.

---

## Casa (inalterada)

| Perfil | Path | Título |
| --- | --- | --- |
| `recepcao` | `/app/fila` | Fila do dia |
| `staff` | `/app/chamados` | Meus chamados |
| `gestor` | `/app/indicadores` | Painel |

---

## Menu visível

✅ no menu · 🚫 rota existe, **fora** do menu · ❌ sem destino.

| Destino | Título | Grupo | `recepcao` | `staff` | `gestor` |
| --- | --- | --- | :---: | :---: | :---: |
| `fila` | Fila do dia | Operação | ✅ casa | ❌ | ❌ |
| `reserva` | Nova reserva | — | 🚫 | ❌ | ❌ |
| `ficha` | Estadia | Operação | ✅ | ❌ | ❌ |
| `alertas` | Chamados e pedidos | Operação | ✅ | ❌ | ❌ |
| `consumos` | Consumos a lançar | Operação | ✅ | ❌ | ❌ |
| `saida` | Saída do hóspede | Operação | ✅ | ❌ | ❌ |
| `catalogo` | Catálogo | Propriedade | ✅ | ❌ | ✅ |
| `vendaveis` | Itens vendáveis | Propriedade | ✅ | ❌ | ✅ |
| `boas-vindas` | Recado de boas-vindas | Propriedade | ✅ | ❌ | ✅ |
| `chamados` | Meus chamados | Operação | ❌ | ✅ casa | ❌ |
| `indicadores` | Painel | Gestão | ❌ | ❌ | ✅ casa |
| `mercado` | Mercado | Gestão | ❌ | ❌ | ✅ |
| `usuarios` | Usuários | Gestão | ❌ | ❌ | ✅ |
| `retencao` | Retenção de dados | Gestão | ❌ | ❌ | ✅ |
| `simulador` | Simulador | *(fim, sem rótulo)* | ✅ | ❌ | ✅ |

Gestão **não** tem grupo Operação (nenhum item). Equipe **não** tem
Propriedade, Gestão nem Simulador. Recepção **não** tem grupo Gestão.

Estadia e Saída sem `:idReserva`: estado vazio já entregue; itens
permanecem no menu.

Endereço alheio: casca vai à casa; API recusa como já recusava.

---

## Rotas

Paths F8.1+ intactos (`/app/ficha/:idReserva?`, `/app/saida/:idReserva?`,
`/app/reserva`, …). Esta fatia não cria destino novo.
