import { describe, expect, it } from "vitest";

import { CAMPOS_INDICADORES, type IndicadoresOperacao } from "./indicadores";

describe("IndicadoresOperacao", () => {
  it("aceita os quatro campos, inclusive zeros", () => {
    const zeros: IndicadoresOperacao = {
      chegadas_hoje: 0,
      hospedados: 0,
      chamados_abertos: 0,
      consumo_a_lancar: 0,
    };
    expect([...CAMPOS_INDICADORES].sort()).toEqual(
      ["chamados_abertos", "chegadas_hoje", "consumo_a_lancar", "hospedados"].sort(),
    );
    expect(Object.keys(zeros).sort()).toEqual([...CAMPOS_INDICADORES].sort());
    expect(zeros).not.toHaveProperty("itens");
    expect(zeros).not.toHaveProperty("id_reserva");
    expect(zeros).not.toHaveProperty("nome");
    expect(zeros).not.toHaveProperty("telefone");
  });
});
