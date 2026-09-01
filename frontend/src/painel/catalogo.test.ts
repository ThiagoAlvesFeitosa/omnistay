import { describe, expect, it } from "vitest";

import {
  CATEGORIAS,
  contarSituacao,
  itensDaCategoria,
  type ItemCatalogo,
} from "./catalogo";

function item(parcial: Partial<ItemCatalogo> & { id_catalogo_item: number }): ItemCatalogo {
  return {
    categoria: "horario",
    titulo: "Café",
    conteudo: "Das 7h às 10h",
    ativo: true,
    ...parcial,
  };
}

describe("categorias do catálogo", () => {
  it("tem as cinco chaves com rótulos de negócio", () => {
    expect(CATEGORIAS.map((c) => c.chave)).toEqual([
      "horario",
      "cardapio",
      "servico",
      "programacao",
      "regra",
    ]);
    expect(CATEGORIAS.map((c) => c.rotulo)).toEqual([
      "Horários",
      "Cardápio",
      "Serviços",
      "Programação",
      "Regras",
    ]);
  });
});

describe("itensDaCategoria", () => {
  it("devolve só a chave pedida, na ordem do array, sem reordenar", () => {
    const itens = [
      item({ id_catalogo_item: 2, categoria: "cardapio", titulo: "Segundo" }),
      item({ id_catalogo_item: 1, categoria: "horario", titulo: "Horário" }),
      item({ id_catalogo_item: 3, categoria: "cardapio", titulo: "Terceiro" }),
    ];
    const daAba = itensDaCategoria(itens, "cardapio");
    expect(daAba.map((i) => i.id_catalogo_item)).toEqual([2, 3]);
    expect(daAba.map((i) => i.titulo)).toEqual(["Segundo", "Terceiro"]);
  });
});

describe("contarSituacao", () => {
  it("conta ativos e desativados do recorte, zero em lista vazia", () => {
    expect(contarSituacao([])).toEqual({ ativos: 0, desativados: 0 });
    expect(
      contarSituacao([
        item({ id_catalogo_item: 1, ativo: true }),
        item({ id_catalogo_item: 2, ativo: false }),
        item({ id_catalogo_item: 3, ativo: true }),
      ]),
    ).toEqual({ ativos: 2, desativados: 1 });
  });
});
