import { describe, expect, it } from "vitest";

import { camposAusentes, idadeDerivada, montarTextoCopia } from "./ficha";

const novePreenchidos = {
  nome_completo: "Marina Duarte Fonseca",
  profissao: "Gerente de contas",
  data_nascimento: "1992-03-14",
  tipo_documento: "cpf",
  numero_documento: "12345678900",
  endereco: "Rua das Acácias, 220",
  cep: "04567000",
  cidade: "São Paulo",
  telefone: "5511987654321",
};

describe("camposAusentes", () => {
  it("ficha com os nove preenchidos não tem ausentes", () => {
    expect(camposAusentes(novePreenchidos)).toEqual([]);
  });

  it("só nome e telefone nomeia os sete ausentes em português", () => {
    const ausentes = camposAusentes({
      nome_completo: "Marina Duarte",
      telefone: "5511987654321",
    });
    expect(ausentes).toEqual([
      "Profissão",
      "Data de nascimento",
      "Tipo de documento",
      "Número do documento",
      "Endereço",
      "CEP",
      "Cidade",
    ]);
  });

  it("null ou string vazia conta como ausente", () => {
    const ausentes = camposAusentes({
      ...novePreenchidos,
      profissao: null,
      cep: "",
    });
    expect(ausentes).toEqual(["Profissão", "CEP"]);
  });
});

describe("idadeDerivada", () => {
  it("calcula a idade na data de referência", () => {
    expect(idadeDerivada("1992-03-14", "2026-08-31")).toBe(34);
  });

  it("sem data devolve null", () => {
    expect(idadeDerivada(null, "2026-08-31")).toBeNull();
    expect(idadeDerivada("", "2026-08-31")).toBeNull();
  });
});

describe("montarTextoCopia", () => {
  it("monta nove linhas rotuladas na ordem da coleta, data local, sem idade nem e-mail", () => {
    const texto = montarTextoCopia(novePreenchidos);
    expect(texto).toBe(
      [
        "Nome completo: Marina Duarte Fonseca",
        "Profissão: Gerente de contas",
        "Data de nascimento: 14/03/1992",
        "Tipo de documento: CPF",
        "Número do documento: 12345678900",
        "Endereço: Rua das Acácias, 220",
        "CEP: 04567000",
        "Cidade: São Paulo",
        "Telefone: 5511987654321",
      ].join("\n"),
    );
    expect(texto).not.toMatch(/^Idade:/m);
    expect(texto).not.toMatch(/e-mail/i);
  });

  it("campo vazio entra só com o rótulo, sem valor inventado", () => {
    const texto = montarTextoCopia({
      nome_completo: "Marina Duarte Fonseca",
      profissao: null,
      data_nascimento: "",
    });
    expect(texto).toContain("Nome completo: Marina Duarte Fonseca");
    expect(texto).toMatch(/^Profissão:$/m);
    expect(texto).toMatch(/^Data de nascimento:$/m);
    expect(texto).not.toMatch(/^Idade:/m);
  });
});
