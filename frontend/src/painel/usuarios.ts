export type PerfilUsuario = "recepcao" | "staff" | "gestor";

export type UsuarioLista = {
  id_usuario: number;
  nome: string;
  email: string;
  perfil: PerfilUsuario;
  ativo: boolean;
};

const ROTULOS: Record<PerfilUsuario, string> = {
  recepcao: "Recepção",
  staff: "Equipe",
  gestor: "Gestão",
};

export function rotuloPerfil(perfil: PerfilUsuario): string {
  return ROTULOS[perfil];
}

export function contarSituacao(lista: readonly UsuarioLista[]): {
  ativos: number;
  desativados: number;
} {
  return {
    ativos: lista.filter((item) => item.ativo).length,
    desativados: lista.filter((item) => !item.ativo).length,
  };
}
