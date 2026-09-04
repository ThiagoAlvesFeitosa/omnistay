# Contrato: navegação da casca

Prefixo `/app`, cookie e recusa 401 **inalterados** (F8.1). Este
contrato substitui o chrome da faixa superior.

---

## Largo (`min-width: 768px`)

- Coluna permanente à esquerda, ~240 px, fundo escuro, altura
  inteira.
- Conteúdo à direita; a navegação **não** cobre o título da tela.
- Sem botão de abrir menu.

---

## Estreito (abaixo de 768 px)

- Área de trabalho é a tela cheia (meus chamados, na equipe).
- Controle explícito abre o overlay com a **mesma** identidade e os
  **mesmos** destinos do perfil.
- Fecha: mesmo controle; toque no fundo (área de trabalho); destino;
  Sair.
- Fechar pelo controle ou pelo fundo **não** muda a rota.

Recepção ou gestão com janela estreita: o mesmo overlay, não um
chrome especial.

---

## Identidade (sempre que autenticado, no chrome de navegação)

1. Topo: **nome da casa** (`nome_hotel`) em destaque.
2. Abaixo: marca **OmniStay** em tom discreto.
3. Rodapé: nome da pessoa, rótulo do perfil, **Sair**.

| `perfil` | Rótulo visível |
| --- | --- |
| `recepcao` | Recepção |
| `gestor` | Gestão |
| `staff` | Equipe |

Não se exibe o jargão `staff` / `gestor` na UI.

---

## Menu

Itens via `itensMenu` + grupos — [destinos-e-grupos.md](./destinos-e-grupos.md).
Simulador depois dos grupos, sem rótulo de grupo. Grupo vazio some.

**Nova reserva** não é `NavLink`. O botão na fila permanece.

O atalho antigo `compacto` (equipe sem `<nav>`) **deixa de existir**.

---

## Teste

Vitest na `Casca`: identidade nos três perfis; grupos; overlay
fecha sem navegar; menu da recepção sem “Nova reserva”; equipe vê
“Meus chamados” e “Equipe”. Viewport estreito: `matchMedia` falso ou
estado equivalente — sem Playwright.
