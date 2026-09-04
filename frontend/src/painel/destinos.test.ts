import { describe, expect, it } from "vitest";

import { DESTINOS, destinoPorCaminho, itensMenu, menuAgrupado, perfilPode } from "./destinos";

describe("destinoPorCaminho da ficha", () => {
  it.each(["/app/ficha", "/app/ficha/12", "/ficha/12"] as const)(
    "trata %s como destino ficha",
    (caminho) => {
      const destino = destinoPorCaminho(caminho);
      expect(destino?.id).toBe("ficha");
    },
  );

  it("recepção pode a ficha com e sem id", () => {
    expect(perfilPode("recepcao", "/app/ficha")).toBe(true);
    expect(perfilPode("recepcao", "/ficha/12")).toBe(true);
  });

  it("staff e gestão não podem a ficha com id", () => {
    expect(perfilPode("staff", "/app/ficha/12")).toBe(false);
    expect(perfilPode("gestor", "/ficha/1")).toBe(false);
  });

  it("destino ficha chama-se Estadia e o path permanece /app/ficha", () => {
    const destino = DESTINOS.find((item) => item.id === "ficha");
    expect(destino?.titulo).toBe("Estadia");
    expect(destino?.caminho).toBe("/app/ficha");
  });
});

describe("destinoPorCaminho da saída", () => {
  it.each(["/app/saida", "/app/saida/12", "/saida/12"] as const)(
    "trata %s como destino saida",
    (caminho) => {
      const destino = destinoPorCaminho(caminho);
      expect(destino?.id).toBe("saida");
    },
  );

  it("recepção pode a saída com e sem id", () => {
    expect(perfilPode("recepcao", "/app/saida")).toBe(true);
    expect(perfilPode("recepcao", "/saida/12")).toBe(true);
  });

  it("staff e gestão não podem a saída com id", () => {
    expect(perfilPode("staff", "/app/saida/12")).toBe(false);
    expect(perfilPode("gestor", "/saida/1")).toBe(false);
  });
});

describe("catálogo, vendáveis e recado por perfil", () => {
  it.each(["/app/catalogo", "/app/vendaveis", "/app/boas-vindas"] as const)(
    "recepção e gestão podem %s; staff não",
    (caminho) => {
      expect(perfilPode("recepcao", caminho)).toBe(true);
      expect(perfilPode("gestor", caminho)).toBe(true);
      expect(perfilPode("staff", caminho)).toBe(false);
    },
  );
});

describe("painel da gestão", () => {
  it.each(["/app/indicadores", "/app/mercado", "/app/usuarios", "/app/retencao"] as const)(
    "só a gestão pode %s",
    (caminho) => {
      expect(perfilPode("gestor", caminho)).toBe(true);
      expect(perfilPode("recepcao", caminho)).toBe(false);
      expect(perfilPode("staff", caminho)).toBe(false);
    },
  );
});

describe("menu por área", () => {
  it("recepção não vê Nova reserva no menu e a rota continua no mapa", () => {
    expect(itensMenu("recepcao").some((item) => item.id === "reserva")).toBe(false);
    expect(DESTINOS.some((item) => item.id === "reserva")).toBe(true);
  });

  it("recepção agrupa Operação, Propriedade e Simulador no fim", () => {
    const grupos = menuAgrupado("recepcao");
    expect(grupos.map((grupo) => grupo.rotulo)).toEqual(["Operação", "Propriedade"]);
    expect(grupos[0].itens.map((item) => item.id)).toEqual([
      "fila",
      "ficha",
      "alertas",
      "consumos",
      "saida",
    ]);
    expect(grupos[1].itens.map((item) => item.id)).toEqual([
      "catalogo",
      "vendaveis",
      "boas-vindas",
    ]);
    expect(itensMenu("recepcao").at(-1)?.id).toBe("simulador");
  });

  it("gestão não tem grupo Operação", () => {
    const grupos = menuAgrupado("gestor");
    expect(grupos.map((grupo) => grupo.rotulo)).toEqual(["Propriedade", "Gestão"]);
    expect(grupos.some((grupo) => grupo.rotulo === "Operação")).toBe(false);
  });

  it("equipe só tem Operação com meus chamados", () => {
    const grupos = menuAgrupado("staff");
    expect(grupos).toHaveLength(1);
    expect(grupos[0].rotulo).toBe("Operação");
    expect(grupos[0].itens.map((item) => item.id)).toEqual(["chamados"]);
  });
});
