export type CategoriaCatalogo =
  | "horario"
  | "cardapio"
  | "servico"
  | "programacao"
  | "regra";

export type ItemCatalogo = {
  id_catalogo_item: number;
  categoria: CategoriaCatalogo;
  titulo: string;
  conteudo: string;
  ativo: boolean;
};

export const CATEGORIAS: readonly { chave: CategoriaCatalogo; rotulo: string }[] = [
  { chave: "horario", rotulo: "Horários" },
  { chave: "cardapio", rotulo: "Cardápio" },
  { chave: "servico", rotulo: "Serviços" },
  { chave: "programacao", rotulo: "Programação" },
  { chave: "regra", rotulo: "Regras" },
];

export function itensDaCategoria(
  itens: ItemCatalogo[],
  categoria: CategoriaCatalogo,
): ItemCatalogo[] {
  return itens.filter((item) => item.categoria === categoria);
}

export function contarSituacao(itens: ItemCatalogo[]): {
  ativos: number;
  desativados: number;
} {
  return {
    ativos: itens.filter((item) => item.ativo).length,
    desativados: itens.filter((item) => !item.ativo).length,
  };
}
