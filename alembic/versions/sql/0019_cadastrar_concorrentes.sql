ALTER TABLE concorrente
    ADD CONSTRAINT ck_concorrente_url_fonte
        CHECK (btrim(url_fonte) ~* '^https?://[^[:space:]]+$');

CREATE UNIQUE INDEX uq_concorrente_hotel_fonte
    ON concorrente (id_hotel, lower(btrim(url_fonte)));

CREATE INDEX ix_concorrente_hotel_ativo
    ON concorrente (id_hotel) WHERE ativo;
