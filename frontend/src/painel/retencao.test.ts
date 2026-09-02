import { describe, expect, it } from "vitest";

import { prazoVisivel } from "./retencao";

describe("prazoVisivel", () => {
  it("null não vira 12 nem 5", () => {
    const visivel = prazoVisivel(null);
    expect(visivel).not.toBe("12");
    expect(visivel).not.toBe("5");
    expect(visivel).not.toBe(12);
    expect(visivel).not.toBe(5);
  });

  it("inteiro ≥ 1 aparece como número", () => {
    expect(prazoVisivel(12)).toBe("12");
    expect(prazoVisivel(5)).toBe("5");
    expect(prazoVisivel(1)).toBe("1");
  });
});
