import { describe, expect, it } from "vitest";

import { contarSituacao, rotuloPerfil, type UsuarioLista } from "./usuarios";

describe("rotuloPerfil", () => {
  it("rótulo de negócio para os três perfis", () => {
    expect(rotuloPerfil("recepcao")).toBe("Recepção");
    expect(rotuloPerfil("staff")).toBe("Equipe");
    expect(rotuloPerfil("gestor")).toBe("Gestão");
  });
});

describe("contarSituacao", () => {
  it("devolve 0 e 0 em lista vazia", () => {
    expect(contarSituacao([])).toEqual({ ativos: 0, desativados: 0 });
  });

  it("separa ativos e desativados sem senha no tipo", () => {
    const lista: UsuarioLista[] = [
      { id_usuario: 1, nome: "Ana", email: "ana@hotel.example", perfil: "gestor", ativo: true },
      { id_usuario: 2, nome: "Beto", email: "beto@hotel.example", perfil: "staff", ativo: false },
      { id_usuario: 3, nome: "Cris", email: "cris@hotel.example", perfil: "recepcao", ativo: true },
    ];
    expect(contarSituacao(lista)).toEqual({ ativos: 2, desativados: 1 });
    expect(lista[0]).not.toHaveProperty("senha");
    expect(lista[0]).not.toHaveProperty("senha_hash");
  });
});
