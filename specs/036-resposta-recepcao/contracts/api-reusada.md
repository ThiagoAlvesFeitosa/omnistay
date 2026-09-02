# Contrato: API reusada

Cookie e hotel da sessão. Esta fatia **não** altera o JSON destas
rotas.

## `GET /reservas/{id_reserva}/ficha`

Intacta (F8.3). A Estadia **só** a chama depois de **ver dados
cadastrais**. Abrir `/ficha/:id` **não** dispara este GET.

## `PUT /reservas/{id_reserva}/ficha`

Intacto. Continua no bloco cadastral expandido.

## `GET` / `POST` consentimento

Intocados. Disparados com a ficha, não com a conversa.

## `GET /fila-do-dia`

JSON intacto — `precisa_atendimento_humano` **já existe**. A tela
da fila passa a lê-lo. A **regra** por trás do booleano muda na
visão (`0025`); o nome do campo não.

## `GET /solicitacoes` e `POST .../resolucao`

Intocados. Responder **não** chama resolução.

## O que esta fatia não chama no envio

Webhook, simulador (a recepção não posta no fio do hóspede),
qualquer URL de sistema de gestão do hotel.
