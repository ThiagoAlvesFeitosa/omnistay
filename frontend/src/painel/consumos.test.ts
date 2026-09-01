import { describe, expect, it } from "vitest";

import { tempoDecorrido } from "./solicitacoes";
import { pendentesDaEstadia, tempoDoMaisAntigo, totalPendente, type ItemConsumoPendente } from "./consumos";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

function item(parcial: Partial<ItemConsumoPendente> & { id_solicitacao: number }): ItemConsumoPendente {
  return {
    id_reserva: 10,
    descricao: "pedido",
    descricao_item: "Lavanderia",
    numero_quarto: "210",
    valor_praticado: "32.00",
    status_lancamento: "pendente",
    aberta_em: "2026-08-29T15:00:00.000Z",
    resolvida_em: null,
    ...parcial,
  };
}

describe("totalPendente", () => {
  it("soma número e string e zera lista vazia", () => {
    expect(totalPendente([])).toBe(0);
    expect(
      totalPendente([
        item({ id_solicitacao: 1, valor_praticado: "32.00" }),
        item({ id_solicitacao: 2, valor_praticado: 56 }),
      ]),
    ).toBe(88);
  });
});

describe("pendentesDaEstadia", () => {
  it("devolve só os da reserva pedida", () => {
    const lista = [
      item({ id_solicitacao: 1, id_reserva: 42 }),
      item({ id_solicitacao: 2, id_reserva: 7 }),
      item({ id_solicitacao: 3, id_reserva: 42 }),
    ];
    expect(pendentesDaEstadia(lista, 42).map((linha) => linha.id_solicitacao)).toEqual([1, 3]);
    expect(pendentesDaEstadia(lista, 99)).toEqual([]);
  });
});

describe("tempoDoMaisAntigo", () => {
  const agora = new Date("2026-08-31T15:00:00.000Z");

  it("usa o primeiro item já ordenado", () => {
    const lista = [
      item({ id_solicitacao: 1, aberta_em: "2026-08-29T15:00:00.000Z" }),
      item({ id_solicitacao: 2, aberta_em: "2026-08-31T12:00:00.000Z" }),
    ];
    expect(tempoDoMaisAntigo(lista, agora)).toBe(tempoDecorrido(lista[0].aberta_em, agora));
  });

  it("lista vazia não inventa tempo", () => {
    expect(tempoDoMaisAntigo([], agora)).toBe("");
  });
});

describe("nomenclatura", () => {
  it("o módulo não usa extrato nem conta", () => {
    const fonte = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "consumos.ts"), "utf8");
    expect(fonte.toLowerCase()).not.toMatch(/extrato|conta/);
  });
});
