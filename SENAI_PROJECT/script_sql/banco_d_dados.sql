CREATE TABLE clube (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(60) NOT NULL CONSTRAINT uk_clube_nome UNIQUE,
    sigla CHAR(3) NOT NULL CONSTRAINT uk_clube_sigla UNIQUE,
    caixa DECIMAL(10,2) NOT NULL DEFAULT 300.00,
    formacao VARCHAR(5) CONSTRAINT chk_clube_formacao CHECK (formacao IN ('3-1', '2-2', '2-1-1', '1-2-1')),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE jogador (
    id_jogador INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    clube_id INTEGER, -- Adicionado: a coluna era referenciada na FK mas não existia
    nome VARCHAR(100) NOT NULL,
    posicao VARCHAR(3) CHECK (posicao IN ('GOL', 'ZAG', 'LAT', 'MEI', 'ATA')),
    agilidade INTEGER CHECK (agilidade BETWEEN 1 AND 100) NOT NULL,
    idade INTEGER CHECK (idade BETWEEN 16 AND 45) NOT NULL,
    valor_base DECIMAL(6,2) NOT NULL,
    condicao VARCHAR(20) CHECK (condicao IN ('APTO', 'MAL_CONDICIONADO', 'DOENTE')), -- Corrigidas aspas duplas para simples
    velocidade INTEGER CHECK (velocidade BETWEEN 1 AND 99),
    finalizacao INTEGER CHECK (finalizacao BETWEEN 1 AND 99), -- Adicionado o tipo INTEGER que faltava
    passe INTEGER CHECK (passe BETWEEN 1 AND 99), -- Corrigido o fechamento do parêntese do CHECK
    drible INTEGER CHECK (drible BETWEEN 1 AND 99),
    defesa INTEGER CHECK (defesa BETWEEN 1 AND 99), -- Adicionado o tipo INTEGER que faltava
    fisico INTEGER CHECK (fisico BETWEEN 1 AND 99), -- Adicionado o tipo INTEGER que faltava
    potencial INTEGER CHECK (potencial BETWEEN 1 AND 99), -- Corrigido o nome da coluna dentro do check (estava 'fisico')
    ativo BOOLEAN NOT NULL DEFAULT TRUE, -- Adicionada a vírgula que faltava
    excluido_em TIMESTAMP NULL,
    criado_em TIMESTAMP NOT NULL, -- Adicionada a vírgula que faltava
    atualizado_em TIMESTAMP,
    CONSTRAINT fk_clubes_id FOREIGN KEY (clube_id) REFERENCES clube (id),
    CONSTRAINT fht_exluido CHECK (
        (ativo = TRUE AND excluido_em IS NULL)
        OR
        (ativo = FALSE AND excluido_em IS NOT NULL)
    )
);


CREATE TABLE contratos (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    jogador_id INTEGER NOT NULL,
    clube_id INTEGER NOT NULL,
    valor_compra DECIMAL(6,2) NOT NULL,
    fidelidade_ate TIMESTAMP NOT NULL,
    situacao VARCHAR(12) NOT NULL CONSTRAINT chk_contratos_situacao CHECK (situacao IN ('ATIVO', 'ENCERRADO', 'RESCINDIDO')),
    iniciado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    encerrado_em TIMESTAMP NULL,
    
    -- Chaves Estrangeiras (FKs)
    CONSTRAINT fk_contratos_jogador FOREIGN KEY (jogador_id) REFERENCES jogador (id_jogador),
    CONSTRAINT fk_contratos_clube FOREIGN KEY (clube_id) REFERENCES clube (id)
);





CREATE TABLE transacoes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    clube_id INTEGER NOT NULL,
    jogador_id INTEGER NOT NULL,
    nome_jogador VARCHAR(100) NOT NULL,
    tipo VARCHAR(6) NOT NULL CONSTRAINT chk_transacoes_tipo CHECK (tipo IN ('COMPRA', 'VENDA')),
    valor DECIMAL(6,2) NOT NULL,
    taxa DECIMAL(6,2) NOT NULL,
    multa DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    lucro DECIMAL(7,2) NULL,
    variacao_caixa DECIMAL(8,2) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    
    CONSTRAINT fk_transacoes_clube FOREIGN KEY (clube_id) REFERENCES clube (id),
    CONSTRAINT fk_transacoes_jogador FOREIGN KEY (jogador_id) REFERENCES jogador (id_jogador)
);


CREATE TABLE escalacoes (
    clube_id INTEGER NOT NULL,
    jogador_id INTEGER NOT NULL CONSTRAINT uk_escalacoes_jogador UNIQUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    
    CONSTRAINT pk_escalacoes PRIMARY KEY (clube_id, jogador_id),

    
    CONSTRAINT fk_escalacoes_clube FOREIGN KEY (clube_id) REFERENCES clube (id),
    CONSTRAINT fk_escalacoes_jogador FOREIGN KEY (jogador_id) REFERENCES jogador (id_jogador)
);




CREATE TABLE partidas (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mandante_id INTEGER NOT NULL,
    visitante_id INTEGER NOT NULL,
    gols_mandante INTEGER NOT NULL CONSTRAINT chk_partidas_gols_mandante CHECK (gols_mandante BETWEEN 0 AND 3),
    gols_visitante INTEGER NOT NULL CONSTRAINT chk_partidas_gols_visitante CHECK (gols_visitante BETWEEN 0 AND 3),
    formacao_mandante VARCHAR(5) NOT NULL CONSTRAINT chk_partidas_formacao_mandante CHECK (formacao_mandante IN ('3-1', '2-2', '2-1-1', '1-2-1')),
    formacao_visitante VARCHAR(5) NOT NULL CONSTRAINT chk_partidas_formacao_visitante CHECK (formacao_visitante IN ('3-1', '2-2', '2-1-1', '1-2-1')),
    jogada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Chaves Estrangeiras (FKs)
    CONSTRAINT fk_partidas_mandante FOREIGN KEY (mandante_id) REFERENCES clube (id),
    CONSTRAINT fk_partidas_visitante FOREIGN KEY (visitante_id) REFERENCES clube (id),

    -- Validação para garantir que um clube não jogue contra si mesmo
    CONSTRAINT chk_partidas_clubes_diferentes CHECK (mandante_id <> visitante_id)
);



CREATE TABLE duelos_partida (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    partida_id INTEGER NOT NULL,
    ordem INTEGER NOT NULL CONSTRAINT chk_duelos_ordem CHECK (ordem BETWEEN 1 AND 6),
    clube_atacante_id INTEGER NOT NULL,
    atacante_id INTEGER NOT NULL,
    defensor_id INTEGER NOT NULL,
    nome_atacante VARCHAR(100) NOT NULL,
    nome_defensor VARCHAR(100) NOT NULL,
    posicao_atacante VARCHAR(3) NOT NULL,
    posicao_defensor VARCHAR(3) NOT NULL,
    condicao_atacante VARCHAR(20) NOT NULL CONSTRAINT chk_duelos_cond_ataque CHECK (condicao_atacante IN ('APTO', 'MAL_CONDICIONADO')),
    condicao_defensor VARCHAR(20) NOT NULL CONSTRAINT chk_duelos_cond_defesa CHECK (condicao_defensor IN ('APTO', 'MAL_CONDICIONADO')),
    atributo_ataque VARCHAR(10) NOT NULL CONSTRAINT chk_duelos_atrib_ataque CHECK (atributo_ataque IN ('shooting', 'passing', 'dribbling', 'defending')),
    atributo_defesa VARCHAR(10) NOT NULL CONSTRAINT chk_duelos_atrib_defesa CHECK (atributo_defesa IN ('shooting', 'passing', 'dribbling', 'defending')),
    valor_ataque INTEGER NOT NULL,
    valor_defesa INTEGER NOT NULL,
    gol BOOLEAN NOT NULL,

    -- Chaves Estrangeiras (FKs)
    CONSTRAINT fk_duelos_partida FOREIGN KEY (partida_id) REFERENCES partidas (id),
    CONSTRAINT fk_duelos_clube_atacante FOREIGN KEY (clube_atacante_id) REFERENCES clube (id),
    CONSTRAINT fk_duelos_atacante FOREIGN KEY (atacante_id) REFERENCES jogador (id_jogador),
    CONSTRAINT fk_duelos_defensor FOREIGN KEY (defensor_id) REFERENCES jogador (id_jogador)
);