export const CAMPOS_FICHA = [
  { chave: "nome_completo", rotulo: "Nome completo" },
  { chave: "profissao", rotulo: "Profissão" },
  { chave: "data_nascimento", rotulo: "Data de nascimento" },
  { chave: "tipo_documento", rotulo: "Tipo de documento" },
  { chave: "numero_documento", rotulo: "Número do documento" },
  { chave: "endereco", rotulo: "Endereço" },
  { chave: "cep", rotulo: "CEP" },
  { chave: "cidade", rotulo: "Cidade" },
  { chave: "telefone", rotulo: "Telefone" },
] as const;

export type ChaveCampoFicha = (typeof CAMPOS_FICHA)[number]["chave"];

export type CamposFicha = Partial<Record<ChaveCampoFicha, string | null>>;

function utilizavel(valor: string | null | undefined): valor is string {
  return valor != null && valor.trim() !== "";
}

export function camposAusentes(ficha: CamposFicha): string[] {
  return CAMPOS_FICHA.filter((campo) => !utilizavel(ficha[campo.chave])).map(
    (campo) => campo.rotulo,
  );
}

export function idadeDerivada(
  dataNascimento: string | null | undefined,
  referencia: string,
): number | null {
  if (!utilizavel(dataNascimento)) {
    return null;
  }
  const nasc = new Date(`${dataNascimento}T00:00:00`);
  const hoje = new Date(`${referencia}T00:00:00`);
  if (Number.isNaN(nasc.getTime()) || Number.isNaN(hoje.getTime())) {
    return null;
  }
  let idade = hoje.getFullYear() - nasc.getFullYear();
  const aniversarioEsteAno = new Date(hoje.getFullYear(), nasc.getMonth(), nasc.getDate());
  if (hoje < aniversarioEsteAno) {
    idade -= 1;
  }
  return idade;
}

export function formatarDataVisivel(iso: string): string {
  const [ano, mes, dia] = iso.split("-");
  if (!ano || !mes || !dia) {
    return iso;
  }
  return `${dia}/${mes}/${ano}`;
}

export function montarTextoCopia(ficha: CamposFicha): string {
  return CAMPOS_FICHA.map((campo) => {
    const bruto = ficha[campo.chave];
    if (!utilizavel(bruto)) {
      return `${campo.rotulo}:`;
    }
    let valor = bruto.trim();
    if (campo.chave === "data_nascimento") {
      valor = formatarDataVisivel(valor);
    } else if (campo.chave === "tipo_documento") {
      valor = valor.toUpperCase();
    }
    return `${campo.rotulo}: ${valor}`;
  }).join("\n");
}

