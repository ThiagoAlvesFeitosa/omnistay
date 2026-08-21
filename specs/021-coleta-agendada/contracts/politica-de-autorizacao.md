# Contrato: política de autorização — F5.2

Esta fatia **não acrescenta operação** na matriz e **não acrescenta rota**.
A coleta é trabalho de sistema, não clique de perfil.

A matriz da F5.1 permanece:

| Operação | `recepcao` | `staff` | `gestor` |
| --- | :---: | :---: | :---: |
| `alterar_concorrentes` | ❌ | ❌ | ✅ |
| `ler_concorrentes` | ❌ | ❌ | ✅ |

---

## Quem dispara a coleta

O worker, com `id_hotel` da ficha. Sem cookie, sem perfil. Não reutiliza
`alterar_concorrentes` (isso cadastra quem acompanhar, não grava preço).

---

## O que cada perfil **não** ganha nesta fatia

| Tentativa | Recusa |
| --- | --- |
| Gestão inventar ou editar linha de `coleta_mercado` | Não há rota. F5.3 reforça “somente leitura” do número coletado |
| Recepção/operação disparar coleta | Não há rota; `403` nas rotas de concorrente continua |
| Gestão de A coletar ficha de B | Processador relê `id_hotel`; ficha alheia = omitida, sem revelar |

---

## Relação com “gestão somente leitura”

O Artefato 5 §11.2 (gestor só lê painéis de mercado) aplica-se ao **número
coletado**. Esta fatia grava o número pelo sistema. A gestão continua
podendo cadastrar concorrentes (F5.1); continua **sem** poder fabricar
preço. Consulta com data, variação e dado velho = F5.3 (`ler_mercado`, se
nascer).

---

## Fora desta fatia

- Tela React
- `POST` de disparo manual
- GET autenticado da série (F5.3)
- Alterar `periodicidade_coleta_mercado` pelo painel (chave no banco;
  sem tela, como as demais)
