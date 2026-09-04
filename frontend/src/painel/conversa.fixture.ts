import type { ConversaResposta, ItemConversa } from "./TelaEstadia";

export function itemConversaDeTeste(sobrepor: Partial<ItemConversa> = {}): ItemConversa {
  return {
    id_mensagem: 1,
    direcao: "recebida",
    origem: "hospede",
    conteudo: "tem berco?",
    status_envio: null,
    entrega: null,
    nova_tentativa: null,
    em: "2026-09-02T18:00:00Z",
    ...sobrepor,
  };
}

export function conversaDeTeste(sobrepor: Partial<ConversaResposta> = {}): ConversaResposta {
  return {
    id_reserva: 1042,
    janela: { aberta: true, motivo: null },
    mensagens: [
      itemConversaDeTeste(),
      itemConversaDeTeste({
        id_mensagem: 2,
        direcao: "enviada",
        origem: "automatico",
        conteudo: "A recepção vai atender.",
        status_envio: "enviada",
        entrega: "enviada",
        nova_tentativa: false,
        em: "2026-09-02T18:01:00Z",
      }),
      itemConversaDeTeste({
        id_mensagem: 3,
        direcao: "enviada",
        origem: "recepcao",
        conteudo: "Sim, temos berço.",
        status_envio: "pendente",
        entrega: "enviando",
        nova_tentativa: false,
        em: "2026-09-02T18:02:00Z",
      }),
    ],
    ...sobrepor,
  };
}
