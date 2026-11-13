# Jacaré Alecrim — backend local

Python 3.12+, FastAPI, HTTPX e Paho MQTT 2.x. Somente leitura; sem frontend,
banco de dados ou controle dos ESP32. Execute um único worker em localhost.

## Instalação e execução (PowerShell)

```powershell
cd C:\Users\Iglesias\source\repos\marco-4-comp-ubiqua
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
# Se uv não estiver instalado, instale-o somente neste ambiente:
python -m pip install uv
uv sync
uv run uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000 --workers 1
# Em outro terminal, com o ambiente ativado:
uv run pytest -q
```

Se a política local impedir ativação, use `Set-ExecutionPolicy -Scope Process Bypass`
nesse terminal. Se houver erro de permissão no cache global do uv, acrescente
`--cache-dir .uv-cache` aos comandos `uv sync` e `uv run`.

## Testar pelo Swagger

Com o servidor iniciado, acesse http://127.0.0.1:8000/docs.
O Swagger já abre com **Try it out** habilitado:

1. Expanda `GET /health` e clique em **Execute**. A resposta esperada é
   HTTP 200 com `{"status":"ok"}`.
2. Execute `GET /api/v1/channels` para listar os canais disponíveis.
3. Para testar o histórico, expanda `GET /api/v1/channels/{channel_id}/readings`,
   informe `channel_id=3499366`, `limit=10` e clique em **Execute**.
   O canal de atuadores é `3540202`. Campos opcionais podem ficar vazios.

Consultas de histórico e última leitura acessam o ThingSpeak. Para canais
privados, preencha `THINGSPEAK_READ_KEY_3499366` e
`THINGSPEAK_READ_KEY_3540202` no `.env` e reinicie o servidor.
As chaves ficam no backend; não precisam ser informadas no Swagger.

O contrato OpenAPI está em http://127.0.0.1:8000/openapi.json.
O Swagger testa HTTP; use um cliente WebSocket para `/api/v1/ws/readings`.
A interface carrega JavaScript e CSS de uma CDN e precisa de acesso à internet.

## Estrutura

```text
src/
  main.py              # Criação da aplicação, lifespan e registro dos routers
  constants.py         # Identificadores dos canais e limites compartilhados
  config.py            # Configuração e mapeamento dos canais
  models/
    live.py            # MQTT e distribuição para WebSockets
  utils/
    reading_normalizer.py        # Validação e normalização das leituras HTTP e MQTT
    thingspeak_readings_client.py # Consulta REST de leituras do ThingSpeak
  routers/
    health.py          # Saúde local
    channels.py        # Catálogo, histórico e última leitura
    readings.py        # Endpoint WebSocket
tests/
  conftest.py          # Fixtures compartilhadas e fábrica de clientes isolados
  test_main.py         # Swagger e contrato OpenAPI
  test_config.py       # Configuração, .env e precedência de variáveis
  models/
    test_live.py       # MQTT, distribuição e encerramento
  utils/
    test_reading_normalizer.py # Normalização e validação das leituras
  routers/
    test_health.py     # Saúde local
    test_channels.py   # Catálogo, histórico, última leitura e erros HTTP
    test_readings.py   # Integração MQTT com múltiplos WebSockets
```

O `.env` permanece na raiz do projeto. O Uvicorn carrega os módulos de `src`
com `--app-dir src`; o pytest usa esse mesmo diretório pelo `pyproject.toml`.

## Configuração

O `.env` local já existe, com valores vazios. Em outra instalação, copie
`.env.example` para `.env`. Preencha as Read API Keys por canal e as três
credenciais de um MQTT Device com permissão Subscribe nos dois canais.
Variáveis do processo prevalecem sobre `.env`. Chaves REST não autenticam MQTT.
Credenciais MQTT parcialmente preenchidas impedem inicialização; todas vazias
permitem executar REST e testes, com aviso de MQTT desabilitado.
Use um Device exclusivo para não disputar o Client ID com os ESP32.

## Fonte e contrato

Mapeamento extraído de `ESP32_Sensores/src/main.cpp` e
`ESP32_Atuadores/src/main.cpp` no
[repositório de referência](https://github.com/nicoleliecheski/projeto_comp_ubiqua_jacare_alecrim).
A cópia de inspeção ficou separada; nenhum firmware foi alterado.

| Canal | field1 | field2 | field3 |
|---|---|---|---|
| 3499366 | temperatura °C | umidade % | gás inflamável PPM |
| 3540202 | ar-condicionado | umidificador | ventilação |

Sensores retornam números decimais. Atuadores retornam inteiros `0` (desligado)
ou `1` (ligado). O estado inicial `2` é interno ao firmware dos sensores e não
é publicado pelos atuadores. Nenhum limiar ou regra de controle é replicado.

O firmware publica `field1=...&field2=...&field3=...`, mas ambos os callbacks
de assinatura interpretam JSON. O backend recebe JSON no tópico
`channels/{channel_id}/subscribe`, usando TLS na porta 8883 e QoS 0, conforme
[MQTT Basics](https://www.mathworks.com/help/thingspeak/mqtt-basics.html) e
[Subscribe](https://www.mathworks.com/help/thingspeak/subscribetoachannelfeed.html).
O formato foi confirmado no código consumidor; captura real MQTT ainda pendente.

REST e WebSocket retornam objetos com `channel_id`, `fields` e, somente quando
recebidos, `entry_id` e `created_at` original. Campos ausentes continuam ausentes;
`null` é preservado. Strings numéricas viram números; strings não finitas como
`nan`, possíveis no DHT, permanecem strings para não inventar valores.
Mensagens malformadas são descartadas sem registrar conteúdo ou segredos.

## Endpoints

- `GET /health`: saúde local, sem consultar ThingSpeak.
- `GET /api/v1/channels`: catálogo derivado do firmware.
- `GET /api/v1/channels/{channel_id}/readings`: lista de leituras;
  `limit=1..8000` (padrão 100), `field=1..3`, `start` e `end` ISO 8601 com fuso.
  Datas são enviadas em UTC; `field` projeta o campo nas entradas retornadas.
- `GET /api/v1/channels/{channel_id}/latest`: última entrada persistida.
- `WS /api/v1/ws/readings`: recebe eventos dos dois canais, sem mensagens de inscrição.
- `/docs`: documentação interativa REST.

Exemplo: `http://127.0.0.1:8000/api/v1/channels/3499366/readings?limit=10&field=1`.
WebSocket: `ws://127.0.0.1:8000/api/v1/ws/readings`.
Histórico e última entrada usam os endpoints oficiais
[Read Data](https://www.mathworks.com/help/thingspeak/readdata.html) e
[Read Last Entry](https://www.mathworks.com/help/thingspeak/readlastentry.html).
Canal desconhecido/sem última leitura retorna 404; parâmetros inválidos, 422;
resposta externa inválida/acesso negado, 502; rede indisponível, 503; timeout, 504.

## Testes e limitações

Tipagem explícita é o padrão em `src/` e `tests/`: parâmetros, retornos,
constantes, atributos e coleções vazias recebem anotações. Coleções declaram
os tipos de seus elementos; contratos de leituras e canais ficam em
`src/models/contracts.py`. Dados externos entram como `object` e passam pela
validação existente. Valores locais com tipo óbvio podem usar inferência.
As regras `ANN` do Ruff exigem anotações nas funções e rejeitam `Any` nas
assinaturas. Essa checagem exige anotações; não substitui um verificador estático
de compatibilidade de tipos.

```powershell
uv run ruff check src tests
uv run ruff format --check src tests
```

Os testes estão separados por router e componente, usando funções pytest e
parametrização para variações do mesmo contrato. `tests/conftest.py` fornece
payloads independentes por teste, respostas esperadas explícitas, `client` com
lifespan ativo e a fábrica `client_for` para cenários com respostas HTTP simuladas.
Use `with client_for(...) as client` para garantir o encerramento dos recursos.
A fixture MQTT fica em `tests/models/test_live.py`, onde é utilizada.

As consultas externas usam `httpx.MockTransport`; chamadas HTTP sem handler
falham imediatamente. Os clientes recebem `Settings()` sem credenciais reais.
Testes de MQTT usam mocks e callbacks, sem acessar o broker. Testes de configuração
substituem a leitura do `.env` e usam `monkeypatch` para isolar variáveis.

```powershell
# Suíte completa, incluindo cobertura de linhas e branches:
uv run pytest --cov --cov-report=term-missing
# Somente o router de canais:
uv run pytest tests/routers/test_channels.py -q
# Relatório navegável em htmlcov/index.html:
uv run pytest --cov --cov-report=html
```

`pytest-cov` é uma dependência de desenvolvimento registrada no lockfile.
A execução com `--cov` exige cobertura mínima de 95%, definida em `pyproject.toml`.
A suíte verifica respostas e erros HTTP, limites e filtros, normalização,
dois WebSockets, reconexão/assinaturas, falhas de envio e encerramento dos recursos.
Cobertura alta não comprova conectividade real nem o funcionamento visual do Swagger.

Conexões ficam em memória. Sem replay, cache ou garantia de entrega MQTT QoS 0;
reconstrua histórico via REST após desconexão. Clientes lentos têm timeout de envio.
O Paho reconecta em segundo plano, sem bloquear REST. Não há autenticação nem CORS
configurado para um frontend ainda inexistente; mantenha a API em localhost.

Verificação externa: ambos os canais responderam HTTP 400 com corpo `-1` na
consulta REST pública. Read API Keys não foram encontradas no firmware.
Leitura autenticada e recepção MQTT real dependem das credenciais pendentes.
