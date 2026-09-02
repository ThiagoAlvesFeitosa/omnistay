import { describe, expect, it } from "vitest";

import { chegadaAdmiteBotao, resumirTurno, saidaAdmiteCaminho, type ItemFila } from "./fila";

function item(parcial: Partial<ItemFila> & { id_reserva: number }): ItemFila {
  return {
    nome: "Hóspede",
    telefone_contato: "5511999999999",
    data_checkin_prevista: "2026-08-31",
    data_checkout_prevista: "2026-09-02",
    status: "aguardando_cadastro",
    estado_cadastro: "aguardando",
    chegada_nao_confirmada: false,
    boas_vindas_nao_enviadas: false,
    precisa_atendimento_humano: false,
    saida_nao_confirmada: false,
    ...parcial,
  };
}

describe("resumirTurno", () => {
  it("lista vazia zera as três contas", () => {
    expect(resumirTurno([])).toEqual({ hoje: 0, hospedados: 0, vencidas: 0 });
  });

  it("hospedado conta só em hospedados", () => {
    const lista = [item({ id_reserva: 1, status: "hospedado", estado_cadastro: "completa" })];
    expect(resumirTurno(lista)).toEqual({ hoje: 0, hospedados: 1, vencidas: 0 });
  });

  it("entrada vencida conta só em vencidas", () => {
    const lista = [
      item({
        id_reserva: 2,
        status: "ficha_recebida",
        chegada_nao_confirmada: true,
        estado_cadastro: "completa",
      }),
    ];
    expect(resumirTurno(lista)).toEqual({ hoje: 0, hospedados: 0, vencidas: 1 });
  });

  it("não hospedado e não vencido conta só em hoje", () => {
    const lista = [item({ id_reserva: 3, status: "aguardando_cadastro" })];
    expect(resumirTurno(lista)).toEqual({ hoje: 1, hospedados: 0, vencidas: 0 });
  });

  it("a soma das três é o número de linhas", () => {
    const lista = [
      item({ id_reserva: 1, status: "aguardando_cadastro" }),
      item({
        id_reserva: 2,
        status: "ficha_parcial",
        chegada_nao_confirmada: true,
        estado_cadastro: "parcial",
      }),
      item({ id_reserva: 3, status: "hospedado", estado_cadastro: "completa" }),
    ];
    const resumo = resumirTurno(lista);
    expect(resumo.hoje + resumo.hospedados + resumo.vencidas).toBe(lista.length);
    expect(resumo).toEqual({ hoje: 1, hospedados: 1, vencidas: 1 });
  });

  it("hospedado com recado não enviado continua em hospedados", () => {
    const lista = [
      item({
        id_reserva: 4,
        status: "hospedado",
        estado_cadastro: "completa",
        boas_vindas_nao_enviadas: true,
      }),
    ];
    expect(resumirTurno(lista)).toEqual({ hoje: 0, hospedados: 1, vencidas: 0 });
  });
});

describe("saidaAdmiteCaminho", () => {
  it("admite só em hospedado", () => {
    expect(saidaAdmiteCaminho("hospedado")).toBe(true);
  });

  it.each(["ficha_recebida", "ficha_parcial", "aguardando_cadastro", "encerrado"] as const)(
    "recusa em %s",
    (status) => {
      expect(saidaAdmiteCaminho(status)).toBe(false);
    },
  );
});

describe("resumirTurno não ganha quarta conta", () => {
  it("hospedado com saída não confirmada continua só nas três partições", () => {
    const lista = [
      item({
        id_reserva: 5,
        status: "hospedado",
        estado_cadastro: "completa",
        saida_nao_confirmada: true,
      }),
    ];
    expect(resumirTurno(lista)).toEqual({ hoje: 0, hospedados: 1, vencidas: 0 });
    expect(Object.keys(resumirTurno(lista))).toEqual(["hoje", "hospedados", "vencidas"]);
  });
});

describe("chegadaAdmiteBotao", () => {
  it.each(["ficha_recebida", "ficha_parcial", "sem_cadastro_previo"] as const)(
    "admite em %s",
    (status) => {
      expect(chegadaAdmiteBotao(status)).toBe(true);
    },
  );

  it.each(["aguardando_cadastro", "hospedado", "encerrado", "cancelada"] as const)(
    "recusa em %s",
    (status) => {
      expect(chegadaAdmiteBotao(status)).toBe(false);
    },
  );
});
