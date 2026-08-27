# Contrato: aviso de assistente virtual

Montagem do recado: `app/modulos/conversa/texto_boas_vindas.py`.
Modelo: [data-model.md](../data-model.md).

---

## Onde vive

Constante de produto, **não** parâmetro da propriedade. Inserida na
montagem do recado de boas-vindas, **antes** da linha do convite.

Ordem obrigatória:

```text
Ola, {prenome}! Sua chegada esta confirmada, seja bem-vindo.
Cafe da manha: {cafe}
Wi-Fi: {wifi}
Checkout: {checkout}
O atendimento inicial e feito por uma assistente virtual. Uma pessoa da recepcao assume quando necessario.
Quer saber mais alguma coisa da sua estadia? Pode perguntar por aqui.
```

| Exigência | Verificação |
| --- | --- |
| Duas ideias | Texto contém assistente virtual **e** pessoa da recepção que assume |
| Uma vez | Só neste recado; coleta, lembrete, sessão, pulso e pesquisa **não** ganham a frase |
| Única `?` | Continua na última linha (contrato F2.2) |
| Três fatos | Café, wi-fi e checkout inalterados |
| Sem slot novo | Assinatura da função **não** ganha parâmetro de aviso |
| Sem oferta | Termos de desconto/promoção continuam ausentes |
| Um dado pessoal | Só o prenome |

---

## O que não muda

- Unicidade: um recado por reserva
- Slots vazios: recado não sai; o aviso **não** viaja sozinho
- Recuperação na janela de `checkin_em`: o recado recuperado já sai **com** o aviso
- Perfis: quem editava os três slots continua sem poder editar o aviso
  (não há operação nova)

---

## Canal real versus simulador

| Superfície | Aviso visível nesta fatia |
| --- | --- |
| Histórico (`mensagem.conteudo`) | Sim — o corpo montado |
| Tela de simulação | Sim — lê o histórico |
| WhatsApp Cloud (template `boas_vindas`) | Não, até republicar o texto fixo na Meta. As quatro variáveis não carregam o aviso |

Critério de pronto: corpo montado. Limitação honesta no canal Meta.

---

## Fora desta fatia

- Tom / personalidade em `parametro_hotel` (resto da F7.2)
- Linha de convite editável (F7.3)
- Assinatura em cada resposta automática
- Recado avulso só com o aviso
