import { describe, expect, it } from "vitest";

import { conversaDeTeste, itemConversaDeTeste } from "./conversa.fixture";

describe("conversaDeTeste", () => {
  it("aceita sobrepor campos que no padrão são null", () => {
    const conversa = conversaDeTeste({
      janela: { aberta: false, motivo: "nunca_escreveu" },
      mensagens: [
        itemConversaDeTeste({
          entrega: "enviada",
          status_envio: "enviada",
          nova_tentativa: false,
        }),
        itemConversaDeTeste({
          id_mensagem: 4,
          entrega: "falhou",
          nova_tentativa: true,
        }),
      ],
    });

    expect(conversa.janela.motivo).toBe("nunca_escreveu");
    expect(conversa.mensagens[0].entrega).toBe("enviada");
    expect(conversa.mensagens[1].nova_tentativa).toBe(true);
  });
});
