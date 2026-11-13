Criar Backend IoT com FastAPI, ThingSpeak, MQTT e WebSocket

## 1. Papel e objetivo

Atue como um **Engenheiro de Software Backend Sênior**, especializado em Python, FastAPI, arquiteturas assíncronas, MQTT, WebSockets, APIs REST e sistemas IoT.

Sua missão é **criar um projeto backend completo do zero**, utilizando FastAPI, para disponibilizar dados históricos e medições em tempo real de sensores simulados no Wokwi e armazenados no ThingSpeak.

A implementação deve ser funcional, modular, tipada, testável, documentada e preparada para evolução, sem complexidade arquitetural desnecessária.

Você possui autonomia para criar diretórios, arquivos, configurações, testes e documentação.

**Não existe um repositório ou código preexistente.** Crie toda a estrutura necessária.

## 2. Contexto e escopo

Sensores simulados no Wokwi, utilizando ESP32, publicam leituras no ThingSpeak.

Um frontend desenvolvido separadamente utilizará esta API para apresentar dashboards interativos, gráficos históricos e valores de sensores atualizados em tempo real.

A API será responsável por:

1. Conectar-se ao broker MQTT do ThingSpeak.
2. Assinar os canais configurados.
3. Receber e normalizar novas medições.
4. Distribuir as medições para clientes WebSocket conectados.
5. Consultar dados históricos utilizando a API REST do ThingSpeak.
6. Expor contratos HTTP e WebSocket consistentes para consumidores externos.
7. Gerenciar adequadamente conexões, reconexões, erros e ciclo de vida.

### Fora do escopo

Não implementar:

- Frontend ou dashboards visuais.
- Código ou simulações Wokwi.
- Persistência local em banco de dados.
- Redis, Kafka, RabbitMQ ou brokers MQTT próprios.
- Microsserviços.
- Autenticação de usuários com banco de dados, JWT ou OAuth.
- Deploy em serviços de nuvem.
- Sistemas complexos de processamento de eventos.

O ThingSpeak será a única fonte persistente das medições.

## 3. Stack tecnológica

Utilize as seguintes tecnologias:

| Tecnologia | Responsabilidade |
|---|---|
| Python 3.12+ | Linguagem |
| FastAPI | API HTTP e WebSocket |
| Uvicorn | Servidor ASGI |
| Pydantic v2 | Validação e serialização |
| Pydantic Settings | Configuração |
| Paho MQTT 2.x | Cliente MQTT |
| HTTPX | Cliente REST assíncrono |
| pytest | Testes |
| pytest-asyncio | Testes assíncronos |
| Ruff | Lint e formatação |
| uv | Gerenciamento de dependências |
| Docker | Containerização |
| Docker Compose | Execução local containerizada |

Utilize versões estáveis e compatíveis entre si.

Não escolha versões antigas apenas para reproduzir exemplos desatualizados.

Utilize `pyproject.toml` e `uv.lock` para gerenciamento reproduzível das dependências.

## 4. Arquitetura

Utilize uma arquitetura de **monólito modular**, separando infraestrutura, integração externa, contratos de dados e exposição de endpoints.

### Fluxo de eventos em tempo real

```text
Wokwi / ESP32
     |
     | HTTP ou MQTT
     v
ThingSpeak
     |
     | MQTT Subscribe
     v
ThingSpeakMQTTClient
     |
     | Mensagem recebida
     v
SensorMessageParser
     |
     | SensorReading
     v
SensorEventDispatcher
     |
     | Distribuição assíncrona
     v
WebSocketConnectionManager
     |
     | JSON via WebSocket
     v
Frontend
```

### Fluxo de consultas históricas

```text
Frontend
   |
   | GET /api/v1/channels/{id}/readings
   v
FastAPI Router
   |
   v
ThingSpeakService
   |
   v
ThingSpeakRESTClient
   |
   | HTTPS
   v
ThingSpeak REST API
   |
   v
Resposta normalizada
```

### Responsabilidades

**ThingSpeakMQTTClient**
- Gerencia conexão, autenticação, assinaturas e reconexões MQTT.
- Encaminha mensagens recebidas ao processamento.
- Não conhece detalhes de WebSocket.

**SensorMessageParser**
- Interpreta mensagens MQTT.
- Identifica canal e dados.
- Valida e normaliza o conteúdo.
- Não gerencia conexões.

**SensorEventDispatcher**
- Recebe medições normalizadas.
- Encaminha eventos ao gerenciador WebSocket.
- Mantém o fluxo de distribuição desacoplado da biblioteca MQTT.

**WebSocketConnectionManager**
- Gerencia clientes conectados.
- Mantém assinaturas por canal.
- Distribui eventos aos clientes autorizados.
- Controla filas, desconexões e backpressure.

**ThingSpeakRESTClient**
- Executa chamadas HTTP ao ThingSpeak.
- Trata autenticação, timeout e erros externos.
- Não possui responsabilidades de apresentação.

**ThingSpeakService**
- Coordena consultas históricas.
- Normaliza respostas externas.
- Aplica regras simples de validação e filtragem.

Evite criar interfaces abstratas para cada classe apenas por formalidade.

## 5. Estrutura inicial de diretórios

Utilize a estrutura abaixo como referência:

```text
thingspeak-realtime-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── channels.py
│   │       └── websocket.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── sensor.py
│   │   └── websocket.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sensor_service.py
│   │   └── event_dispatcher.py
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── thingspeak/
│   │       ├── __init__.py
│   │       ├── mqtt_client.py
│   │       ├── rest_client.py
│   │       └── parser.py
│   │
│   └── websocket/
│       ├── __init__.py
│       └── connection_manager.py
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_sensor_parser.py
│   │   ├── test_event_dispatcher.py
│   │   └── test_connection_manager.py
│   └── integration/
│       ├── test_rest_api.py
│       ├── test_websocket.py
│       └── test_lifespan.py
│
├── docs/
│   ├── architecture.md
│   ├── api-contracts.md
│   └── thingspeak-setup.md
│
├── .env.example
├── .gitignore
├── .dockerignore
├── .python-version
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── compose.yaml
└── README.md
```

Ajustes pontuais são permitidos quando simplificarem o código.

Não crie arquivos vazios ou módulos sem responsabilidade concreta, exceto quando necessários para a estrutura Python.

## 6. Configuração

Implemente configuração centralizada utilizando Pydantic Settings.

Disponibilize um `.env.example` contendo:

```env
APP_NAME=ThingSpeak Realtime API
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

THINGSPEAK_REST_BASE_URL=https://api.thingspeak.com

THINGSPEAK_MQTT_HOST=mqtt3.thingspeak.com
THINGSPEAK_MQTT_PORT=8883
THINGSPEAK_MQTT_CLIENT_ID=
THINGSPEAK_MQTT_USERNAME=
THINGSPEAK_MQTT_PASSWORD=
THINGSPEAK_MQTT_KEEPALIVE=60

THINGSPEAK_CHANNEL_IDS=12345

THINGSPEAK_HTTP_TIMEOUT=10
THINGSPEAK_READ_API_KEY=

WEBSOCKET_QUEUE_MAX_SIZE=100
WEBSOCKET_MAX_CONNECTIONS=100

CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Requisitos

- Credenciais obrigatórias devem ser validadas.
- Valores sensíveis devem utilizar tipos apropriados, como `SecretStr`.
- A aplicação deve suportar canais públicos e privados.
- Projetar a configuração para permitir diferentes chaves de leitura por canal.
- Não registrar credenciais em logs.
- Nunca enviar credenciais do ThingSpeak ao frontend.
- Configurar CORS explicitamente para os endpoints HTTP.
- Tratar separadamente a verificação de Origin e autorização nos endpoints WebSocket.
- Não adicionar chaves reais ao repositório.

Utilize uma configuração simples para os canais inicialmente. Caso múltiplas credenciais exijam um formato mais estruturado, utilize JSON carregado por variável de ambiente ou arquivo de configuração documentado.

## 7. Integração MQTT

### 7.1. Conexão

Implemente a conexão com:

```text
Host: mqtt3.thingspeak.com
Porta: 8883
Transporte: TCP/TLS
QoS: 0
```

Utilize a autenticação oficial do ThingSpeak MQTT Device:

- Client ID.
- Username.
- Password.

Essas credenciais são diferentes das API Keys de leitura e escrita dos canais.

A assinatura principal será:

```text
channels/{channel_id}/subscribe
```

Crie assinaturas individuais para cada canal configurado.

### 7.2. Comportamento

O cliente deve:

1. Conectar-se ao broker.
2. Autenticar-se.
3. Assinar os canais configurados.
4. Receber mensagens.
5. Validar tópico e payload.
6. Encaminhar os dados ao parser.
7. Publicar eventos normalizados internamente.

Utilize a Callback API atual do Paho MQTT.

### 7.3. Integração com asyncio

O Paho MQTT pode executar callbacks fora do event loop do FastAPI.

Garanta que a transição para o ambiente assíncrono seja thread-safe.

Uma solução aceitável é utilizar `loop.call_soon_threadsafe(...)` para encaminhar eventos a uma fila assíncrona limitada, processada por uma task supervisionada pelo lifespan.

Não execute operações WebSocket diretamente nos callbacks MQTT.

Não crie um event loop independente por mensagem.

### 7.4. Reconexão

Implemente:

- Reconexão automática.
- Backoff exponencial com jitter, dentro de limites configuráveis.
- Restauração das assinaturas após reconexão.
- Registro de erros de autenticação e conexão.
- Estado de conexão consultável pelo health check.
- Encerramento limpo.

Distinga falhas temporárias de configuração inválida.

A reconexão não deve criar múltiplas instâncias concorrentes do cliente MQTT.

### 7.5. Limitações do ThingSpeak

Considere explicitamente:

- QoS 0 não garante entrega.
- O ThingSpeak pode encerrar conexões ociosas.
- Existem limites de assinatura conforme o plano.
- Escritas em lote via Bulk Write não geram as mesmas notificações MQTT Subscribe.
- O ThingSpeak deve continuar sendo a fonte de verdade.

Não implemente garantias de entrega que o protocolo e o serviço externo não oferecem.

## 8. Normalização dos dados

Crie o modelo `SensorReading` com um contrato semelhante a:

```json
{
  "channel_id": 12345,
  "entry_id": 1001,
  "timestamp": "2026-11-09T20:30:00Z",
  "fields": {
    "field1": 27.5,
    "field2": 65.2
  }
}
```

### Requisitos

- `channel_id`: inteiro positivo.
- `entry_id`: inteiro positivo ou nulo.
- `timestamp`: datetime UTC, quando disponível.
- `fields`: dicionário de nomes para valores numéricos, strings ou nulos, conforme o campo.
- Preservar a semântica dos dados recebidos.
- Não converter automaticamente strings não numéricas para números sem uma regra clara.
- Não inventar o `entry_id`.
- Não substituir o timestamp original por horário de recebimento sem distinguir explicitamente as duas informações.

### Parser MQTT

Antes de implementar, confirme na documentação ou em exemplos verificáveis o formato real dos payloads recebidos pelo tópico de assinatura utilizado.

O parser deverá:

- Identificar o canal a partir do tópico.
- Rejeitar canais não configurados.
- Interpretar corretamente o formato de payload.
- Tratar mensagens inválidas.
- Retornar um modelo tipado.
- Não interromper o processamento das próximas mensagens após uma falha.

Se o payload MQTT não fornecer timestamp ou `entry_id`, permita campos nulos e documente a limitação.

Considere incluir um campo adicional `received_at`, separado do timestamp da medição, quando necessário.

## 9. API REST

Utilize o prefixo:

```text
/api/v1
```

### 9.1. Listagem de canais

```http
GET /api/v1/channels
```

Retorne os canais configurados e informações relevantes para o frontend.

Exemplo:

```json
{
  "channels": [
    {
      "id": 12345,
      "name": "Monitoramento Ambiental",
      "fields": {
        "field1": "Temperatura",
        "field2": "Umidade"
      }
    }
  ]
}
```

Não invente metadados caso não estejam configurados ou disponíveis no ThingSpeak.

### 9.2. Consulta histórica

```http
GET /api/v1/channels/{channel_id}/readings
```

Parâmetros:

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `start` | datetime | Início do intervalo |
| `end` | datetime | Fim do intervalo |
| `limit` | int | Quantidade máxima de registros |
| `field` | string | Campo opcional |

Regras:

- Validar datas.
- Exigir `start <= end` quando ambos forem informados.
- Exigir timestamps com timezone e normalizá-los para UTC.
- Aplicar um limite padrão razoável, como 100 registros.
- Impor limite máximo compatível com a API do ThingSpeak.
- Não permitir consulta a canais não configurados.
- Utilizar `httpx.AsyncClient`.
- Retornar erros adequados quando o serviço externo estiver indisponível.

Resposta sugerida:

```json
{
  "channel_id": 12345,
  "count": 2,
  "readings": [
    {
      "channel_id": 12345,
      "entry_id": 1000,
      "timestamp": "2026-11-09T20:29:45Z",
      "fields": {
        "field1": 27.3,
        "field2": 64.8
      }
    },
    {
      "channel_id": 12345,
      "entry_id": 1001,
      "timestamp": "2026-11-09T20:30:00Z",
      "fields": {
        "field1": 27.5,
        "field2": 65.2
      }
    }
  ]
}
```

### 9.3. Última leitura

```http
GET /api/v1/channels/{channel_id}/latest
```

Retornar a última leitura persistida disponível na API REST do ThingSpeak.

Não utilizar exclusivamente o cache de eventos MQTT para esse endpoint.

### 9.4. Erros HTTP

Adotar uma estrutura consistente:

```json
{
  "detail": {
    "code": "THINGSPEAK_UNAVAILABLE",
    "message": "Unable to retrieve sensor readings."
  }
}
```

Utilizar códigos HTTP apropriados para:

- Entrada inválida: 422.
- Canal não configurado: 404.
- Indisponibilidade do serviço externo: 502 ou 503.
- Timeout do serviço externo: 504.
- Erros inesperados: 500.

Não revelar exceções internas, segredos ou URLs contendo API keys.

## 10. WebSocket

### 10.1. Endpoint

```text
WS /api/v1/ws/sensors
```

Defina um protocolo simples de assinaturas por canal.

Após a conexão, o cliente poderá enviar:

```json
{
  "action": "subscribe",
  "channels": [12345, 67890]
}
```

Para cancelar:

```json
{
  "action": "unsubscribe",
  "channels": [67890]
}
```

### 10.2. Confirmação

Quando uma assinatura for aceita:

```json
{
  "type": "subscription.confirmed",
  "channels": [12345, 67890]
}
```

### 10.3. Evento de medição

```json
{
  "type": "sensor.reading",
  "data": {
    "channel_id": 12345,
    "entry_id": 1001,
    "timestamp": "2026-11-09T20:30:00Z",
    "fields": {
      "field1": 27.5,
      "field2": 65.2
    }
  }
}
```

### 10.4. Erros

Utilize um contrato padronizado:

```json
{
  "type": "error",
  "code": "INVALID_CHANNEL",
  "message": "The requested channel is unavailable."
}
```

### 10.5. ConnectionManager

Implemente um gerenciador responsável por:

- Registrar conexões.
- Armazenar assinaturas por conexão.
- Distribuir mensagens somente aos clientes interessados.
- Remover conexões encerradas.
- Isolar falhas de clientes individuais.
- Gerenciar filas de saída limitadas por conexão.
- Impedir crescimento ilimitado de memória.

Cada conexão deve possuir uma fila limitada e uma tarefa dedicada de envio, ou mecanismo equivalente que preserve isolamento.

**Política inicial de backpressure:** ao exceder o limite da fila de um cliente, encerre essa conexão de forma controlada, registre o motivo e permita que o frontend recupere dados via REST após reconectar.

Não descarte silenciosamente eventos sem documentar a política adotada.

### 10.6. Protocolo

- Utilizar JSON.
- Validar mensagens de entrada com Pydantic.
- Rejeitar ações desconhecidas.
- Validar canais solicitados.
- Limitar tamanho das mensagens e quantidade de assinaturas.
- Não permitir que clientes publiquem medições ou comandos MQTT.
- Definir códigos de fechamento WebSocket apropriados.
- Documentar o contrato.

### 10.7. Segurança

Neste primeiro momento, a API poderá operar sem autenticação de usuários, desde que isso seja explicitamente configurável e documentado como adequado apenas a ambientes controlados.

Implemente pelo menos:

- Validação de Origin nos handshakes WebSocket.
- Restrição aos canais configurados e autorizados.
- Limites de conexões.
- Limites de filas.
- Limites de tamanho dos payloads recebidos.

Não confunda configuração de CORS com segurança WebSocket.

## 11. Histórico e sincronização em tempo real

O sistema utilizará dois mecanismos diferentes:

**REST:** recuperação confiável dos dados que já foram persistidos e estão disponíveis no ThingSpeak.

**MQTT:** notificação de novas medições com baixa latência, sem garantia de entrega.

Não implemente persistência local.

### Estratégia recomendada para o frontend

Documente o seguinte fluxo:

1. Conectar ao WebSocket e solicitar assinatura.
2. Receber confirmação da assinatura.
3. Consultar o histórico inicial via REST.
4. Manter temporariamente em memória os eventos WebSocket recebidos durante a consulta.
5. Consolidar histórico e eventos novos.
6. Deduplicar utilizando `channel_id` e `entry_id`, quando presentes.
7. Ordenar as medições pelo timestamp correspondente.
8. Após desconexão, reconectar e consultar novamente o intervalo potencialmente perdido.

O backend deverá fornecer contratos suficientes para permitir esse fluxo.

Como `entry_id` e timestamp podem não estar presentes em todos os payloads MQTT, documente que a deduplicação perfeita pode depender de uma leitura posterior via REST.

Não implementar entrega exatamente uma vez nem sincronização distribuída.

## 12. Ciclo de vida FastAPI

Utilize `lifespan` com `asynccontextmanager`.

Durante o startup:

1. Inicializar configurações.
2. Criar o cliente HTTPX compartilhado.
3. Inicializar o gerenciador WebSocket.
4. Inicializar o dispatcher.
5. Criar as filas e tasks necessárias.
6. Inicializar o cliente MQTT.
7. Iniciar o processo supervisionado de conexão e assinatura.

Durante o shutdown:

1. Impedir novas operações.
2. Encerrar ou sinalizar as conexões WebSocket.
3. Encerrar o cliente MQTT.
4. Cancelar e aguardar tasks supervisionadas.
5. Encerrar o cliente HTTPX.
6. Liberar recursos restantes.

Garanta inicialização idempotente e encerramento previsível.

Uma falha temporária no broker MQTT não deve causar vazamento de tarefas ou conexões.

## 13. Health checks

Disponibilize:

```http
GET /health/live
GET /health/ready
```

### Liveness

Deve indicar se o processo da API está operacional.

Não realizar requisições externas nesse endpoint.

### Readiness

Deve indicar se a instância está apta a fornecer as funcionalidades essenciais, considerando o estado da conexão MQTT e a inicialização dos componentes.

Retornar HTTP 503 quando não estiver pronta, de acordo com a política definida.

Não confundir uma indisponibilidade temporária do ThingSpeak com a necessidade de reiniciar o processo.

Documentar a política de readiness escolhida.

## 14. Logging e observabilidade

Utilize o módulo padrão `logging` ou uma dependência leve, caso justificado.

Registrar:

- Startup e shutdown.
- Conexão MQTT estabelecida.
- Desconexões.
- Tentativas de reconexão.
- Assinaturas MQTT.
- Falhas de parsing.
- Erros em consultas HTTP.
- Número de clientes WebSocket conectados.
- Desconexões causadas por backpressure.

Não registrar:

- Passwords.
- API Keys.
- Tokens.
- Payloads sensíveis.
- URLs que exponham credenciais.

Evitar logs para cada medição em nível INFO. Utilizar DEBUG para detalhes operacionais quando necessário.

## 15. Testes

Criar testes automatizados utilizando pytest.

### Testes unitários

**Parser**
- Payload válido.
- Payload inválido.
- Canal desconhecido.
- Campo ausente.
- Valor nulo.
- Dados não numéricos.
- Timestamp inválido.
- Payload sem identificador de medição.

**Dispatcher**
- Evento válido encaminhado.
- Falha de um consumidor.
- Fila interna cheia.
- Encerramento correto.

**ConnectionManager**
- Múltiplos clientes.
- Assinatura por canal.
- Unsubscribe.
- Remoção de conexão.
- Cliente lento.
- Fila cheia.
- Falha de envio.

### Testes de integração da API

**REST**
- Consulta histórica válida.
- Consulta com intervalo.
- Validação de parâmetros.
- Canal inexistente.
- Timeout HTTP.
- Resposta inválida do ThingSpeak.
- Chave de leitura privada.

**WebSocket**
- Conexão.
- Subscribe.
- Unsubscribe.
- Recebimento de eventos.
- Isolamento por canal.
- Mensagem inválida.
- Desconexão.

**Lifespan**
- Inicialização.
- Encerramento.
- Liberação de recursos.
- Ausência de tasks pendentes.

### Isolamento

Testes automatizados não devem depender de conexão real ao ThingSpeak.

Utilize mocks e fakes para simular o MQTT e a REST API.

Inclua opcionalmente um teste de integração real, desabilitado por padrão e executado somente com credenciais explícitas.

Não considere testes com mocks como comprovação de conectividade real.

## 16. Docker e execução

### Dockerfile

Criar uma imagem:

- Com Python em versão estável.
- Utilizando `uv` para instalação das dependências.
- Com instalação reproduzível a partir do lockfile.
- Executando a aplicação com usuário não-root.
- Com suporte a encerramento por SIGTERM.
- Sem copiar `.env` ou credenciais para a imagem.

### Docker Compose

Criar `compose.yaml` contendo somente a API.

Não incluir banco de dados, Redis ou broker MQTT local.

Expor a porta 8000 para execução local.

Garantir carregamento explícito das variáveis de ambiente.

### Comandos de desenvolvimento

O projeto deverá oferecer comandos documentados equivalentes a:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Testes:

```bash
uv run pytest
```

Lint:

```bash
uv run ruff check .
```

Formatação:

```bash
uv run ruff format .
```

Docker:

```bash
docker compose up --build
```

## 17. Documentação obrigatória

### README.md

Incluir:

1. Objetivo do projeto.
2. Visão geral da arquitetura.
3. Tecnologias.
4. Pré-requisitos.
5. Instalação com uv.
6. Configuração do `.env`.
7. Execução local.
8. Execução com Docker.
9. Como configurar o ThingSpeak.
10. Como testar os endpoints.
11. Como conectar um cliente WebSocket.
12. Como executar os testes.
13. Limitações conhecidas.

### docs/architecture.md

Descrever:

- Componentes internos.
- Fluxo MQTT.
- Fluxo REST.
- Fluxo WebSocket.
- Gerenciamento do ciclo de vida.
- Tratamento de falhas.
- Estratégia de sincronização.
- Restrições de escalabilidade.

### docs/api-contracts.md

Documentar:

- Endpoints HTTP.
- Parâmetros.
- Respostas.
- Erros.
- Mensagens WebSocket.
- Protocolo de assinatura.
- Regras de timestamps e identificação.

### docs/thingspeak-setup.md

Incluir instruções para:

- Criar um canal.
- Configurar seus fields.
- Criar um MQTT Device.
- Obter Client ID, Username e Password.
- Autorizar acesso aos canais.
- Configurar uma Read API Key quando necessário.
- Testar MQTT Subscribe.
- Configurar variáveis de ambiente da API.
- Verificar a chegada de eventos.

Nunca utilizar credenciais reais nos exemplos.

## 18. Critérios de aceite

A implementação será considerada concluída quando:

- [ ] O projeto puder ser instalado utilizando `uv sync`.
- [ ] A aplicação iniciar corretamente.
- [ ] A configuração for validada.
- [ ] O cliente MQTT conseguir estabelecer conexão usando credenciais válidas.
- [ ] Os canais configurados forem assinados.
- [ ] Mensagens MQTT forem normalizadas corretamente.
- [ ] As medições forem distribuídas por WebSocket.
- [ ] Múltiplos clientes conseguirem receber eventos.
- [ ] O isolamento de assinaturas por canal funcionar.
- [ ] O endpoint REST retornar dados históricos.
- [ ] O endpoint REST retornar a última medição.
- [ ] Os health checks funcionarem.
- [ ] A reconexão MQTT for tratada.
- [ ] O encerramento liberar recursos.
- [ ] Os testes automatizados passarem.
- [ ] O Ruff não apontar problemas.
- [ ] A aplicação executar via Docker Compose.
- [ ] A documentação estiver completa.

Os critérios que dependem de credenciais reais devem ser marcados como pendentes de validação externa caso elas não estejam disponíveis.

Não invente resultados de testes.

## 19. Restrições e decisões arquiteturais

Adote obrigatoriamente as seguintes decisões iniciais:

1. Utilizar uma única instância do backend, com um worker Uvicorn.
2. Manter as conexões WebSocket em memória.
3. Utilizar MQTT Subscribe para receber eventos.
4. Utilizar REST para dados históricos.
5. Não armazenar medições no backend.
6. Não implementar event sourcing.
7. Não introduzir infraestrutura distribuída.
8. Não utilizar polling REST como mecanismo principal de tempo real.
9. Não criar classes ou interfaces desnecessárias.
10. Não adicionar funcionalidades não solicitadas.

Documente que a implementação inicial com ConnectionManager em memória não suporta automaticamente distribuição de eventos entre múltiplos workers ou réplicas.

## 20. Plano de execução do agente

Execute o trabalho nesta ordem:

### Fase 1 — Bootstrap

- Criar estrutura do projeto.
- Inicializar `pyproject.toml`.
- Configurar `uv`.
- Adicionar dependências.
- Configurar Ruff e pytest.
- Criar configuração centralizada.
- Criar aplicação FastAPI mínima.

### Fase 2 — Domínio e integração REST

- Criar schemas.
- Implementar REST Client do ThingSpeak.
- Implementar serviço de consulta.
- Implementar endpoints históricos.
- Testar os endpoints.

### Fase 3 — Integração MQTT

- Implementar o cliente Paho MQTT.
- Implementar parser.
- Configurar assinaturas.
- Implementar reconexão.
- Encaminhar eventos ao dispatcher.
- Criar testes.

### Fase 4 — WebSocket

- Implementar ConnectionManager.
- Implementar protocolo de subscribe/unsubscribe.
- Implementar filas por cliente.
- Implementar distribuição de eventos.
- Integrar dispatcher e WebSocket.
- Criar testes.

### Fase 5 — Lifecycle e robustez

- Integrar todos os componentes ao lifespan.
- Implementar shutdown.
- Implementar health checks.
- Implementar logging.
- Verificar tratamento de erros e backpressure.

### Fase 6 — Ambiente e documentação

- Criar Dockerfile.
- Criar Docker Compose.
- Criar `.env.example`.
- Criar README.
- Documentar arquitetura e contratos.

### Fase 7 — Validação final

Executar:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
docker compose build
```

Corrigir os problemas encontrados.

Caso alguma validação não possa ser executada no ambiente disponível, informar explicitamente o motivo.

## 21. Entrega esperada

Ao finalizar, apresentar:

1. Resumo da arquitetura implementada.
2. Árvore de diretórios final.
3. Principais arquivos e responsabilidades.
4. Endpoints HTTP e WebSocket disponíveis.
5. Dependências utilizadas.
6. Comandos de instalação e execução.
7. Instruções de configuração do ThingSpeak.
8. Resultado efetivo dos testes e verificações.
9. Limitações conhecidas.
10. Eventuais etapas pendentes de validação real.

**Não entregue apenas uma proposta, pseudocódigo ou exemplos isolados. Crie efetivamente todos os arquivos necessários para que o projeto seja executável.**

Não solicite confirmação para decisões técnicas que possam ser resolvidas com os requisitos fornecidos.

## 22. Referências oficiais

Consulte, quando necessário:

- ThingSpeak MQTT Basics: https://www.mathworks.com/help/thingspeak/mqtt-basics.html
- ThingSpeak MQTT Subscribe: https://www.mathworks.com/help/thingspeak/subscribetoachannelfeed.html
- ThingSpeak REST: https://www.mathworks.com/help/thingspeak/readdata.html
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
- FastAPI Lifespan: https://fastapi.tiangolo.com/advanced/events/
- Paho MQTT Python: https://eclipse.dev/paho/files/paho.mqtt.python/html/
- HTTPX: https://www.python-httpx.org/
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

## 23. Princípio orientador

O resultado deve ser um backend Python capaz de transformar o ThingSpeak em uma fonte de dados para dashboards personalizados.

O sistema deve oferecer:

**Dados históricos por REST + novas medições por MQTT + distribuição em tempo real por WebSocket.**

Mantenha a implementação simples, robusta, modular e fácil de entender.

Priorize código funcional e testável em vez de complexidade arquitetural desnecessária.