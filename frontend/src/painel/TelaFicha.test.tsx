import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { montarTextoCopia } from "./ficha";
import { TelaFicha, type FichaResposta } from "./TelaFicha";

function json(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fichaParcial: FichaResposta = {
  id_reserva: 1042,
  id_hospede: 7,
  ficha_completa: false,
  status_reserva: "ficha_parcial",
  estado_cadastro: "parcial",
  nome_completo: "Marina Duarte",
  profissao: null,
  data_nascimento: null,
  tipo_documento: null,
  numero_documento: null,
  endereco: null,
  cep: null,
  cidade: null,
  telefone: "5511987654321",
};

const fichaCompleta: FichaResposta = {
  ...fichaParcial,
  ficha_completa: true,
  status_reserva: "ficha_recebida",
  estado_cadastro: "completa",
  nome_completo: "Marina Duarte Fonseca",
  profissao: "Gerente de contas",
  data_nascimento: "1992-03-14",
  tipo_documento: "cpf",
  numero_documento: "12345678900",
  endereco: "Rua das Acácias, 220",
  cep: "04567000",
  cidade: "São Paulo",
};

const consentimentoNunca = {
  id_hospede: 7,
  finalidade: "comunicacao_marketing",
  concedido: false,
  momento: null,
  origem: null,
  em: "2026-08-31T00:00:00Z",
};

function fetchDaFicha(
  ficha: FichaResposta,
  consentimento: Record<string, unknown> = consentimentoNunca,
  extras?: (url: string, init?: RequestInit) => Response | undefined,
) {
  return vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const extra = extras?.(url, init);
    if (extra) {
      return extra;
    }
    if (String(url).includes("/consentimento")) {
      return json(consentimento);
    }
    return json(ficha);
  });
}

function renderFicha(rota: string, fetchMock: ReturnType<typeof vi.fn>) {
  vi.stubGlobal("fetch", fetchMock);
  return render(
    <MemoryRouter basename="/app" initialEntries={[rota]}>
      <Routes>
        <Route path="/ficha/:idReserva?" element={<TelaFicha />} />
        <Route path="/fila" element={<div data-testid="fila" />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("TelaFicha", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("menu sem reserva não busca ficha e aponta para a fila e para Chamados e pedidos", async () => {
    const fetchMock = vi.fn();
    renderFicha("/app/ficha", fetchMock);
    expect(await screen.findByText(/abre pela fila do dia/i)).toBeInTheDocument();
    expect(screen.getByText(/chamados e pedidos/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /fila do dia/i })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("abre a ficha parcial com ausentes nomeados, sem e-mail", async () => {
    const fetchMock = fetchDaFicha(fichaParcial);
    renderFicha("/app/ficha/1042", fetchMock);
    expect((await screen.findAllByText("Marina Duarte")).length).toBeGreaterThan(0);
    expect(screen.getByText(/parcial/i)).toBeInTheDocument();
    expect(screen.getByText(/Falta:/)).toHaveTextContent("Profissão");
    expect(screen.getByText(/Falta:/)).toHaveTextContent("CEP");
    expect(screen.queryByLabelText(/e-mail/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/idade/i)).not.toBeInTheDocument();
    const gets = fetchMock.mock.calls.filter((chamada) =>
      String(chamada[0]).includes("/reservas/1042/ficha"),
    );
    expect(gets).toHaveLength(1);
    expect(gets[0][1]).toEqual(expect.objectContaining({ credentials: "include" }));
  });

  it("ficha completa mostra distintivo e idade derivada, sem input de idade", async () => {
    const fetchMock = fetchDaFicha(fichaCompleta);
    renderFicha("/app/ficha/1042", fetchMock);
    expect((await screen.findAllByText("Marina Duarte Fonseca")).length).toBeGreaterThan(0);
    expect(screen.getByText(/completa/i)).toBeInTheDocument();
    expect(screen.queryByText(/Falta:/)).not.toBeInTheDocument();
    expect(screen.getByText(/\d+ anos/)).toBeInTheDocument();
    expect(screen.queryByLabelText(/idade/i)).not.toBeInTheDocument();
  });

  it("leitura humana avisa sem reproduzir mensagem", async () => {
    const fetchMock = fetchDaFicha({ ...fichaParcial, estado_cadastro: "leitura_humana" });
    renderFicha("/app/ficha/1042", fetchMock);
    expect(await screen.findByText(/leitura humana/i)).toBeInTheDocument();
    expect(screen.queryByText(/olá/i)).not.toBeInTheDocument();
  });

  it("falha de leitura não usa o estado vazio do menu", async () => {
    const fetchMock = vi.fn().mockResolvedValue(json({ detail: "falha" }, 500));
    renderFicha("/app/ficha/1042", fetchMock);
    expect(await screen.findByText(/não foi possível carregar a ficha/i)).toBeInTheDocument();
    expect(screen.queryByText(/abre pela fila do dia/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tentar de novo" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /fila do dia/i })).toBeInTheDocument();
  });

  it("404 não inventa nome", async () => {
    const fetchMock = vi.fn().mockResolvedValue(json({ detail: "nao encontrada" }, 404));
    renderFicha("/app/ficha/1042", fetchMock);
    expect(await screen.findByText(/não foi possível carregar a ficha/i)).toBeInTheDocument();
    expect(screen.queryByText("Marina Duarte")).not.toBeInTheDocument();
  });

  it("tentar de novo recupera a ficha", async () => {
    let tentativas = 0;
    const fetchMock = vi.fn().mockImplementation(async (url: string) => {
      if (String(url).includes("/consentimento")) {
        return json(consentimentoNunca);
      }
      tentativas += 1;
      if (tentativas === 1) {
        return json({ detail: "falha" }, 500);
      }
      return json(fichaCompleta);
    });
    renderFicha("/app/ficha/1042", fetchMock);
    fireEvent.click(await screen.findByRole("button", { name: "Tentar de novo" }));
    expect((await screen.findAllByText("Marina Duarte Fonseca")).length).toBeGreaterThan(0);
  });

  it("Gravar envia os nove campos e atualiza o distintivo", async () => {
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (metodo === "PUT" && String(url).includes("/reservas/1042/ficha")) {
        return json(fichaCompleta);
      }
      if (String(url).includes("/consentimento")) {
        return json(consentimentoNunca);
      }
      return json(fichaParcial);
    });
    renderFicha("/app/ficha/1042", fetchMock);
    fireEvent.click(await screen.findByRole("button", { name: "Editar" }));
    fireEvent.change(screen.getByLabelText("Nome completo"), {
      target: { value: "Marina Duarte Fonseca" },
    });
    fireEvent.change(screen.getByLabelText("Profissão"), {
      target: { value: "Gerente de contas" },
    });
    fireEvent.change(screen.getByLabelText("Data de nascimento"), {
      target: { value: "1992-03-14" },
    });
    fireEvent.change(screen.getByLabelText("Tipo de documento"), {
      target: { value: "cpf" },
    });
    fireEvent.change(screen.getByLabelText("Número do documento"), {
      target: { value: "12345678900" },
    });
    fireEvent.change(screen.getByLabelText("Endereço"), {
      target: { value: "Rua das Acácias, 220" },
    });
    fireEvent.change(screen.getByLabelText("CEP"), { target: { value: "04567000" } });
    fireEvent.change(screen.getByLabelText("Cidade"), { target: { value: "São Paulo" } });
    fireEvent.click(screen.getByRole("button", { name: "Gravar" }));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (chamada) =>
            String(chamada[0]).includes("/reservas/1042/ficha") &&
            (chamada[1]?.method ?? "GET") === "PUT",
        ),
      ).toBe(true),
    );
    const put = fetchMock.mock.calls.find(
      (chamada) =>
        String(chamada[0]).includes("/reservas/1042/ficha") &&
        (chamada[1]?.method ?? "GET") === "PUT",
    );
    expect(JSON.parse(String(put?.[1]?.body))).toEqual({
      nome_completo: "Marina Duarte Fonseca",
      profissao: "Gerente de contas",
      data_nascimento: "1992-03-14",
      tipo_documento: "cpf",
      numero_documento: "12345678900",
      endereco: "Rua das Acácias, 220",
      cep: "04567000",
      cidade: "São Paulo",
      telefone: "5511987654321",
    });
    expect(await screen.findByText(/completa/i)).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(
        (chamada) =>
          String(chamada[0]).includes("/webhook") || String(chamada[0]).includes("/simulador"),
      ),
    ).toBe(false);
  });

  it("422 mostra o detalhe e não afirma completa", async () => {
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (metodo === "PUT") {
        return json({ detail: "Campo cep invalido." }, 422);
      }
      if (String(url).includes("/consentimento")) {
        return json(consentimentoNunca);
      }
      return json(fichaParcial);
    });
    renderFicha("/app/ficha/1042", fetchMock);
    fireEvent.click(await screen.findByRole("button", { name: "Editar" }));
    fireEvent.change(screen.getByLabelText("CEP"), { target: { value: "12" } });
    fireEvent.click(screen.getByRole("button", { name: "Gravar" }));
    expect(await screen.findByText(/Campo cep invalido/i)).toBeInTheDocument();
    expect(screen.getByText(/parcial/i)).toBeInTheDocument();
    expect(screen.queryByText(/^completa$/i)).not.toBeInTheDocument();
  });

  it("Cancelar não dispara PUT", async () => {
    const fetchMock = fetchDaFicha(fichaParcial);
    renderFicha("/app/ficha/1042", fetchMock);
    fireEvent.click(await screen.findByRole("button", { name: "Editar" }));
    fireEvent.change(screen.getByLabelText("Profissão"), { target: { value: "Outra" } });
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(
      fetchMock.mock.calls.filter((chamada) => (chamada[1]?.method ?? "GET") === "PUT"),
    ).toHaveLength(0);
    expect(screen.queryByLabelText("Profissão")).not.toBeInTheDocument();
    expect(screen.getByText(/parcial/i)).toBeInTheDocument();
  });

  it("Copiar tudo chama a área de transferência com o texto rotulado", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    renderFicha("/app/ficha/1042", fetchDaFicha(fichaCompleta));
    fireEvent.click(await screen.findByRole("button", { name: "Copiar tudo" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(montarTextoCopia(fichaCompleta)));
    expect(writeText.mock.calls[0][0]).not.toMatch(/^Idade:/m);
    expect(writeText.mock.calls[0][0]).not.toMatch(/e-mail/i);
  });

  it("se a cópia automática falhar, o texto permanece selecionável", async () => {
    const writeText = vi.fn().mockRejectedValue(new Error("denied"));
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    renderFicha("/app/ficha/1042", fetchDaFicha(fichaCompleta));
    fireEvent.click(await screen.findByRole("button", { name: "Copiar tudo" }));
    const bloco = await screen.findByText(/Nome completo: Marina Duarte Fonseca/);
    expect(bloco.tagName).toBe("PRE");
  });

  it("mostra aceite vigente com data e revoga com origem painel", async () => {
    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const metodo = (init?.method ?? "GET").toUpperCase();
      if (String(url).includes("/consentimento") && metodo === "POST") {
        return json(
          {
            id_hospede: 7,
            finalidade: "comunicacao_marketing",
            concedido: false,
            momento: "2026-08-31T12:00:00Z",
            origem: "painel",
            em: "2026-08-31T12:00:00Z",
          },
          201,
        );
      }
      if (String(url).includes("/consentimento")) {
        return json({
          id_hospede: 7,
          finalidade: "comunicacao_marketing",
          concedido: true,
          momento: "2026-03-14T10:00:00Z",
          origem: "solicitacao_titular",
          em: "2026-08-31T00:00:00Z",
        });
      }
      return json(fichaCompleta);
    });
    renderFicha("/app/ficha/1042", fetchMock);
    expect(await screen.findByText(/concedido em 14\/03\/2026/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Revogar" }));
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(
          (chamada) =>
            String(chamada[0]).includes("/hospedes/7/consentimento") &&
            chamada[1]?.method === "POST",
        ),
      ).toBe(true),
    );
    const post = fetchMock.mock.calls.find(
      (chamada) =>
        String(chamada[0]).includes("/consentimento") && chamada[1]?.method === "POST",
    );
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({
      concedido: false,
      origem: "painel",
    });
    expect(
      fetchMock.mock.calls.some((chamada) => String(chamada[1]?.body ?? "").includes("pesquisa_checkout")),
    ).toBe(false);
  });

  it("nunca registrado e recusa datada não se confundem", async () => {
    const fetchNunca = fetchDaFicha(fichaParcial, consentimentoNunca);
    const nunca = renderFicha("/app/ficha/1042", fetchNunca);
    expect(await screen.findByText(/nunca registrado/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Revogar" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Registrar aceite" }));
    await waitFor(() =>
      expect(
        fetchNunca.mock.calls.some(
          (chamada) =>
            String(chamada[0]).includes("/consentimento") && chamada[1]?.method === "POST",
        ),
      ).toBe(true),
    );
    const post = fetchNunca.mock.calls.find(
      (chamada) => String(chamada[0]).includes("/consentimento") && chamada[1]?.method === "POST",
    );
    expect(JSON.parse(String(post?.[1]?.body))).toEqual({
      concedido: true,
      origem: "painel",
    });
    nunca.unmount();

    const recusa = {
      id_hospede: 7,
      finalidade: "comunicacao_marketing",
      concedido: false,
      momento: "2026-04-01T00:00:00Z",
      origem: "painel",
      em: "2026-08-31T00:00:00Z",
    };
    renderFicha("/app/ficha/1042", fetchDaFicha(fichaParcial, recusa));
    expect(await screen.findByText(/recusado em 01\/04\/2026/i)).toBeInTheDocument();
    expect(screen.queryByText(/nunca registrado/i)).not.toBeInTheDocument();
  });
});
