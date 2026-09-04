import { formatarMoeda } from "./apresentacao";

export type ItemVendavel = {
  id_item_vendavel: number;
  nome: string;
  preco_atual: string | number;
  ativo: boolean;
};

export function formatarPreco(valor: string | number): string {
  return formatarMoeda(valor);
}

export function formatarPrecoDigitavel(valor: string | number): string {
  const numero = typeof valor === "number" ? valor : Number(valor);
  if (Number.isNaN(numero)) {
    return String(valor);
  }
  return numero.toFixed(2);
}
