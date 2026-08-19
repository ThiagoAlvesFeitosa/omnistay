# Contrato: mensageria de sessão — confirmação de consumo e aviso

Porta já existente `enviar_texto_sessao`. **Nenhum método novo.** O hóspede
acabou de escrever; a janela de sessão está aberta. Sem template Utility.

Textos: funções puras em `conversa`. Testáveis sem porta.

---

## Confirmação de consumo (`unico`)

`montar_confirmacao_consumo(nome_completo, descricao_item, valor_praticado)`

- Prenome + recebimento do item + valor formatado `R$ 12,00` (duas casas,
  vírgula decimal)
- Afirma que a equipe vai atender
- **Não** afirma que o valor já foi lançado no sistema de gestão
- **Não** promete prazo
- **Não** contém as palavras “extrato” nem “conta” (nenhuma capitalização)

A enviada nasce `pendente` e só então a porta é chamada. JSON
`tipo = confirmacao_consumo` + `id_solicitacao`. Sem o texto no JSON.

---

## Aviso de identificação humana

`montar_aviso_identificacao(nome_completo)`

- Prenome + recebimento + recepção vai conferir
- **Sem** valor, **sem** nome de item chutado
- **Não** contém “extrato” nem “conta”

JSON `tipo = aviso_identificacao`. `desfecho` na **recebida**: `item_ambiguo`
ou `identificacao_indisponivel`.

---

## Confirmação de serviço (`nenhum`)

Inalterada (`montar_confirmacao_pedido`). Sem preço.

---

## Confirmação de resolução de consumo

O recado da F3.6 para tipo `servico` (“pedido atendido”) vale para `consumo`.
**Não** cita valor nem lançamento. **Não** usa “extrato” nem “conta”.
Lançar e dispensar **não** disparam mensagem.

---

## Falha de envio

Preserva `consumo` (e o valor), a enviada e o `desfecho`. Reagenda só a
mensageria. Não reabre identificação. Não apaga pendência de lançamento.

---

## Fora deste contrato

- Template Utility de consumo
- Recado no lançar / dispensar
- Lista de pedidos no checkout (F4.2)
- Porta nova ou parâmetro de copy em `parametro_hotel`
