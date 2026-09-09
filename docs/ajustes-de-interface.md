# Ajustes de interface — lista acumulada

**Para que serve:** juntar tudo que foi notado durante os testes, para entregar de uma vez em vez
de pingado. Aberto em 02/09/2026.

**Princípio que orienta a lista:** quanto mais simples e intuitivo, melhor. Menu serve para
navegar; ação pertence à tela onde ela faz sentido.

---

## 1. Menu lateral no lugar do superior

Horizontal com onze itens já está apertado e vai quebrar em tela menor.

- Lateral fixa, largura ~240px, fundo escuro, altura inteira
- Em tela estreita, vira menu que abre por botão — a tela da equipe precisa continuar
  utilizável no celular

## 2. Identidade no topo da lateral

Hoje só aparece o nome do usuário, solto no canto.

- **Nome do hotel** em destaque, no topo
- **Marca OmniStay** logo abaixo, discreta — é a marca do produto, não do cliente
- **Nome do usuário e o perfil** ("Recepção", "Gestão", "Equipe") no rodapé da lateral, junto
  do botão Sair

> **Exige mudança no backend:** `GET /sessoes/atual` e `POST /sessoes` não devolvem o nome do
> hotel. Acrescentar `nome_hotel`, vindo de `propriedade` pelo `id_hotel` da sessão.

## 3. Tirar do menu o que é ação, não lugar

**"Nova reserva" está no menu e como botão na fila do dia.** Redundância confunde: sugere que
são coisas diferentes.

- Sai do menu. Fica só o botão na fila do dia, que é onde a ação pertence
- Revisar o resto do menu com o mesmo critério

## 4. Agrupar o menu por área

Onze itens numa lista plana não têm hierarquia. Agrupar, com rótulos discretos:

- **Operação** — fila do dia, chamados e pedidos, consumos a lançar, saída do hóspede
- **Propriedade** — catálogo, itens vendáveis, recado de boas-vindas
- **Gestão** — painel, mercado, usuários, retenção
- **Simulador** — separado, no fim

Cada item continua aparecendo só para quem pode usá-lo.

## 5. Simulador

É a tela que mais aparece no vídeo, e é a menos cuidada.

- **Tipografia serifada, diferente do resto do painel.** Alinhar
- **A caixa de mensagem não envia com Enter** — só clicando no botão. Corrigir:
  Enter envia, Shift+Enter quebra linha
- Aparência de conversa: balões distintos para hóspede e hotel, horário em cada mensagem
- Lista de reservas com o mesmo estilo de cartão das outras telas

## 6. Moeda e data no padrão brasileiro

Aparece em várias telas e é o que mais denuncia protótipo.

- `R$ 0,00` — hoje mostra `0.00`
- `02/09/2026` — hoje mostra `2026-09-02`
- Função utilitária compartilhada, com teste

---

## Como entregar

Tudo isto é uma fatia só, de umas duas a três horas. Vale fazer de uma vez: são todas mudanças
na mesma camada, e fatiar multiplicaria o retrabalho.

**Manter verdes** os testes que já existem, e acrescentar teste da casca nova.
