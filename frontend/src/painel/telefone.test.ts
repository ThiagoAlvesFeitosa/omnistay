import { describe, expect, it } from "vitest";

import { TelefoneInvalido, normalizar } from "./telefone";

describe("normalizar telefone", () => {
  it("aceita máscara nacional e dígitos", () => {
    expect(normalizar("(11) 98765-4321")).toBe("5511987654321");
    expect(normalizar("11987654321")).toBe("5511987654321");
  });

  it("recusa número curto e estrangeiro", () => {
    expect(() => normalizar("123")).toThrow(TelefoneInvalido);
    expect(() => normalizar("123")).toThrow(/brasileiro com DDD/);
    expect(() => normalizar("447911123456")).toThrow(TelefoneInvalido);
  });
});
