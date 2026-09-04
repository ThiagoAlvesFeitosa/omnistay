# Quickstart: casca redesenhada e apresentação BR

Validação humana + suítes. Sem Playwright. Contratos:
[sessao-nome-da-casa.md](./contracts/sessao-nome-da-casa.md),
[casca-navegacao.md](./contracts/casca-navegacao.md),
[apresentacao-br.md](./contracts/apresentacao-br.md),
[conversa-bolhas.md](./contracts/conversa-bolhas.md).

## Pré-requisitos

API e worker como no restante do projeto. Frontend: `npm install`
em `frontend/`, `npm run dev` (base `/app/`). Sessão de demo já
semeada.

## 1. Nome da casa no JSON

Com cookie de recepção da propriedade A:

```text
GET /sessoes/atual
```

Esperado: `200`, `nome_hotel` igual ao `hotel.nome` dessa casa.
`POST /sessoes` 201 devolve o mesmo campo. Não aparece `id_hotel`.
Login da propriedade B não devolve o nome da A.

## 2. Casca no computador

Entrar como recepção. Lateral escura: nome da casa, OmniStay
discreto, grupos Operação / Propriedade, Simulador no fim, rodapé
com nome + **Recepção** + Sair. **Nova reserva** não está no menu;
está no botão da fila. Estadia e Saída estão em Operação.

Gestão: Propriedade + Gestão + Simulador; rótulo **Gestão**.
Equipe: só Operação / Meus chamados; rótulo **Equipe**.

## 3. Casca no telefone (ou janela < 768 px)

Equipe: meus chamados ocupam a tela; botão abre o menu; tocar fora
fecha sem mudar de tela; Sair fecha e vai à entrada.

## 4. Simulador e Estadia

Simulador: tipografia do painel, cartões na lista, balões dois
lados, horário `14:32` em mensagem de hoje, Enter envia,
Shift+Enter quebra linha.

Estadia: os mesmos dois lados; rótulos Hóspede / Automático /
Recepção; Enter **não** envia. Mensagem de outro dia: data e hora.

## 5. Grafia

Fila: datas `02/09/2026`. Vendáveis / painel: `R$ 9,00`. Chamados:
`02/09/2026 14:32 · há …`. Mercado / retenção: instante completo,
não `2026-09-01`. Input de data da nova reserva continua nativo.

## Comandos

```bash
pytest testes/unitarios/modulos/acesso -q
pytest testes/integracao/test_autenticacao.py -q
cd frontend && npm test
```

Esperado: sessão com `nome_hotel`; Vitest da casca, apresentação,
simulador e regressão das telas (grafia nova no mesmo cenário).
Worker intocado.
