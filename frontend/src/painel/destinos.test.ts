import { describe, expect, it } from "vitest";

import { destinoInicial, itensMenu } from "./destinos";

describe("destinoInicial", () => {
  it("leva recepção à fila do dia", () => {
    expect(destinoInicial("recepcao")).toBe("/app/fila");
  });

  it("leva staff a meus chamados", () => {
    expect(destinoInicial("staff")).toBe("/app/chamados");
  });

  it("leva gestão ao painel", () => {
    expect(destinoInicial("gestor")).toBe("/app/indicadores");
  });
});

describe("itensMenu", () => {
  function ids(perfil: "recepcao" | "staff" | "gestor"): string[] {
    return itensMenu(perfil).map((item) => item.id);
  }

  it("recepção vê fila e simulador, não meus chamados nem painel", () => {
    const visiveis = ids("recepcao");
    expect(visiveis).toContain("fila");
    expect(visiveis).toContain("simulador");
    expect(visiveis).not.toContain("chamados");
    expect(visiveis).not.toContain("indicadores");
  });

  it("staff vê só meus chamados", () => {
    expect(ids("staff")).toEqual(["chamados"]);
  });

  it("gestão vê painel e simulador, não fila nem meus chamados", () => {
    const visiveis = ids("gestor");
    expect(visiveis).toContain("indicadores");
    expect(visiveis).toContain("simulador");
    expect(visiveis).not.toContain("fila");
    expect(visiveis).not.toContain("chamados");
  });
});
