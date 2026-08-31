import { describe, expect, it } from "vitest";

import { rotuloNatureza, tempoDecorrido } from "./solicitacoes";

describe("rotuloNatureza", () => {
  it("distingue reclamação, serviço e consumo", () => {
    expect(rotuloNatureza("reclamacao")).toBe("reclamação");
    expect(rotuloNatureza("servico")).toBe("serviço");
    expect(rotuloNatureza("consumo")).toBe("consumo");
    expect(new Set(["reclamacao", "servico", "consumo"].map(rotuloNatureza)).size).toBe(3);
  });

  it("valor desconhecido não empresta rótulo de outra natureza", () => {
    const rotulo = rotuloNatureza("outro");
    expect(rotulo).not.toBe("reclamação");
    expect(rotulo).not.toBe("serviço");
    expect(rotulo).not.toBe("consumo");
  });
});

describe("tempoDecorrido", () => {
  const agora = new Date("2026-08-31T15:00:00.000Z");

  it("menos de um minuto fala em menos de 1 min", () => {
    const aberto = new Date("2026-08-31T14:59:30.000Z").toISOString();
    expect(tempoDecorrido(aberto, agora)).toMatch(/menos de 1 min/i);
  });

  it("minutos, horas e dias usam a unidade certa", () => {
    expect(tempoDecorrido(new Date("2026-08-31T14:57:00.000Z").toISOString(), agora)).toMatch(/3.*min/i);
    expect(tempoDecorrido(new Date("2026-08-31T12:00:00.000Z").toISOString(), agora)).toMatch(/3.*h/i);
    expect(tempoDecorrido(new Date("2026-08-29T15:00:00.000Z").toISOString(), agora)).toMatch(/2.*d/i);
  });

  it("não usa extrato nem conta", () => {
    const texto = tempoDecorrido(new Date("2026-08-31T14:00:00.000Z").toISOString(), agora);
    expect(texto.toLowerCase()).not.toMatch(/extrato|conta/);
  });
});
