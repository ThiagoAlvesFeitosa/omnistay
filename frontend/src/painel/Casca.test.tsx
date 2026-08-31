import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { definirManipulador401 } from "./sessao";
import { Casca } from "./Casca";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const sessaoRecepcionista = {
  id_sessao: 1,
  id_usuario: 1,
  nome: "Cleber Rocha",
  perfil: "recepcao",
  dispositivo: null,
  expira_em: "2026-09-01T00:00:00Z",
};

function fetchPorPerfil(perfil: string, nome = "Funcionário") {
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/sessoes/atual" && metodo === "GET") {
      return json({ ...sessaoRecepcionista, perfil, nome });
    }
    if (url === "/sessoes" && metodo === "POST") {
      return json({ id_usuario: 1, nome, perfil, expira_em: sessaoRecepcionista.expira_em }, 201);
    }
    if (url === "/sessoes/atual" && metodo === "DELETE") {
      return new Response(null, { status: 204 });
    }
    if (String(url).startsWith("/simulador")) {
      return json({ conversas: [] });
    }
    if (url === "/fila-do-dia" && metodo === "GET") {
      return json({ itens: [] });
    }
    if (url === "/solicitacoes" && metodo === "GET") {
      return json({ itens: [] });
    }
    if (url === "/reservas" && metodo === "POST") {
      return json(
        {
          id_reserva: 1,
          id_hotel: 1,
          nome: "Nova",
          telefone_contato: "5511999999999",
          data_checkin_prevista: "2026-08-31",
          data_checkout_prevista: "2026-09-02",
          status: "aguardando_cadastro",
        },
        201,
      );
    }
    return new Response(null, { status: 404 });
  });
}

function renderCasca(rota: string) {
  return render(
    <MemoryRouter basename="/app" initialEntries={[rota]}>
      <Casca />
    </MemoryRouter>,
  );
}

describe("Casca", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    definirManipulador401(null);
  });

  it.each([
    ["recepcao", "Fila do dia"],
    ["staff", "Meus chamados"],
    ["gestor", "Painel"],
  ] as const)("casa de %s mostra %s", async (perfil, titulo) => {
    vi.stubGlobal("fetch", fetchPorPerfil(perfil));
    renderCasca("/app/entrar");
    expect(await screen.findByRole("heading", { name: titulo })).toBeInTheDocument();
  });

  it("autenticado em /entrar não permanece na entrada", async () => {
    vi.stubGlobal("fetch", fetchPorPerfil("recepcao"));
    renderCasca("/app/entrar");
    expect(await screen.findByRole("heading", { name: "Fila do dia" })).toBeInTheDocument();
    expect(screen.queryByLabelText("E-mail")).not.toBeInTheDocument();
  });

  it("remount com sessão válida permanece na casa sem POST /sessoes", async () => {
    const fetchMock = fetchPorPerfil("recepcao");
    vi.stubGlobal("fetch", fetchMock);
    const { unmount } = renderCasca("/app/fila");
    expect(await screen.findByRole("heading", { name: "Fila do dia" })).toBeInTheDocument();
    unmount();
    renderCasca("/app/fila");
    expect(await screen.findByRole("heading", { name: "Fila do dia" })).toBeInTheDocument();
    const posts = fetchMock.mock.calls.filter(
      (chamada) => chamada[0] === "/sessoes" && (chamada[1]?.method ?? "GET") === "POST",
    );
    expect(posts).toHaveLength(0);
    expect(localStorage.getItem("omnistay_sessao")).toBeNull();
    expect(sessionStorage.getItem("token")).toBeNull();
  });

  it("Sair chama DELETE e volta à entrada", async () => {
    let autenticado = true;
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/sessoes/atual" && metodo === "GET") {
        if (!autenticado) {
          return json({ detail: "Sessao ausente ou invalida." }, 401);
        }
        return json(sessaoRecepcionista);
      }
      if (url === "/sessoes/atual" && metodo === "DELETE") {
        autenticado = false;
        return new Response(null, { status: 204 });
      }
      if (url === "/fila-do-dia" && metodo === "GET") {
        return json({ itens: [] });
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const { unmount } = renderCasca("/app/fila");
    expect(await screen.findByRole("heading", { name: "Fila do dia" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Sair" }));
    expect(await screen.findByLabelText("E-mail")).toBeInTheDocument();
    const deletes = fetchMock.mock.calls.filter(
      (chamada) => chamada[0] === "/sessoes/atual" && chamada[1]?.method === "DELETE",
    );
    expect(deletes).toHaveLength(1);
    expect(deletes[0][1]).toEqual(expect.objectContaining({ credentials: "include" }));
    unmount();
    renderCasca("/app/fila");
    expect(await screen.findByLabelText("E-mail")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Fila do dia" })).not.toBeInTheDocument();
  });

  it("menu da recepção omite meus chamados e painel, inclui simulador", async () => {
    vi.stubGlobal("fetch", fetchPorPerfil("recepcao"));
    renderCasca("/app/fila");
    expect(await screen.findByRole("link", { name: "Fila do dia" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Simulador" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Meus chamados" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Painel" })).not.toBeInTheDocument();
  });

  it("menu do staff não mostra simulador nem fila", async () => {
    vi.stubGlobal("fetch", fetchPorPerfil("staff"));
    renderCasca("/app/chamados");
    expect(await screen.findByRole("heading", { name: "Meus chamados" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Simulador" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Fila do dia" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Painel" })).not.toBeInTheDocument();
  });

  it("menu da gestão omite fila e meus chamados, inclui simulador", async () => {
    vi.stubGlobal("fetch", fetchPorPerfil("gestor"));
    renderCasca("/app/indicadores");
    expect(await screen.findByRole("heading", { name: "Painel" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Simulador" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Fila do dia" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Meus chamados" })).not.toBeInTheDocument();
  });

  it("recepção em /chamados não vê o título da equipe", async () => {
    vi.stubGlobal("fetch", fetchPorPerfil("recepcao"));
    renderCasca("/app/chamados");
    expect(await screen.findByRole("heading", { name: "Fila do dia" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Meus chamados" })).not.toBeInTheDocument();
  });

  it("recepção em /catalogo vê só o título Catálogo", async () => {
    vi.stubGlobal("fetch", fetchPorPerfil("recepcao"));
    renderCasca("/app/catalogo");
    expect(await screen.findByRole("heading", { name: "Catálogo" })).toBeInTheDocument();
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("simulador autenticado como recepção não pede e-mail", async () => {
    vi.stubGlobal("fetch", fetchPorPerfil("recepcao"));
    renderCasca("/app/simulador");
    expect(await screen.findByText(/simulador de conversa/i)).toBeInTheDocument();
    expect(screen.queryByLabelText("E-mail")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Senha")).not.toBeInTheDocument();
  });

  it("staff no simulador não vê o fio", async () => {
    vi.stubGlobal("fetch", fetchPorPerfil("staff"));
    renderCasca("/app/simulador");
    expect(await screen.findByRole("heading", { name: "Meus chamados" })).toBeInTheDocument();
    expect(screen.queryByText(/simulador de conversa/i)).not.toBeInTheDocument();
  });

  it("401 no meio do uso volta à entrada com aviso", async () => {
    let statusAtual = 200;
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (url === "/sessoes/atual" && metodo === "GET") {
        if (statusAtual === 401) {
          return json({ detail: "Sessao ausente ou invalida." }, 401);
        }
        return json(sessaoRecepcionista);
      }
      if (String(url).startsWith("/simulador")) {
        statusAtual = 401;
        await new Promise((resolver) => setTimeout(resolver, 30));
        return json({ detail: "Sessao ausente ou invalida." }, 401);
      }
      if (url === "/fila-do-dia") {
        return json({ itens: [] });
      }
      return new Response(null, { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    renderCasca("/app/simulador");
    expect(await screen.findByText(/simulador de conversa/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("E-mail")).toBeInTheDocument());
    expect(screen.getByText("Sessão ausente ou inválida.")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Fila do dia" })).not.toBeInTheDocument();
  });

  it("staff e gestão em /ficha não vêem a ficha nem disparam GET", async () => {
    for (const perfil of ["staff", "gestor"] as const) {
      const fetchMock = fetchPorPerfil(perfil);
      vi.stubGlobal("fetch", fetchMock);
      const casa = perfil === "staff" ? "Meus chamados" : "Painel";

      for (const rota of ["/app/ficha", "/app/ficha/1"]) {
        const visao = renderCasca(rota);
        expect(await screen.findByRole("heading", { name: casa })).toBeInTheDocument();
        expect(screen.queryByRole("heading", { name: "Ficha do hóspede" })).not.toBeInTheDocument();
        expect(screen.queryByText("Marina Duarte")).not.toBeInTheDocument();
        const ficha = fetchMock.mock.calls.filter(
          (chamada) =>
            String(chamada[0]).includes("/ficha") ||
            String(chamada[0]).includes("/consentimento"),
        );
        expect(ficha).toHaveLength(0);
        visao.unmount();
      }
    }
  });

  it("staff em /alertas não monta Chamados e pedidos nem busca a lista da recepção", async () => {
    const fetchMock = fetchPorPerfil("staff");
    vi.stubGlobal("fetch", fetchMock);
    renderCasca("/app/alertas");
    expect(await screen.findByRole("heading", { name: "Meus chamados" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Chamados e pedidos" })).not.toBeInTheDocument();
    const gets = fetchMock.mock.calls.filter(
      (chamada) => chamada[0] === "/solicitacoes" && (chamada[1]?.method ?? "GET") === "GET",
    );
    expect(gets).toHaveLength(1);
  });

  it("staff recarrega Meus chamados compacto sem pedir senha", async () => {
    vi.stubGlobal("fetch", fetchPorPerfil("staff"));
    renderCasca("/app/chamados");
    expect(await screen.findByRole("heading", { name: "Meus chamados" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sair" })).toBeInTheDocument();
    expect(screen.queryByLabelText("E-mail")).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Fila do dia" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Chamados e pedidos" })).not.toBeInTheDocument();
  });

  it("gestão em /alertas e /chamados não opera as listas", async () => {
    for (const rota of ["/app/alertas", "/app/chamados"]) {
      const fetchMock = fetchPorPerfil("gestor");
      vi.stubGlobal("fetch", fetchMock);
      const visao = renderCasca(rota);
      expect(await screen.findByRole("heading", { name: "Painel" })).toBeInTheDocument();
      expect(screen.queryByRole("heading", { name: "Chamados e pedidos" })).not.toBeInTheDocument();
      expect(screen.queryByRole("heading", { name: "Meus chamados" })).not.toBeInTheDocument();
      const gets = fetchMock.mock.calls.filter(
        (chamada) => chamada[0] === "/solicitacoes" && (chamada[1]?.method ?? "GET") === "GET",
      );
      expect(gets).toHaveLength(0);
      visao.unmount();
    }
  });

  it("staff e gestão em fila ou reserva não disparam GET da lista nem POST", async () => {
    for (const perfil of ["staff", "gestor"] as const) {
      const fetchMock = fetchPorPerfil(perfil);
      vi.stubGlobal("fetch", fetchMock);
      const casa = perfil === "staff" ? "Meus chamados" : "Painel";

      const fila = renderCasca("/app/fila");
      expect(await screen.findByRole("heading", { name: casa })).toBeInTheDocument();
      expect(screen.queryByText("Marina Duarte")).not.toBeInTheDocument();
      fila.unmount();

      const reserva = renderCasca("/app/reserva");
      expect(await screen.findByRole("heading", { name: casa })).toBeInTheDocument();
      expect(screen.queryByLabelText("Nome do hóspede")).not.toBeInTheDocument();
      const operacionais = fetchMock.mock.calls.filter(
        (chamada) =>
          chamada[0] === "/fila-do-dia" ||
          (chamada[0] === "/reservas" && chamada[1]?.method === "POST"),
      );
      expect(operacionais).toHaveLength(0);
      reserva.unmount();
    }
  });
});
