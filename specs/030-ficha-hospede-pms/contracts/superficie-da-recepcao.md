# Contrato: superfície da recepção — ficha

Fonte: `TelaFicha` em `/app/ficha` e `/app/ficha/:idReserva`.
A casca (F8.1) permanece: menu, sair, recusa de destino alheio.
A fila (F8.2) ganha **Ver ficha**; o restante da fila não muda.

Recepção no computador. Sem layout de mão nesta fatia.

---

## Abrir a partir da fila (`/app/fila`)

Em cada linha, controle rotulado **Ver ficha** (link ou botão que
navega para `/app/ficha/{id_reserva}`). Convive com **Confirmar
chegada** quando este existir. Clique em nome, telefone, datas ou
situação **não** confirma chegada (F8.2 intacto) e **não** é o
caminho da ficha — o rótulo é.

---

## Menu sem reserva (`/app/ficha`)

Título **Ficha do hóspede**. Texto de que a ficha se abre pela fila
do dia. **Zero** `GET /reservas/…/ficha`. Sem dado cadastral.

Atalho visível de volta à fila.

---

## Ficha de uma reserva (`/app/ficha/:idReserva`)

Título **Ficha do hóspede**. Identificação: nome + reserva (id) +
distintivo **completa** ou **parcial** (rótulos distintos).

Se `estado_cadastro === "leitura_humana"`: aviso de que precisa de
leitura humana, **sem** o corpo da mensagem.

**Campos**, nesta ordem, os nove da coleta. Sem e-mail. Sem campo
de idade gravável. Se houver data de nascimento, a idade pode
aparecer como texto derivado ao lado, claramente não editável.

**Parcial**: lista cada ausente pelo rótulo (“Falta: Profissão,
CEP, …”), não só “faltam N”.

**Copiar tudo** — gesto principal visível. Monta o texto das nove
linhas `Rótulo: valor` (valor vazio se ausente). Chama a cópia do
navegador. Se falhar: o mesmo texto permanece visível e
selecionável. O OmniStay **não** diz que o sistema de gestão gravou.

**Editar / Gravar** — habilita os nove campos; Gravar dispara
`PUT`. Cancelar descarta o formulário e volta ao último carregado.
Sucesso: distintivo e ausentes atualizam na hora. Nenhuma mensagem
ao hóspede.

**Voltar à fila** — navega para `/app/fila` (GET da fila como já é).

### Consentimento (bloco abaixo dos campos)

| Estado | O que mostra | Ação |
| --- | --- | --- |
| Aceite com `momento` | concedido em {data} | **Revogar** |
| Recusa com `momento` | recusado em {data} | registrar aceite no balcão, se a pessoa pedir |
| Sem `momento` | nunca registrado / sem aceite vigente | registrar aceite no balcão |

Revogar e aceite: `POST` com `origem: "painel"`. Sem diálogo de
marketing, sem pesquisa.

### Falha de leitura

Painel (menu, título) permanece. Declara que a ficha não carregou.
Oferece **Tentar de novo** e voltar à fila. **Não** mostra ficha de
outra pessoa. **Não** usa o estado vazio do menu. **Não** manda à
entrada (isso é só 401).

### Carregando

Título visível; não mostrar “completa” nem lista de ausentes como se
já tivesse dado.

---

## Texto de cópia (formato desta variação)

Uma linha por campo, na ordem da coleta, rótulo em português:

```text
Nome completo: Marina Duarte Fonseca
Profissão: Gerente de contas
Data de nascimento: 14/03/1992
Tipo de documento: CPF
Número do documento: 12345678900
Endereço: Rua das Acácias, 220
CEP: 04567000
Cidade: São Paulo
Telefone: 5511987654321
```

Campo vazio: `Profissão:` sem valor inventado. Sem linha `Idade`.
Sem e-mail. Sem corpo de mensagem.

Data no texto copiado: a mesma que a tela mostra (local `dd/mm/aaaa`).

---

## O que não aparece

- E-mail
- Foto / anexo de documento
- Confirmar chegada ou saída
- Acompanhante
- Ordem de campos configurável / copiar um campo
- Destino `ficha` para staff ou gestão (casca já redireciona)
