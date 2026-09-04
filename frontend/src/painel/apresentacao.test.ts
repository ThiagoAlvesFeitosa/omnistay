import { describe, expect, it } from "vitest";

import {
  formatarDataCalendario,
  formatarHorarioBolha,
  formatarInstante,
  formatarInstanteComDecorrido,
  formatarMoeda,
} from "./apresentacao";

describe("formatarMoeda", () => {
  it("nove reais com cifrão e vírgula", () => {
    expect(formatarMoeda(9)).toBe("R$ 9,00");
  });

  it("zero é R$ 0,00", () => {
    expect(formatarMoeda(0)).toBe("R$ 0,00");
  });

  it("milhar com ponto", () => {
    expect(formatarMoeda(1320)).toBe("R$ 1.320,00");
  });
});

describe("formatarDataCalendario", () => {
  it("ISO só dia vira dia/mês/ano", () => {
    expect(formatarDataCalendario("2026-09-02")).toBe("02/09/2026");
  });

  it("ilegível não inventa dia", () => {
    expect(formatarDataCalendario("")).toBe("");
    expect(formatarDataCalendario("ontem")).toBe("");
  });
});

describe("formatarInstante", () => {
  it("mostra data e hora:minuto sem segundos", () => {
    const parede = new Date(2026, 8, 2, 14, 32, 45);
    expect(formatarInstante(parede)).toBe("02/09/2026 14:32");
  });
});

describe("formatarInstanteComDecorrido", () => {
  it("instante absoluto e relativo juntos", () => {
    const aberto = new Date(2026, 8, 2, 14, 32, 0);
    const agora = new Date(2026, 8, 2, 14, 40, 0);
    expect(formatarInstanteComDecorrido(aberto, agora)).toBe("02/09/2026 14:32 · há 8 min");
  });
});

describe("formatarHorarioBolha", () => {
  const agora = new Date(2026, 8, 2, 18, 0, 0);

  it("mesmo dia de calendário mostra só a hora", () => {
    const hoje = new Date(2026, 8, 2, 14, 32, 0);
    expect(formatarHorarioBolha(hoje, agora)).toBe("14:32");
  });

  it("outro dia mostra data e hora", () => {
    const outro = new Date(2026, 8, 1, 14, 32, 0);
    expect(formatarHorarioBolha(outro, agora)).toBe("01/09/2026 14:32");
  });

  it("não usa o relativo de urgência", () => {
    const hoje = new Date(2026, 8, 2, 14, 32, 0);
    expect(formatarHorarioBolha(hoje, agora)).not.toMatch(/há /);
  });
});
