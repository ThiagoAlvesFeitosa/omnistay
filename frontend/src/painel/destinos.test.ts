import { describe, expect, it } from "vitest";

import { DESTINOS, destinoPorCaminho, perfilPode } from "./destinos";

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
