# Codex — backend acadêmico mínimo para o Projeto Jacaré Alecrim

## Objetivo e fonte de verdade

Desenvolva **localmente, como projeto independente**, um backend Python/FastAPI para disponibilizar dados históricos e atualizações de medições do ThingSpeak a um futuro dashboard interativo. **Não desenvolva o frontend.**

Repositório de referência: https://github.com/nicoleliecheski/projeto_comp_ubiqua_jacare_alecrim.git

**O comportamento implementado no código desse repositório é a fonte de verdade absoluta.** Antes de começar, leia os arquivos de firmware dos ESP32 e as configurações pertinentes; identifique os canais ThingSpeak, o significado de cada `field`, os formatos de dados, os estados dos atuadores e como as medições são publicadas/consultadas. Em caso de divergência, **prevaleça o código sobre o README e sobre qualquer especificação anterior**. Não altere nem tente corrigir a lógica dos ESP32. Use o `INSTRUCTIONS.md` fornecido apenas como **referência de funcionalidades** (histórico REST + eventos MQTT + WebSocket), descartando exigências incompatíveis com o código real ou desnecessárias para esta demonstração.

É um projeto **exclusivamente acadêmico e de uso local**, sem necessidade de escalabilidade ou manutenção futura. Priorize a menor implementação que funcione, com código legível e testes essenciais; não introduza arquitetura sofisticada.

## Local de trabalho — obrigatório

- Utilize o repositório de referência **somente para leitura/análise**. Se necessário, clone-o em uma pasta separada exclusivamente para inspeção.
- Utilize o **diretório local independente**, fora da árvore do repositório de referência, para todo o código do backend. Não crie `backend/` no repositório original e não altere nenhum de seus arquivos, nem mesmo na cópia local.
- Não faça `git add`, `commit`, `push`, fork, pull request nem publicação em repositório ou serviço remoto. **A entrega será somente a pasta local do backend**, para minha revisão e refinamento antes de decidir onde publicar.
- Antes de escrever arquivos, confirme que o diretório de saída escolhido não pertence à árvore do repositório de referência. Se não conseguir garantir isso, **pergunte onde criar o projeto**.

## Funcionalidades essenciais

1. **Histórico REST:** consulte a API do ThingSpeak para obter os dados históricos e a última medição dos canais realmente utilizados pelo firmware. Exponha:
   - `GET /api/v1/channels` — canais identificados e seus campos, conforme o código/ThingSpeak;
   - `GET /api/v1/channels/{channel_id}/readings` — histórico, com `limit` e filtros `start`, `end` e `field` somente se aplicáveis;
   - `GET /api/v1/channels/{channel_id}/latest` — última medição persistida;
   - `GET /health` — estado básico da API, sem consulta externa.
2. **Atualizações ao vivo:** receba novas medições dos canais via **MQTT Subscribe do ThingSpeak** e as repasse a clientes conectados em **um único WebSocket**: `WS /api/v1/ws/readings`. Para manter o projeto simples, envie cada evento aos clientes conectados e inclua `channel_id` no JSON, sem protocolo individual de subscribe/unsubscribe.
3. **Dados consistentes:** normalize os resultados REST e os eventos MQTT para um JSON simples com `channel_id`, `fields` e, quando existentes, `entry_id` e timestamp original. Preserve o significado e o tipo dos valores utilizados pelo firmware. Não invente campos, IDs ou horários. **Verifique o formato verdadeiro do payload MQTT recebido**, que pode diferir do payload publicado pelos dispositivos.
4. **Tratamento mínimo de falhas:** valide parâmetros e canais configurados; trate respostas inesperadas, timeouts, indisponibilidade do ThingSpeak, mensagens MQTT inválidas e clientes WebSocket desconectados. Use a reconexão do cliente MQTT sem bloquear o funcionamento dos endpoints REST. Encerre recursos ao desligar a API.

O backend será **somente de leitura** em relação ao ThingSpeak: não publique medições, não controle atuadores e não replique a lógica de decisão do firmware.

## Implementação e configuração

- Use **Python 3.12+, FastAPI, Uvicorn, HTTPX e Paho MQTT 2.x**, com `uv`, `pyproject.toml` e `pytest`. Acrescente dependências apenas quando necessárias.
- **Ambiente virtual obrigatório (`venv`):** dentro da pasta independente do backend, crie `.venv` com `python -m venv .venv` (usando Python 3.12 ou superior), ative-o antes de instalar dependências e de desenvolver ou executar o projeto. Utilize `uv sync` para instalar dependências no ambiente virtual do projeto e `uv run` para executar a aplicação e os testes; não instale dependências do projeto no Python global. Inclua `.venv/` no `.gitignore` e documente no README como criar e ativar o ambiente virtual no sistema operacional utilizado.
- Mantenha uma estrutura enxuta: aplicação/rotas, integração com ThingSpeak (REST e MQTT), WebSocket e testes. Use uma única instância do Uvicorn e memória local para as conexões. Não crie camadas artificiais, interfaces abstratas, dispatcher genérico nem infraestrutura de filas elaborada.
- Evite bloquear o event loop e faça a transição dos callbacks do Paho MQTT para o loop assíncrono de forma segura.
- Não inclua banco de dados, persistência local, cache, autenticação de usuários, Docker, microsserviços, CI/CD, observabilidade avançada ou documentação longa. O ThingSpeak é a única fonte persistente de dados.
- Crie `.env` **local** e `.env.example`. **Está autorizado a consultar as constantes e credenciais hardcoded no repositório de referência e utilizar seus valores reais no `.env` local**, quando forem aplicáveis ao backend. Não inclua segredos no `.env.example`, em arquivos versionáveis, no README, em logs ou na resposta final. Inclua `.env` no `.gitignore`.
- Não confunda chaves REST dos canais com credenciais de **MQTT Device**; não presuma que uma substitui a outra. Se as credenciais necessárias não existirem no código ou não forem compatíveis com a operação, **pergunte** em vez de inventar valores.
- Gere apenas um `README.md` curto com instalação, configuração, execução, endpoints, testes e limitações.

## Verificação e conclusão

- Crie testes automatizados objetivos, com mocks dos serviços externos, para histórico/última leitura, entradas inválidas, falhas REST e encaminhamento de eventos MQTT ao WebSocket. Os testes devem funcionar sem rede ou credenciais reais.
- Crie e utilize o `.venv` local, instale as dependências nele, execute testes e verifique a inicialização da API, quando o ambiente permitir. Corrija os erros identificados e repita as verificações relevantes.
- Se houver acesso e credenciais válidas, realize uma verificação real do ThingSpeak; caso contrário, **indique explicitamente que a conectividade real não foi verificada**. Não confunda testes com mocks com integração externa validada.
- Ao concluir, informe somente **o caminho da pasta local criada**, os principais arquivos, endpoints, comandos de execução, resultados reais das verificações e eventuais pendências.

**Regra absoluta contra suposições:** não assuma fatos sobre o firmware, mapeamento de canais, credenciais, payload MQTT, requisitos ou ambiente que não sejam verificáveis no código de referência, neste prompt ou na documentação oficial das APIs. **Se uma informação necessária permanecer incerta ou contraditória, faça uma pergunta objetiva e aguarde a resposta antes de decidir.** Não preencha lacunas com valores fictícios nem escolha silenciosamente um comportamento funcional.
