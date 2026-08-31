CREATE OR REPLACE FUNCTION fn_valida_transicao_reserva()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF NOT (
        (OLD.status = 'aguardando_cadastro' AND NEW.status IN
            ('ficha_recebida', 'ficha_parcial', 'sem_cadastro_previo', 'cancelada'))
     OR (OLD.status IN ('ficha_recebida', 'ficha_parcial', 'sem_cadastro_previo')
            AND NEW.status IN ('hospedado', 'cancelada'))
     OR (OLD.status = 'ficha_parcial' AND NEW.status = 'ficha_recebida')
     OR (OLD.status = 'ficha_recebida' AND NEW.status = 'ficha_parcial')
     OR (OLD.status = 'hospedado' AND NEW.status = 'encerrado')
    ) THEN
        RAISE EXCEPTION
            'Transicao de status invalida na reserva %: % -> %',
            OLD.id_reserva, OLD.status, NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
