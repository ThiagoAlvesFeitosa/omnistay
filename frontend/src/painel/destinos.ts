export type Perfil = "recepcao" | "staff" | "gestor";

export type GrupoMenu = "operacao" | "propriedade" | "gestao";

export type Destino = {
  id: string;
  titulo: string;
  caminho: string;
  perfis: readonly Perfil[];
  grupo?: GrupoMenu;
  noMenu?: boolean;
};

export const ROTULO_GRUPO: Record<GrupoMenu, string> = {
  operacao: "Operação",
  propriedade: "Propriedade",
  gestao: "Gestão",
};

export const DESTINOS: readonly Destino[] = [
  { id: "fila", titulo: "Fila do dia", caminho: "/app/fila", perfis: ["recepcao"], grupo: "operacao" },
  {
    id: "reserva",
    titulo: "Nova reserva",
    caminho: "/app/reserva",
    perfis: ["recepcao"],
    noMenu: true,
  },
  { id: "ficha", titulo: "Estadia", caminho: "/app/ficha", perfis: ["recepcao"], grupo: "operacao" },
  {
    id: "alertas",
    titulo: "Chamados e pedidos",
    caminho: "/app/alertas",
    perfis: ["recepcao"],
    grupo: "operacao",
  },
  {
    id: "consumos",
    titulo: "Consumos a lançar",
    caminho: "/app/consumos",
    perfis: ["recepcao"],
    grupo: "operacao",
  },
  {
    id: "saida",
    titulo: "Saída do hóspede",
    caminho: "/app/saida",
    perfis: ["recepcao"],
    grupo: "operacao",
  },
  {
    id: "catalogo",
    titulo: "Catálogo",
    caminho: "/app/catalogo",
    perfis: ["recepcao", "gestor"],
    grupo: "propriedade",
  },
  {
    id: "vendaveis",
    titulo: "Itens vendáveis",
    caminho: "/app/vendaveis",
    perfis: ["recepcao", "gestor"],
    grupo: "propriedade",
  },
  {
    id: "boas-vindas",
    titulo: "Recado de boas-vindas",
    caminho: "/app/boas-vindas",
    perfis: ["recepcao", "gestor"],
    grupo: "propriedade",
  },
  {
    id: "chamados",
    titulo: "Meus chamados",
    caminho: "/app/chamados",
    perfis: ["staff"],
    grupo: "operacao",
  },
  {
    id: "indicadores",
    titulo: "Painel",
    caminho: "/app/indicadores",
    perfis: ["gestor"],
    grupo: "gestao",
  },
  { id: "mercado", titulo: "Mercado", caminho: "/app/mercado", perfis: ["gestor"], grupo: "gestao" },
  { id: "usuarios", titulo: "Usuários", caminho: "/app/usuarios", perfis: ["gestor"], grupo: "gestao" },
  {
    id: "retencao",
    titulo: "Retenção de dados",
    caminho: "/app/retencao",
    perfis: ["gestor"],
    grupo: "gestao",
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

const ORDEM_GRUPO: GrupoMenu[] = ["operacao", "propriedade", "gestao"];

export function destinoInicial(perfil: Perfil): string {
  return CASA[perfil];
}

export const ROTULO_PERFIL: Record<Perfil, string> = {
  recepcao: "Recepção",
  staff: "Equipe",
  gestor: "Gestão",
};

export function itensMenu(perfil: Perfil): Destino[] {
  return DESTINOS.filter((destino) => destino.perfis.includes(perfil) && destino.noMenu !== true);
}

export type GrupoVisivel = {
  id: GrupoMenu;
  rotulo: string;
  itens: Destino[];
};

export function menuAgrupado(perfil: Perfil): GrupoVisivel[] {
  const visiveis = itensMenu(perfil).filter((destino) => destino.grupo);
  return ORDEM_GRUPO.flatMap((id) => {
    const itens = visiveis.filter((destino) => destino.grupo === id);
    if (itens.length === 0) {
      return [];
    }
    return [{ id, rotulo: ROTULO_GRUPO[id], itens }];
  });
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
  const ficha = DESTINOS.find((destino) => destino.id === "ficha");
  if (ficha && (absoluto === ficha.caminho || absoluto.startsWith(`${ficha.caminho}/`))) {
    return ficha;
  }
  const saida = DESTINOS.find((destino) => destino.id === "saida");
  if (saida && (absoluto === saida.caminho || absoluto.startsWith(`${saida.caminho}/`))) {
    return saida;
  }
  return DESTINOS.find((destino) => destino.caminho === absoluto);
}

export function perfilPode(perfil: Perfil, pathname: string): boolean {
  const destino = destinoPorCaminho(pathname);
  return destino ? destino.perfis.includes(perfil) : false;
}
