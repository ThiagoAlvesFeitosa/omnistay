export function prazoVisivel(valor: number | null): string {
  if (valor == null || !Number.isInteger(valor) || valor < 1) {
    return "Prazo não configurado";
  }
  return String(valor);
}
