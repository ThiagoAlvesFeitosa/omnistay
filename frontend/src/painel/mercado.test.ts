import { describe, expect, it } from "vitest";

import {
  linhaAtual,
  linhaComFalha,
  semColeta,
  temPrecoEncontrado,
  type ItemMercado,
} from "./mercado";

function item(parcial: Partial<ItemMercado> & { id_concorrente: number }): ItemMercado {
  return {
    nome: "Hotel Vizinho",
    ativo: true,
    situacao: "atual",
    ultimo_sucesso: {
      preco: 180,
      nota_media: 8.5,
      coletado_em: "2026-09-01T10:00:00Z",
    },
    ultima_falha: null,
    ...parcial,
  };
}

describe("marcas da linha de mercado", () => {
  it("linhaComFalha é verdadeiro para so_falha e para ultima_falha presente", () => {
    expect(
      linhaComFalha(
        item({
          id_concorrente: 1,
          situacao: "so_falha",
          ultimo_sucesso: null,
          ultima_falha: { coletado_em: "2026-09-01T08:00:00Z" },
        }),
      ),
    ).toBe(true);
    expect(
      linhaComFalha(
        item({
          id_concorrente: 2,
          situacao: "desatualizado",
          ultima_falha: { coletado_em: "2026-09-01T12:00:00Z" },
        }),
      ),
    ).toBe(true);
    expect(linhaComFalha(item({ id_concorrente: 3, situacao: "atual" }))).toBe(false);
  });

  it("linhaAtual só quando situacao é atual", () => {
    expect(linhaAtual(item({ id_concorrente: 1, situacao: "atual" }))).toBe(true);
    expect(linhaAtual(item({ id_concorrente: 2, situacao: "desatualizado" }))).toBe(false);
    expect(
      linhaAtual(
        item({
          id_concorrente: 3,
          situacao: "so_falha",
          ultimo_sucesso: null,
          ultima_falha: { coletado_em: "2026-09-01T08:00:00Z" },
        }),
      ),
    ).toBe(false);
  });

  it("semColeta só para sem_coleta", () => {
    expect(
      semColeta(item({ id_concorrente: 1, situacao: "sem_coleta", ultimo_sucesso: null })),
    ).toBe(true);
    expect(semColeta(item({ id_concorrente: 2, situacao: "atual" }))).toBe(false);
  });

  it("preço zero de sucesso não é tratado como vazio", () => {
    const zero = item({
      id_concorrente: 1,
      ultimo_sucesso: { preco: 0, nota_media: null, coletado_em: "2026-09-01T10:00:00Z" },
    });
    expect(temPrecoEncontrado(zero)).toBe(true);
    expect(
      temPrecoEncontrado(item({ id_concorrente: 2, situacao: "sem_coleta", ultimo_sucesso: null })),
    ).toBe(false);
  });
});
