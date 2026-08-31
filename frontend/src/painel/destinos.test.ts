import { describe, expect, it } from "vitest";

import { destinoPorCaminho, perfilPode } from "./destinos";

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
});
