import { beforeEach, describe, expect, it, vi } from "vitest";

import { entrar, obterAtual, sair } from "./sessao";

function respostaJson(corpo: unknown, status: number): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("sessao", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it("entrar faz POST /sessoes com credentials include e não grava token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      respostaJson(
        {
          id_usuario: 1,
          nome: "Cleber",
          perfil: "recepcao",
          expira_em: "2026-09-01T00:00:00Z",
        },
        201,
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await entrar("cleber@hotel.com", "segredo");

    expect(fetchMock).toHaveBeenCalledWith(
      "/sessoes",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: "cleber@hotel.com", senha: "segredo" }),
      }),
    );
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
    const corpo = String(fetchMock.mock.calls[0][1].body);
    expect(corpo).not.toMatch(/token/);
  });

  it("obterAtual faz GET /sessoes/atual com credentials include", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      respostaJson(
        {
          id_sessao: 1,
          id_usuario: 1,
          nome: "Cleber",
          perfil: "recepcao",
          dispositivo: null,
          expira_em: "2026-09-01T00:00:00Z",
        },
        200,
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await obterAtual();

    expect(fetchMock).toHaveBeenCalledWith(
      "/sessoes/atual",
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("sair faz DELETE /sessoes/atual", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await sair();

    expect(fetchMock).toHaveBeenCalledWith(
      "/sessoes/atual",
      expect.objectContaining({
        method: "DELETE",
        credentials: "include",
      }),
    );
  });
});
