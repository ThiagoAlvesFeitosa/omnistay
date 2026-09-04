import { describe, expect, it } from "vitest";

import { formatarPreco, type ItemVendavel } from "./vendaveis";

describe("ItemVendavel", () => {
  it("não tem campo descrição", () => {
    const item: ItemVendavel = {
      id_item_vendavel: 1,
      nome: "Água",
      preco_atual: "9.00",
      ativo: true,
    };
    expect("descricao" in item).toBe(false);
    expect(JSON.stringify(item)).not.toMatch(/descri/i);
  });
});

describe("formatarPreco", () => {
  it("na leitura delega a formatarMoeda", () => {
    expect(formatarPreco(9)).toBe("R$ 9,00");
    expect(formatarPreco("32.5")).toBe("R$ 32,50");
    expect(formatarPreco("28.00")).toBe("R$ 28,00");
  });
});
