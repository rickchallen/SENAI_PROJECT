# Liga5 — Gestão de futebol

Aplicação web para administrar jogadores, clubes, contratos, transferências e uma
liga de futebol de cinco. A API aplica as regras de negócio e calcula todos os
valores financeiros, avaliações, multas, comissões, placares e classificações.
O React apresenta os dados recebidos e não duplica esses cálculos.

## Tecnologias

- Backend: Python 3.14, FastAPI, SQLAlchemy 2 e psycopg 3.
- Banco: PostgreSQL 18.
- Frontend: React 19, TypeScript 7, Vite 8 e Tailwind CSS 4.
- Testes e qualidade: pytest, HTTPX, Ruff e Oxlint.
- Execução: Docker Compose.

As dependências diretas estão declaradas em `back-end/requirements.txt` e
`frontend1/package.json`; o arquivo `frontend1/package-lock.json` fixa as
dependências JavaScript.

## Estrutura

```text
SENAI_PROJECT/
├── back-end/
│   ├── app/
│   │   ├── api.py                 # rotas, erros HTTP, CORS e logs
│   │   ├── domain.py              # cálculos e regras puras
│   │   ├── entidades.py           # entidades ORM com nomes de domínio
│   │   ├── repositories.py        # consultas e persistência
│   │   ├── services/              # casos de uso por módulo
│   │   └── validation.py          # contratos de entrada e query params
│   ├── tests/
│   ├── main.py
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend1/
│   └── src/
│       ├── api.ts                 # cliente HTTP e mensagens de erro
│       ├── components/            # telas por funcionalidade
│       ├── format.ts              # apresentação de moeda e datas
│       └── types.ts
├── script_sql/
│   └── 001_initial_schema.sql     # migração inicial versionada
├── docker-compose.yml
└── .env.example
```

As entidades persistidas e as sete tabelas obrigatórias mantêm os nomes do
enunciado: `clubes`, `jogadores`, `contratos`, `transacoes`, `escalacoes`,
`partidas` e `duelos_partida`. Os campos da API seguem `snake_case` e o contrato
documentado no enunciado.

## Executar com Docker Compose

Pré-requisitos: Docker Engine com Docker Compose v2 e Git. A aplicação foi
preparada para Python 3.14 e Node.js 22; no modo Compose, esses runtimes já vêm
nas imagens dos containers.

No terminal, entre na pasta `SENAI_PROJECT` e execute:

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

- Interface: <http://localhost:4173>
- API (origem, sem `/api/v1`): <http://localhost:8000>
- Swagger/OpenAPI: <http://localhost:8000/docs>
- Base da API: `http://localhost:8000/api/v1`

Para acompanhar os logs:

```bash
docker compose logs -f backend frontend database
```

O PostgreSQL executa `script_sql/001_initial_schema.sql` ao inicializar um
volume vazio. Para recriar o banco do zero e executar novamente a migração:

```bash
docker compose down -v
docker compose up --build -d
```

O comando `down -v` apaga os dados persistidos da aplicação. Não o execute se
quiser manter o banco atual.

## Variáveis de ambiente

Copie `.env.example` para `.env`. O arquivo contém valores exclusivamente para
desenvolvimento local; não use essas credenciais em produção nem versione o
arquivo `.env`.

| Variável | Uso |
| --- | --- |
| `POSTGRES_DB` | Nome do banco criado pelo container. |
| `POSTGRES_USER` | Usuário do PostgreSQL. |
| `POSTGRES_PASSWORD` | Senha local do PostgreSQL. |
| `API_PORT` | Porta publicada para a API (padrão `8000`). |
| `FRONTEND_PORT` | Porta publicada para o frontend (padrão `4173`). |
| `CORS_ORIGINS` | Origens permitidas para as chamadas ao backend. |
| `VITE_API_URL` | URL da API incorporada ao build do frontend. |
| `DATABASE_URL` | URL SQLAlchemy para executar o backend fora do Compose. |

Se a senha do banco tiver caracteres reservados em uma URL, use a forma
percent-encoded correspondente em `DATABASE_URL`.

## Desenvolvimento local e validação

Os testes usam SQLite em memória exclusivamente como banco de teste; a aplicação
usa PostgreSQL. A partir da raiz do projeto:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r back-end/requirements-dev.txt
```

Testes e lint do backend:

```bash
cd back-end
python -m pytest
ruff check main.py app tests
ruff format --check main.py app tests
cd ..
```

Build e lint do frontend:

```bash
cd frontend1
npm ci
npm run lint
npm run build
```

Para iniciar apenas o servidor de desenvolvimento do frontend, com a API já
disponível na URL configurada em `VITE_API_URL`:

```bash
cd frontend1
npm run dev
```

O backend pode ser iniciado localmente com `uvicorn main:app --reload` a partir
de `back-end`, desde que `DATABASE_URL` aponte para um PostgreSQL inicializado
com a migração versionada.

## Regras e segurança

- Os endpoints da aplicação são públicos, sem login ou controle de acesso,
  conforme a premissa do enunciado. Não há contas ou dados pessoais.
- As regras e cálculos são validados no backend. Os erros de entrada, recursos
  ausentes e conflitos de negócio são respondidos com `400`, `404` e `409`,
  respectivamente, sempre com `message`.
- Compras, vendas, escalações e partidas são transacionais; operações recusadas
  não persistem alterações parciais.
- Valores monetários usam `Decimal` e arredondamento half-up ao final de cada
  cálculo. A moeda fica armazenada em colunas `DECIMAL`.
- Datas são persistidas como horário local de Brasília e retornadas com o
  deslocamento fixo `-03:00`, conforme a RN01.
- Consultas ao banco usam SQLAlchemy com parâmetros vinculados. O PostgreSQL
  não publica uma porta no host pelo Compose.
- O CORS permite apenas as origens declaradas em `CORS_ORIGINS`. Respostas da
  API incluem cabeçalhos básicos de proteção e cada requisição é registrada com
  método, caminho, status e duração.
- O container do backend executa com usuário sem privilégios. Segredos locais
  ficam em `.env`, ignorado pelo Git.

## Decisões e premissas

- A listagem de jogadores calcula valor de mercado e aplica filtros/ordenação
  sobre os valores atuais; a paginação é aplicada após esses passos, como exige
  a RN07.
- A ordem alfabética remove acentos e não diferencia caixa; empates são
  resolvidos pelo identificador crescente.
- O contrato continua ativo depois do fim da fidelidade até a venda. A situação
  muda para `ENCERRADO` ou `RESCINDIDO` somente na venda.
- A escalação mantém a formação quando um titular é vendido ou passa a `DOENTE`;
  o titular removido não retorna automaticamente ao elenco de titulares.
- Uma venda sem multa encerra o contrato; havendo multa, ele é rescindido.
- A interface mostra datas no fuso `America/Recife`, compatível com o horário
  fixo de Brasília usado pela API.

## Funcionalidades não implementadas

Nenhuma funcionalidade obrigatória descrita no enunciado ficou de fora. Os
diferenciais opcionais de testes automatizados de frontend e testes de ponta a
ponta não foram implementados.

## Uso de inteligência artificial

Foi utilizado o Copilot SDK no VS Code para auxiliar na leitura da especificação,
na implementação das camadas FastAPI/SQLAlchemy, nas regras de negócio, nos
testes de backend e na interface React/TypeScript. O auxílio foi usado para
acelerar a implementação e revisar consistência entre contrato HTTP e telas.
As sugestões foram conferidas contra o enunciado e os testes; foram alteradas
após validação, inclusive no mapeamento dos campos de atributos, nos nomes das
entidades em português e no cálculo/ordem dos duelos. As decisões finais e os
ajustes pertencem ao autor do projeto.
