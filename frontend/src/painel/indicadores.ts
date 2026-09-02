export const CAMPOS_INDICADORES = [
  "chegadas_hoje",
  "hospedados",
  "chamados_abertos",
  "consumo_a_lancar",
] as const;

export type IndicadoresOperacao = {
  chegadas_hoje: number;
  hospedados: number;
  chamados_abertos: number;
  consumo_a_lancar: number;
};
