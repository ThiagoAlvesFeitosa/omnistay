export type Perfil = "recepcao" | "staff" | "gestor";

export type Destino = {
  id: string;
  titulo: string;
  caminho: string;
  perfis: readonly Perfil[];
};

export const DESTINOS: readonly Destino[] = [
  { id: "fila", titulo: "Fila do dia", caminho: "/app/fila", perfis: ["recepcao"] },
  { id: "reserva", titulo: "Nova reserva", caminho: "/app/reserva", perfis: ["recepcao"] },
  { id: "ficha", titulo: "Ficha do hóspede", caminho: "/app/ficha", perfis: ["recepcao"] },
  {
    id: "alertas",
    titulo: "Chamados e pedidos",
    caminho: "/app/alertas",
    perfis: ["recepcao"],
  },
  {
    id: "consumos",
    titulo: "Consumos a lançar",
    caminho: "/app/consumos",
    perfis: ["recepcao"],
  },
  { id: "saida", titulo: "Saída do hóspede", caminho: "/app/saida", perfis: ["recepcao"] },
  { id: "catalogo", titulo: "Catálogo", caminho: "/app/catalogo", perfis: ["recepcao"] },
  {
    id: "vendaveis",
    titulo: "Itens vendáveis",
    caminho: "/app/vendaveis",
    perfis: ["recepcao"],
  },
  {
    id: "boas-vindas",
    titulo: "Recado de boas-vindas",
    caminho: "/app/boas-vindas",
    perfis: ["recepcao"],
  },
  { id: "chamados", titulo: "Meus chamados", caminho: "/app/chamados", perfis: ["staff"] },
  {
    id: "indicadores",
    titulo: "Painel",
    caminho: "/app/indicadores",
    perfis: ["gestor"],
  },
  { id: "mercado", titulo: "Mercado", caminho: "/app/mercado", perfis: ["gestor"] },
  { id: "usuarios", titulo: "Usuários", caminho: "/app/usuarios", perfis: ["gestor"] },
  {
    id: "retencao",
    titulo: "Retenção de dados",
    caminho: "/app/retencao",
    perfis: ["gestor"],
  },
  {
    id: "simulador",
    titulo: "Simulador",
    caminho: "/app/simulador",
    perfis: ["recepcao", "gestor"],
  },
];

const CASA: Record<Perfil, string> = {
  recepcao: "/app/fila",
  staff: "/app/chamados",
  gestor: "/app/indicadores",
};

export function destinoInicial(perfil: Perfil): string {
  return CASA[perfil];
}

export function itensMenu(perfil: Perfil): Destino[] {
  return DESTINOS.filter((destino) => destino.perfis.includes(perfil));
}

export function caminhoRelativo(caminho: string): string {
  if (caminho === "/app" || caminho === "/app/") {
    return "/";
  }
  return caminho.startsWith("/app") ? caminho.slice("/app".length) || "/" : caminho;
}

export function destinoPorCaminho(pathname: string): Destino | undefined {
  const absoluto = pathname.startsWith("/app")
    ? pathname
    : `/app${pathname === "/" ? "" : pathname}`;
  return DESTINOS.find((destino) => destino.caminho === absoluto);
}

export function perfilPode(perfil: Perfil, pathname: string): boolean {
  const destino = destinoPorCaminho(pathname);
  return destino ? destino.perfis.includes(perfil) : false;
}
