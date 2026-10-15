# Research: Conferir o CPF antes de gravar

## 1. Onde a conferência mora

**Decision**: Estender `validar_campos_extraidos` em
`app/modulos/conversa/validacao_ficha.py`. Quando `tipo_documento`
é `cpf`, o número só entra na saída se tiver onze dígitos (depois
de ignorar pontuação), não for sequência de um só dígito, e os
dois dígitos verificadores da Receita fecharem. O valor na saída
é sempre os onze dígitos. RG e passaporte continuam passthrough
como hoje. Sem biblioteca nova.

**Rationale**: Coleta (`refinar_resultado` → `consolidar_ficha_titular`)
e painel (`completar_ficha_titular`) já passam por essa função. Um
único sítio fecha FR-001 nos dois caminhos (Artigo XI). CEP e
telefone já normalizam ali; CPF segue o mesmo padrão.

**Alternatives considered**: Validar só no `PUT` — o WhatsApp
continuaria gravando dígito trocado. Lib `validate-docbr` —
peça extra sem problema que o módulo 11 não resolva (Artigo XI).
CHECK no banco exigindo onze dígitos para todo CPF — quebra os
pares antigos que a clarificação manda deixar com a escrita
original.

## 2. Painel: recusa inteira e aviso no campo

**Decision**: `completar_ficha_titular` já aborta o `UPDATE` se
qualquer informado não sobrevive à validação (`DadosInvalidos` →
`422`). Manter isso. Mensagem **sem** eco do número: o CPF não
confere. A tela (`TelaFicha`) mostra o recado **no campo** número
do documento, **não** substitui o rascunho — o que a pessoa digitou
permanece para corrigir só o CPF.

A API continua devolvendo o número em onze dígitos (como o CEP em
oito). Formatação `000.000.000-00` é da superfície: leitura, cópia
e, em edição, o valor visível do rascunho. Conferência no servidor;
o frontend **não** duplica o algoritmo.

**Rationale**: Clarificação de 15/10 (salvamento inteiro + aviso no
campo + formulário conservado). Duplicar módulo 11 em TypeScript
cria duas fontes (Artigo XI). `422` com `detail` texto já existe;
a tela passa a amarrar esse recado ao campo.

**Alternatives considered**: Gravar o resto e soltar o CPF —
recusado na clarificação. Validar só no cliente — o worker da
coleta não passaria. Corpo `422` estruturado `{campo, msg}` —
desnecessário se a mensagem de CPF é inequívoca e o tipo no
formulário já é CPF.

## 3. Forma canônica e índice único

**Decision**: Persistência = onze dígitos. Índice
`uq_hospede_documento` **não muda**. Sem CHECK novo em
`numero_documento`. Sem coluna nova.

**Rationale**: Clarificação: painel e cópia formatam; o gravado é
só dígitos. Os pares antigos que colidiriam ficam com a escrita
original — um CHECK “CPF ⇒ `\d{11}`” recusaria essas linhas
(Artigo IX: garantia no banco **quando pode**; aqui não pode sem
violar FR-012). Unicidade continua a de hoje; F9.3 é quem troca o
índice para `(id_hotel, …)`.

**Alternatives considered**: Gravar pontuado — duas grafias viram
dois documentos na F9.3. Dropar o UNIQUE nesta fatia — antecipa
F9.3 e deixa colisão silenciosa. CHECK com exceções pontuadas —
frágil e ainda não cobre RG.

## 4. Migração dos já gravados

**Decision**: Revisão Alembic **0027** (+ `docs/04-schema.sql` só
se o comentário da coluna mudar; o índice não muda). Para
`hospede` com `tipo_documento = 'cpf'` e número presente:

1. Forma nova = só dígitos.
2. Agrupar por essa forma. Grupos de **um**: `UPDATE` para onze
   dígitos.
3. Grupos de **dois ou mais**: ninguém do grupo é atualizado.
4. Log `warning`: `cpf_migracao_colisao pares=%s ids=%s` com a
   contagem de grupos deixados de fora e os `id_hospede`, **nunca**
   o número.
5. `0001` congelado.

A lógica de agrupamento é testável (função pura ou SQL coberto por
teste de integração com duas linhas que colapsam).

**Rationale**: Clarificação FR-012. Converter um do par e deixar o
outro criaria UNIQUE violation no `UPDATE`. Pular o grupo inteiro
preserva o índice e os cadastros. Identidade é F9.3/F9.5.

**Alternatives considered**: Converter o de menor `id` e pular o
resto — o spec manda o **par** ficar com a escrita original.
Apagar duplicata — proibido. Relaxar UNIQUE — F9.3.

## 5. Massa de demonstração e testes existentes

**Decision**: Trocar o CPF inválido `123.456.789-00` (estado,
roteiro, wireframe) por um número cujos dígitos fecham, gravado em
onze dígitos. Testes que usam `tipo_documento=rg` **não mudam**.
Onde o tipo é `cpf` com número que não confere, o teste passa a
esperar recusa ou usa um CPF que fecha. `semear_demo.py` cria
reserva, não ficha — o hóspede de demonstração nasce no simulador;
o roteiro de conversa é que precisa do CPF válido.

**Rationale**: FR-008 e o achado de 18/09. RG `1234567` nos testes
de ficha completa continua válido (FR-007).

**Alternatives considered**: Aceitar `123.456.789-00` como exceção
de demo — viola a conferência e reabre o 18/09.

## 6. Algoritmo (Receita, sem parâmetro de hotel)

**Decision**: Onze dígitos; rejeitar se todos iguais; dois dígitos
verificadores (módulo 11, pesos 10..2 e 11..2, resto 10 ou 11 →
0). Não é `parametro_hotel` (Artigo XIII): é regra federal, não
prazo da casa.

**Rationale**: Spec e backlog. Sequência `111.111.111-11` fecha o
módulo 11 em algumas contas e mesmo assim a Receita não emite —
FR-004 exige a rejeição à parte.

**Alternatives considered**: Consultar a Receita se o CPF existe —
integração externa, fora do MVP, e não é o defeito de 18/09.
Validar só o tamanho — o dígito trocado passaria.
