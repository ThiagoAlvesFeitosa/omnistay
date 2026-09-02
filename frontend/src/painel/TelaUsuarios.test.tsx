import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelaUsuarios } from "./TelaUsuarios";
import type { UsuarioLista } from "./usuarios";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function usuario(parcial: Partial<UsuarioLista> & { id_usuario: number }): UsuarioLista {
  return {
    nome: "Funcionário",
    email: `user${parcial.id_usuario}@hotel.example`,
    perfil: "staff",
    ativo: true,
    ...parcial,
  };
}

function fetchUsuarios(
  iniciais: UsuarioLista[],
  extras?: (url: string, init?: RequestInit) => Response | null,
) {
  let lista = [...iniciais];
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const extra = extras?.(url, init);
    if (extra) {
      return extra;
    }
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/usuarios" && metodo === "GET") {
      return json({ usuarios: lista });
    }
    if (url === "/usuarios" && metodo === "POST") {
      const corpo = JSON.parse(String(init?.body ?? "{}")) as Record<string, string>;
      if ((corpo.senha ?? "").length < 12) {
        return json({ detail: "Senha precisa ter ao menos 12 caracteres" }, 422);
      }
      if (lista.some((item) => item.email === corpo.email)) {
        return json({ detail: "Email ja cadastrado." }, 409);
      }
      const criado = usuario({
        id_usuario: 99,
        nome: corpo.nome,
        email: corpo.email,
        perfil: corpo.perfil as UsuarioLista["perfil"],
        ativo: true,
      });
      lista = [...lista, criado];
      return json(criado, 201);
    }
    if (metodo === "DELETE" && /^\/usuarios\/\d+$/.test(url)) {
      const id = Number(url.split("/").pop());
      lista = lista.map((item) => (item.id_usuario === id ? { ...item, ativo: false } : item));
      return new Response(null, { status: 204 });
    }
    return new Response(null, { status: 404 });
  });
}

function renderUsuarios() {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/usuarios"]}>
      <TelaUsuarios idUsuarioSessao={1} />
    </MemoryRouter>,
  );
}

describe("TelaUsuarios", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("lista colunas, esconde Desativar na própria linha e não reativa", async () => {
    const fetchMock = fetchUsuarios([
      usuario({ id_usuario: 1, nome: "Thiago", email: "thiago@hotel.example", perfil: "gestor" }),
      usuario({ id_usuario: 2, nome: "Bia", email: "bia@hotel.example", perfil: "recepcao" }),
      usuario({
        id_usuario: 3,
        nome: "Caio",
        email: "caio@hotel.example",
        perfil: "staff",
        ativo: false,
      }),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    renderUsuarios();

    expect(await screen.findByRole("heading", { name: "Usuários" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/usuarios",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(screen.getByText("Thiago")).toBeInTheDocument();
    expect(screen.getByText("thiago@hotel.example")).toBeInTheDocument();
    expect(screen.getByText("Gestão")).toBeInTheDocument();
    expect(screen.getByText("você")).toBeInTheDocument();
    expect(screen.getByText("Bia")).toBeInTheDocument();
    expect(screen.getByText("Recepção")).toBeInTheDocument();
    expect(screen.getByText("Caio")).toBeInTheDocument();
    expect(screen.getByText("Desativado")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reativar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Desativar Thiago" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Desativar Bia" })).toBeInTheDocument();

    const sessoes = fetchMock.mock.calls.filter((chamada) => String(chamada[0]).startsWith("/sessoes"));
    expect(sessoes).toHaveLength(0);
    const patches = fetchMock.mock.calls.filter(
      (chamada) => (chamada[1]?.method ?? "GET").toUpperCase() === "PATCH",
    );
    expect(patches).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Desativar Bia" }));
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: "Desativar Bia" })).not.toBeInTheDocument();
    });
    const deletes = fetchMock.mock.calls.filter(
      (chamada) => chamada[0] === "/usuarios/2" && chamada[1]?.method === "DELETE",
    );
    expect(deletes).toHaveLength(1);
    const gets = fetchMock.mock.calls.filter(
      (chamada) => chamada[0] === "/usuarios" && (chamada[1]?.method ?? "GET") === "GET",
    );
    expect(gets.length).toBeGreaterThanOrEqual(2);
  });

  it("cria com POST e mostra 409 e 422", async () => {
    const fetchMock = fetchUsuarios([
      usuario({ id_usuario: 1, nome: "Thiago", email: "thiago@hotel.example", perfil: "gestor" }),
    ]);
    vi.stubGlobal("fetch", fetchMock);
    renderUsuarios();
    expect(await screen.findByText("Thiago")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "+ Novo" }));
    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Novo" } });
    fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "thiago@hotel.example" } });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "senha-nova-1234" } });
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
    expect(await screen.findByText("Email ja cadastrado.")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "novo@hotel.example" } });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "curta" } });
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
    expect(await screen.findByText(/12 caracteres/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "senha-nova-1234" } });
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
    expect(await screen.findByText("novo@hotel.example")).toBeInTheDocument();
    const posts = fetchMock.mock.calls.filter(
      (chamada) => chamada[0] === "/usuarios" && chamada[1]?.method === "POST",
    );
    expect(posts.length).toBeGreaterThanOrEqual(1);
    expect(JSON.parse(String(posts[posts.length - 1][1]?.body))).toEqual(
      expect.objectContaining({
        nome: "Novo",
        email: "novo@hotel.example",
        senha: "senha-nova-1234",
      }),
    );
  });
});
