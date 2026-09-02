export type SituacaoMercado =
  | "atual"
  | "desatualizado"
  | "cadencia_ausente"
  | "sem_coleta"
  | "so_falha";

export type UltimoSucesso = {
  preco: number | string | null;
  nota_media: number | string | null;
  coletado_em: string;
};

export type ItemMercado = {
  id_concorrente: number;
  nome: string;
  ativo: boolean;
  situacao: SituacaoMercado;
  ultimo_sucesso: UltimoSucesso | null;
  ultima_falha: { coletado_em: string } | null;
};

export type VisaoMercado = {
  periodicidade_horas: number | null;
  concorrentes: ItemMercado[];
};

export function linhaComFalha(item: ItemMercado): boolean {
  return item.situacao === "so_falha" || item.ultima_falha != null;
}

export function linhaAtual(item: ItemMercado): boolean {
  return item.situacao === "atual";
}

export function semColeta(item: ItemMercado): boolean {
  return item.situacao === "sem_coleta";
}

export function temPrecoEncontrado(item: ItemMercado): boolean {
  return item.ultimo_sucesso != null && item.ultimo_sucesso.preco != null;
}
