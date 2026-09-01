import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TelaBoasVindas } from "./TelaBoasVindas";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const recado = {
  cafe: "das 7h às 10h no salão",
  wifi: "rede Hotel, senha na recepção",
  checkout: "12h",
  convite: "Quer saber dos serviços? Pergunte por aqui.",
};

function fetchRecado(
  inicial: typeof recado | "erro" = recado,
  extras?: (url: string, init?: RequestInit) => Response | null,
) {
  let atual = inicial === "erro" ? recado : { ...inicial };
  let tentativasGet = 0;
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const extra = extras?.(url, init);
    if (extra) {
      return extra;
    }
    const metodo = (init?.method ?? "GET").toUpperCase();
    if (url === "/propriedade/boas-vindas" && metodo === "GET") {
      tentativasGet += 1;
      if (inicial === "erro" && tentativasGet === 1) {
        return json({ detail: "falha" }, 500);
      }
      return json(atual);
    }
    if (url === "/propriedade/boas-vindas" && metodo === "PUT") {
      const corpo = JSON.parse(String(init?.body ?? "{}")) as typeof recado;
      atual = corpo;
      return json(atual);
    }
    return new Response(null, { status: 404 });
  });
}

function renderRecado(somenteLeitura = false) {
  return render(
    <MemoryRouter basename="/app" initialEntries={["/app/boas-vindas"]}>
      <TelaBoasVindas somenteLeitura={somenteLeitura} />
    </MemoryRouter>,
  );
}

describe("TelaBoasVindas", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("mostra os quatro campos, salva com PUT e não dispara chegada", async () => {
    const fetchMock = fetchRecado();
    vi.stubGlobal("fetch", fetchMock);
    renderRecado();

    expect(await screen.findByRole("heading", { name: "Recado de boas-vindas" })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/propriedade/boas-vindas",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(screen.getByLabelText("Café da manhã")).toHaveValue(recado.cafe);
    expect(screen.getByLabelText("Wi-fi")).toHaveValue(recado.wifi);
    expect(screen.getByLabelText("Horário de saída")).toHaveValue(recado.checkout);
    expect(screen.getByLabelText("Convite")).toHaveValue(recado.convite);
    expect(screen.queryByLabelText(/assistente virtual/i)).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Convite"), {
      target: { value: "Pergunte sobre o spa." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => {
      const put = fetchMock.mock.calls.find(
        (chamada) =>
          chamada[0] === "/propriedade/boas-vindas" && (chamada[1]?.method ?? "") === "PUT",
      );
      expect(put).toBeDefined();
      expect(JSON.parse(String(put?.[1]?.body))).toEqual({
        cafe: recado.cafe,
        wifi: recado.wifi,
        checkout: recado.checkout,
        convite: "Pergunte sobre o spa.",
      });
    });
    expect(screen.getByLabelText("Convite")).toHaveValue("Pergunte sobre o spa.");
    expect(
      fetchMock.mock.calls.some((chamada) => String(chamada[0]).includes("/chegada")),
    ).toBe(false);
  });

  it("422 mantém os valores carregados; falha de leitura não finge recado vazio", async () => {
    const fetchMock = fetchRecado(recado, (url, init) => {
      if (url === "/propriedade/boas-vindas" && (init?.method ?? "") === "PUT") {
        return json({ detail: "O campo cafe nao aceita quebra de linha." }, 422);
      }
      return null;
    });
    vi.stubGlobal("fetch", fetchMock);
    const visao = renderRecado();
    fireEvent.change(await screen.findByLabelText("Café da manhã"), {
      target: { value: "linha\nquebrada" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
    expect(await screen.findByText("O campo cafe nao aceita quebra de linha.")).toBeInTheDocument();
    expect(screen.getByLabelText("Café da manhã")).toHaveValue(recado.cafe);
    expect(screen.getByLabelText("Wi-fi")).toHaveValue(recado.wifi);
    visao.unmount();

    vi.stubGlobal("fetch", fetchRecado("erro"));
    renderRecado();
    expect(await screen.findByText("O recado não carregou.")).toBeInTheDocument();
    expect(screen.queryByLabelText("Café da manhã")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(await screen.findByLabelText("Café da manhã")).toBeInTheDocument();
  });
});
