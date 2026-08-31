export type ItemSolicitacao = {
  id_solicitacao: number;
  id_reserva: number;
  tipo: string;
  descricao: string;
  numero_quarto: string | null;
  urgencia: string;
  janela_preferencia: string | null;
  status: string;
  aberta_em: string;
  destaque_tempo_excedido: boolean;
  valor_praticado: string | number | null;
  status_lancamento: string | null;
};

const NATUREZAS: Record<string, string> = {
  reclamacao: "reclamação",
  servico: "serviço",
  consumo: "consumo",
};

export function rotuloNatureza(tipo: string): string {
  return NATUREZAS[tipo] ?? tipo;
}

export function tempoDecorrido(abertaEm: string, agora: Date): string {
  const aberto = new Date(abertaEm).getTime();
  const ms = Math.max(0, agora.getTime() - aberto);
  const minuto = 60_000;
  const hora = 60 * minuto;
  const dia = 24 * hora;
  if (ms < minuto) {
    return "há menos de 1 min";
  }
  if (ms < hora) {
    return `há ${Math.floor(ms / minuto)} min`;
  }
  if (ms < dia) {
    return `há ${Math.floor(ms / hora)} h`;
  }
  return `há ${Math.floor(ms / dia)} d`;
}
