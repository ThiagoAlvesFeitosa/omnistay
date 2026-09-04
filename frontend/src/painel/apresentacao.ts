import { tempoDecorrido } from "./solicitacoes";

function paraData(quando: string | Date): Date | null {
  const data = quando instanceof Date ? quando : new Date(quando);
  if (Number.isNaN(data.getTime())) {
    return null;
  }
  return data;
}

function doisDigitos(valor: number): string {
  return String(valor).padStart(2, "0");
}

function instanteLocal(data: Date): string {
  return `${doisDigitos(data.getDate())}/${doisDigitos(data.getMonth() + 1)}/${data.getFullYear()} ${doisDigitos(data.getHours())}:${doisDigitos(data.getMinutes())}`;
}

function horaLocal(data: Date): string {
  return `${doisDigitos(data.getHours())}:${doisDigitos(data.getMinutes())}`;
}

function mesmoDiaCalendario(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

export function formatarMoeda(valor: string | number): string {
  const numero = typeof valor === "number" ? valor : Number(valor);
  if (Number.isNaN(numero)) {
    return String(valor);
  }
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  })
    .format(numero)
    .replace(/\u00a0/g, " ");
}

export function formatarDataCalendario(iso: string): string {
  const [ano, mes, dia] = iso.split("-");
  if (!ano || !mes || !dia || ano.length !== 4 || mes.length !== 2 || dia.length !== 2) {
    return "";
  }
  if (Number.isNaN(Number(ano)) || Number.isNaN(Number(mes)) || Number.isNaN(Number(dia))) {
    return "";
  }
  return `${dia}/${mes}/${ano}`;
}

export function formatarInstante(quando: string | Date): string {
  const data = paraData(quando);
  if (!data) {
    if (typeof quando === "string") {
      return formatarDataCalendario(quando.slice(0, 10));
    }
    return "";
  }
  return instanteLocal(data);
}

export function formatarInstanteComDecorrido(
  abertoEm: string | Date,
  agora: Date,
): string {
  const instante = formatarInstante(abertoEm);
  const iso = abertoEm instanceof Date ? abertoEm.toISOString() : abertoEm;
  const decorrido = tempoDecorrido(iso, agora);
  if (!instante) {
    return decorrido;
  }
  return `${instante} · ${decorrido}`;
}

export function formatarHorarioBolha(quando: string | Date, agora: Date): string {
  const data = paraData(quando);
  if (!data) {
    return "";
  }
  if (mesmoDiaCalendario(data, agora)) {
    return horaLocal(data);
  }
  return instanteLocal(data);
}
