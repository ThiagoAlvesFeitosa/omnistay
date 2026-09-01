import { tempoDecorrido } from "./solicitacoes";

export type ItemConsumoPendente = {
  id_solicitacao: number;
  id_reserva: number;
  descricao: string;
  descricao_item: string;
  numero_quarto: string | null;
  valor_praticado: string | number;
  status_lancamento: string;
  aberta_em: string;
  resolvida_em: string | null;
};

function valorNumerico(valor: string | number): number {
  return typeof valor === "number" ? valor : Number(valor);
}

export function totalPendente(itens: ItemConsumoPendente[]): number {
  return itens.reduce((soma, linha) => soma + valorNumerico(linha.valor_praticado), 0);
}

export function pendentesDaEstadia(
  itens: ItemConsumoPendente[],
  idReserva: number,
): ItemConsumoPendente[] {
  return itens.filter((linha) => linha.id_reserva === idReserva);
}

export function tempoDoMaisAntigo(itens: ItemConsumoPendente[], agora: Date): string {
  const primeiro = itens[0];
  return primeiro ? tempoDecorrido(primeiro.aberta_em, agora) : "";
}
