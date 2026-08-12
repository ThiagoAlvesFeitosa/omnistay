# Contrato: política de autorização

A política é uma decisão pura: recebe o perfil e o nome da operação, devolve permitido ou recusado.
Não conhece HTTP, não conhece banco, e por isso é testável por unidade.

**A matriz declara operações que ainda não têm rota.** Hóspede chega na F1.3, reserva na F1.1,
solicitação na F3.4. Elas estão aqui porque a alternativa é cada fatia futura inventar sua própria
regra de acesso no momento em que escreve o roteador — e é assim que um perfil operacional acaba
lendo ficha cadastral por descuido. Ver [research.md](../research.md) seção 8.

---

## Matriz

| Operação | `recepcao` | `staff` | `gestor` | Fatia que a liga a uma rota |
| --- | :---: | :---: | :---: | --- |
| `ver_sessao_propria` | ✅ | ✅ | ✅ | **F0.3** |
| `encerrar_sessao_propria` | ✅ | ✅ | ✅ | **F0.3** |
| `listar_sessoes` | ✅ | ❌ | ❌ | **F0.3** |
| `revogar_sessao` | ✅ | ❌ | ❌ | **F0.3** |
| `administrar_usuario` | ❌ | ❌ | ✅ | **F0.3** |
| `ler_dado_cadastral_de_hospede` | ✅ | ❌ | ❌ | F1.3 |
| `alterar_ficha_de_hospede` | ✅ | ❌ | ❌ | F1.3 |
| `alterar_reserva` | ✅ | ❌ | ❌ | F1.1 |
| `confirmar_fase_da_reserva` | ✅ | ❌ | ❌ | F2.2, F4.1 |
| `ler_solicitacao_atribuida` | ✅ | ✅ | ✅ | F3.4, F3.5 |
| `resolver_solicitacao` | ✅ | ✅ | ❌ | F3.6 |
| `lancar_consumo` | ✅ | ❌ | ❌ | F3.7 |
| `alterar_catalogo` | ✅ | ❌ | ❌ | F2.1 |
| `ler_indicadores` | ✅ | ❌ | ✅ | F4.1, F5.3 |

---

## As decisões que a matriz toma, e por quê

**`staff` não lê nada de cadastro, e é isso que paga a sessão longa.** A contrapartida aceita no
Artefato 5 §11.2 é que um dispositivo perdido mantém acesso até a revogação. Ela só é aceitável
porque o que esse dispositivo alcança são chamados, nunca ficha de hóspede.

**`gestor` também não lê dado cadastral.** O backlog exige a recusa apenas para o perfil
operacional, então esta é uma escolha, não uma imposição: a gestão consulta indicadores, e indicador
agregado não é ficha. Minimização de dados pessoais (Artigo VIII) sem custo funcional.

**`gestor` administra usuário, e isso não contradiz "somente leitura".** A recusa da FR-019 vale
para dado de domínio — reserva, hóspede, solicitação, consumo e avaliação. Usuário não é dado de
domínio: é quem opera o sistema. Foi a ambiguidade corrigida no backlog durante a especificação.

**`gestor` não revoga sessão, e `recepcao` não cadastra usuário.** Autoridade e urgência são
separadas de propósito. Cadastrar e desligar funcionário é autoridade e cabe à gestão. Revogar
sessão de celular extraviado é urgência, e às três da manhã não pode depender do gerente.

**`staff` resolve solicitação, e por isso `alterar_dado_de_dominio` não existe como operação
única.** Fechar um chamado altera dado de domínio. Uma operação grossa recusaria o perfil operacional
junto com a gestão, ou liberaria a gestão junto com o operacional. A granularidade não é
preciosismo: é o que torna a matriz implementável sem exceção escondida no roteador.

**`alterar_catalogo` fica só com a recepção.** Catálogo não está na lista de dados de domínio da
FR-019, então a gestão poderia alterá-lo sem contrariar a spec. A escolha de não permitir mantém
coerência com "somente leitura" e é revisitável na F2.1, quando existir a tela.

---

## Como a recusa aparece

| Situação | Resposta |
| --- | --- |
| Sem cookie, cookie forjado, sessão expirada, sessão revogada, usuário desativado | **401**, sempre com a mesma mensagem |
| Sessão válida, perfil sem permissão para a operação | **403** |
| Sessão válida, alvo existente em outra propriedade | **404**, para não revelar que existe |

A distinção entre 401 e 403 é informação legítima: o cliente precisa saber se deve autenticar de
novo ou se aquele caminho simplesmente não é dele. O que nunca é dito é **por que** o 401 aconteceu.

---

## Isolamento por propriedade

A política responde por perfil. O isolamento por propriedade é ortogonal a ela e vale sempre: toda
leitura e toda escrita filtram pelo hotel do usuário da sessão, mesmo com uma única propriedade
cadastrada (Artigo XIV). Perfil autorizado a uma operação **não** implica alcance a dado de outro
hotel — são duas verificações, e nenhuma substitui a outra.
