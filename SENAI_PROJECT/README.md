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

O backend carrega as variáveis do `.env` na raiz do projeto e pode ser iniciado
localmente com `uvicorn main:app --reload` a partir de `back-end`. Para esse
modo, configure `DATABASE_URL` para o PostgreSQL local e aplique a migração
versionada antes de iniciar a API.

## Executar e testar no Windows sem Docker

Este roteiro executa PostgreSQL, API e interface como processos locais. Não é
necessário instalar nem iniciar Docker ou Docker Compose.

### Requisitos

- Python 3.14, com o inicializador `py` disponível no PowerShell.
- PostgreSQL 18 instalado e em execução na porta `5432`.
- Node.js 22 e npm.
- `psql` disponível no `PATH` (ou use o Query Tool do pgAdmin para as instruções
  SQL abaixo).

Confira as versões:

```powershell
py -3.14 --version
psql --version
node --version
npm --version
```

Se o serviço PostgreSQL não estiver iniciado, localize-o e inicie-o pelo
Windows Services (`services.msc`). O nome do serviço varia conforme a
instalação; `Get-Service *postgres*` mostra os nomes disponíveis. Se necessário,
abra o PowerShell como administrador para iniciar o serviço.

### Preparar usuário e banco PostgreSQL

O `.env` configura a conexão usada pela aplicação, mas **não altera a senha
armazenada no PostgreSQL**. Se a senha configurada localmente não for conhecida
ou não corresponder à do `.env`, conecte-se ao servidor pelo pgAdmin usando uma
conta administrativa válida e, no Query Tool, defina a senha do role que será
usado pela aplicação:

```sql
ALTER ROLE postgres WITH PASSWORD 'SUA_SENHA_LOCAL';
```

Substitua `SUA_SENHA_LOCAL` pela senha local desejada. Não use essa senha em
produção nem a adicione ao Git. Crie o banco `senai` apenas se ele ainda não
existir. Pelo PowerShell, com `createdb` disponível:

```powershell
createdb -W -U postgres -h localhost -p 5432 senai
```

O parâmetro `-W` solicita a senha. Se o banco já existir, não execute novamente
o comando de criação. Alternativamente, crie-o pelo pgAdmin.

Na raiz de `SENAI_PROJECT`, crie o arquivo local `.env` caso ainda não exista,
copiando `.env.example`, e ajuste `DATABASE_URL` para o servidor local:

```powershell
Copy-Item .env.example .env
notepad .env
```

Use esta forma para a URL e troque `SENHA_URL_ENCODED` pela senha definida no
PostgreSQL (percent-encode caracteres reservados da URL):

```text
DATABASE_URL=postgresql+psycopg://postgres:SENHA_URL_ENCODED@localhost:5432/senai
```

Não sobrescreva um `.env` já existente. O arquivo `.env` é local e não deve ser
versionado. Aplique o esquema somente em um banco vazio/recém-criado:

```powershell
psql -W -U postgres -h localhost -p 5432 -d senai -f "E:\Desafios_S\SENAI_PROJECT\script_sql\001_initial_schema.sql"
```

Se o projeto estiver em outra pasta, ajuste o caminho do arquivo SQL. A migração
não deve ser aplicada de novo sobre tabelas já existentes. Para conferir a
conexão e o banco antes de iniciar a API:

```powershell
psql -W -U postgres -h localhost -p 5432 -d senai -c "SELECT current_user, current_database();"
```

Se `psql` não for reconhecido, adicione a pasta `bin` da instalação do
PostgreSQL ao `PATH`, ou execute `psql.exe` pelo caminho completo, normalmente
`C:\Program Files\PostgreSQL\18\bin\psql.exe`.

### Iniciar o backend

No primeiro terminal do PowerShell, entre na raiz `SENAI_PROJECT` e crie o
ambiente virtual:

```powershell
Set-Location "E:\Desafios_S\SENAI_PROJECT"
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r back-end\requirements-dev.txt
```

Se a ativação do ambiente for bloqueada pela política do PowerShell, permita
scripts somente para o terminal atual e tente ativá-lo novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Confirme a conexão com o banco. Execute a partir da pasta `back-end`:

```powershell
Set-Location .\back-end
python -c "from sqlalchemy import text; from app.database import engine; conn=engine.connect(); print(conn.execute(text('SELECT current_user, current_database()')).one()); conn.close()"
```

Inicie a API nesse mesmo terminal:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Mantenha o terminal aberto. A documentação interativa da API fica em
<http://localhost:8000/docs>.

### Iniciar o frontend

Abra um segundo terminal do PowerShell:

```powershell
Set-Location "E:\Desafios_S\SENAI_PROJECT\frontend1"
npm ci
npm run dev
```

Mantenha esse terminal aberto. Acesse a aplicação em
<http://localhost:5173>. No desenvolvimento, a interface usa por padrão a API
em `http://localhost:8000/api/v1`. Se a API ou o frontend estiverem em outras
portas, ajuste `DATABASE_URL`/`VITE_API_URL` e `CORS_ORIGINS` conforme necessário
(reinicie os processos após mudar variáveis de ambiente).

### Testes automatizados

Os testes do backend usam SQLite em memória; portanto, `pytest` não depende do
PostgreSQL local. Com o ambiente virtual ativado:

```powershell
Set-Location "E:\Desafios_S\SENAI_PROJECT\back-end"
python -m pytest -q
```

Verifique também lint e build do frontend:

```powershell
Set-Location "E:\Desafios_S\SENAI_PROJECT\frontend1"
npm run lint
npm run build
```

### Teste manual da API

Com PostgreSQL e os dois servidores em execução, abra
<http://localhost:8000/docs>. Use `POST /api/v1/players` com um jogador válido:

```json
{
  "name": "Rui Prado",
  "position": "MEI",
  "agility": 70,
  "age": 25,
  "pace": 70,
  "shooting": 70,
  "passing": 70,
  "dribbling": 70,
  "defending": 70,
  "physical": 70,
  "potential": 70
}
```

A API deve responder `201`, atribuir condição `APTO` e calcular `overall` 70,
`base_value` 30,00 e `market_value` 30,00. O nome deve ter pelo menos duas
palavras e não conter números. Em seguida, consulte `GET /api/v1/players/{id}`:
o valor base permanece gravado e o overall/valor de mercado são calculados na
consulta.

Para testar compra, venda e histórico, crie um clube com `POST /api/v1/clubs`:

```json
{
  "name": "Aguias FC",
  "acronym": "AGU"
}
```

Anote os `id` retornados. Faça `POST /api/v1/players/{id}/buy` com o id do clube
criado e uma data futura (até 1.095 dias) em `loyalty_until`, por exemplo:

```json
{
  "club_id": 1,
  "loyalty_until": "2030-01-01T12:00:00-03:00"
}
```

Use o id real do clube e uma data que ainda esteja no futuro. Confira o elenco
em `GET /api/v1/clubs/{id}`, venda o jogador com
`POST /api/v1/players/{id}/sell` e consulte
`GET /api/v1/clubs/{id}/transactions` para verificar os lançamentos da compra e
venda. A interface web oferece os mesmos fluxos pelas telas de jogadores,
clubes e mercado.

### Testar escalação e partida

Para testar o fluxo completo, crie dois clubes e cadastre cinco jogadores livres
para cada um, nas posições `GOL`, duas posições entre `ZAG`/`LAT`, `MEI` e
`ATA`. Pode reutilizar os atributos do exemplo acima, variando nomes (sempre
duas palavras) e posição. Compre os jogadores para seus clubes, configure cada
escalação com `PUT /api/v1/clubs/{id}/lineup` usando a formação `2-1-1` e os cinco
ids correspondentes:

```json
{
  "formation": "2-1-1",
  "player_ids": [1, 2, 3, 4, 5]
}
```

Os ids são exemplos: use os ids reais dos jogadores que pertencem ao clube.
Depois envie `POST /api/v1/matches`:

```json
{
  "home_club_id": 1,
  "away_club_id": 2
}
```

Use os ids reais dos dois clubes. Confira o resultado e os duelos em
`GET /api/v1/matches/{id}` e a classificação em `GET /api/v1/standings`. O
Swagger descreve todos os endpoints e os formatos de resposta.

### Problemas comuns

- **Falha de autenticação:** confirme que a senha do role PostgreSQL coincide
  com `DATABASE_URL`. Editar `.env` não altera a senha configurada no servidor.
- **Conexão recusada ou timeout:** verifique se o serviço PostgreSQL está
  iniciado, se o host/porta em `DATABASE_URL` são `localhost:5432` e se o banco
  `senai` existe.
- **Erro de tabela inexistente:** aplique `script_sql\001_initial_schema.sql`
  uma vez em um banco vazio.
- **Frontend não alcança a API:** mantenha ambos os processos ativos, confira
  <http://localhost:8000/docs> e confirme que `CORS_ORIGINS` inclui
  `http://localhost:5173`.
- **Porta ocupada:** inicie o serviço na porta livre e ajuste também a URL da
  API no frontend e as origens CORS.

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
