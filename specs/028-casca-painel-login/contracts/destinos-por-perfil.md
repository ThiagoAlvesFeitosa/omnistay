# Contrato: destinos por perfil

Fonte da verdade da casca: módulo `frontend/src/painel/destinos.ts`.
A matriz de `politica.py` **não** duplica este mapa. Recusa HTTP
continua nas rotas de API já existentes.

Perfis: `recepcao` · `staff` · `gestor` (os mesmos de `usuario.perfil`).

---

## Casa (tela inicial)

| Perfil | Path | Título |
| --- | --- | --- |
| `recepcao` | `/app/fila` | Fila do dia |
| `staff` | `/app/chamados` | Meus chamados |
| `gestor` | `/app/indicadores` | Painel |

Sem passo intermediário de escolha.

---

## Menu visível

✅ aparece · ❌ não aparece. Sair é ação da casca, não linha desta
tabela; autenticado **sempre** vê Sair.

| Destino | Título | `recepcao` | `staff` | `gestor` |
| --- | --- | :---: | :---: | :---: |
| `fila` | Fila do dia | ✅ casa | ❌ | ❌ |
| `reserva` | Nova reserva | ✅ | ❌ | ❌ |
| `ficha` | Ficha do hóspede | ✅ | ❌ | ❌ |
| `alertas` | Chamados e pedidos | ✅ | ❌ | ❌ |
| `consumos` | Consumos a lançar | ✅ | ❌ | ❌ |
| `saida` | Saída do hóspede | ✅ | ❌ | ❌ |
| `catalogo` | Catálogo | ✅ | ❌ | ❌ |
| `vendaveis` | Itens vendáveis | ✅ | ❌ | ❌ |
| `boas-vindas` | Recado de boas-vindas | ✅ | ❌ | ❌ |
| `chamados` | Meus chamados | ❌ | ✅ casa | ❌ |
| `indicadores` | Painel | ❌ | ❌ | ✅ casa |
| `mercado` | Mercado | ❌ | ❌ | ✅ |
| `usuarios` | Usuários | ❌ | ❌ | ✅ |
| `retencao` | Retenção de dados | ❌ | ❌ | ✅ |
| `simulador` | Simulador | ✅ | ❌ | ✅ |

Fora desta fatia (nem no menu):

- Dispositivos conectados (revogar continua API da recepção)
- Configurações / módulos por propriedade (F7.4)

---

## Endereço alheio

Quem autenticado abre um path que o seu perfil não tem: a casca **não**
renderiza o título nem o corpo daquele destino. Vai à casa. A API, se
chamada, continua recusando com o status que já recusava (`403` / `404`).

Visitante no mesmo path: `/app/entrar`.

---

## Telas nomeadas

Destinos que não são a casa nem o simulador: só o título da tabela.
Zero hóspede, zero chamado, zero indicador numérico inventado. Zero
`fetch` operacional.

O simulador é exceção: já opera contra `/simulador/conversas`.
