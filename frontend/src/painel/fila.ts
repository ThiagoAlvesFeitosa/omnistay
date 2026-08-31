export type ItemFila = {
  id_reserva: number;
  nome: string | null;
  telefone_contato: string;
  data_checkin_prevista: string;
  data_checkout_prevista: string;
  status: string;
  estado_cadastro: string | null;
  chegada_nao_confirmada: boolean;
  boas_vindas_nao_enviadas: boolean;
};

export type ResumoTurno = {
  hoje: number;
  hospedados: number;
  vencidas: number;
};

export function resumirTurno(itens: ItemFila[]): ResumoTurno {
  let hoje = 0;
  let hospedados = 0;
  let vencidas = 0;
  for (const linha of itens) {
    if (linha.status === "hospedado") {
      hospedados += 1;
    } else if (linha.chegada_nao_confirmada) {
      vencidas += 1;
    } else {
      hoje += 1;
    }
  }
  return { hoje, hospedados, vencidas };
}

export function chegadaAdmiteBotao(status: string): boolean {
  return (
    status === "ficha_recebida" ||
    status === "ficha_parcial" ||
    status === "sem_cadastro_previo"
  );
}
