export class TelefoneInvalido extends Error {
  constructor(mensagem = "Informe um telefone brasileiro com DDD (celular com 11 dígitos ou fixo com 10).") {
    super(mensagem);
    this.name = "TelefoneInvalido";
  }
}

export function normalizar(valor: string): string {
  const digitos = [...valor].filter((caractere) => caractere >= "0" && caractere <= "9").join("");
  if (digitos.startsWith("55") && (digitos.length === 12 || digitos.length === 13)) {
    return digitos;
  }
  if (digitos.length === 10 || digitos.length === 11) {
    return "55" + digitos;
  }
  throw new TelefoneInvalido();
}

export function telefoneUtilizavel(valor: string): boolean {
  try {
    normalizar(valor);
    return true;
  } catch {
    return false;
  }
}
