# GSN Print Service Protocol

## Objetivo

Este documento define o contrato oficial de comunicação entre o CRM/servidor e o GSN Print Service para a Sprint 5.

Nenhuma implementação do cliente WebSocket deve divergir deste contrato sem atualização explícita deste arquivo.

## Escopo

- Transporte: WebSocket
- Serialização: JSON UTF-8
- Versão inicial do protocolo: `1.0`
- Direção da comunicação:
  - Servidor -> Cliente
  - Cliente -> Servidor
- Objetivo inicial:
  - autenticação
  - heartbeat
  - recebimento de comandos
  - enfileiramento de impressão
  - rastreamento de status
  - tratamento de falhas

## Princípios

- Toda mensagem deve usar um envelope único.
- Toda mensagem deve ser versionada.
- Toda mensagem deve possuir identificador único.
- `computer_name` não é identificador estável e não deve ser usado como chave principal.
- O identificador estável do cliente é `computer_id`.
- O token de autenticação faz parte do envelope para simplificar compatibilidade inicial.
- O payload deve preservar estrutura original em JSON.
- Campos desconhecidos devem ser ignorados de forma segura quando a versão do protocolo for compatível.

## Envelope padrão

Todas as mensagens trocadas entre cliente e servidor devem obedecer ao seguinte envelope:

```json
{
  "version": "1.0",
  "id": "34d15184-95b6-4d7b-a4cb-6cb8b1ed95bb",
  "timestamp": "2026-08-02T15:10:00Z",
  "type": "print",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {}
}
```

## Campos do envelope

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `version` | `string` | Sim | Versão do protocolo. Ex.: `1.0`. |
| `id` | `string` | Sim | Identificador único da mensagem. Deve ser UUID. |
| `timestamp` | `string` | Sim | Data/hora em ISO 8601 UTC. |
| `type` | `string` | Sim | Tipo semântico da mensagem. |
| `computer_id` | `string` | Sim | Identificador persistente da estação/serviço. Deve ser UUID estável. |
| `company_id` | `string` | Sim | Identificador da empresa/tenant. |
| `token` | `string` | Sim | Token de autenticação vigente. |
| `payload` | `object` | Sim | Conteúdo específico do tipo de mensagem. |

## Regras gerais

- `id` identifica a mensagem atual, não o job.
- Mensagens relacionadas a um mesmo job devem referenciar `job_id` dentro de `payload`.
- Mensagens relacionadas a uma mensagem anterior devem referenciar `message_id` dentro de `payload`.
- `timestamp` deve sempre ser gerado em UTC.
- `payload` nunca deve ser serializado com `str(...)`.
- Persistência local deve usar `json.dumps(...)`.
- Reidratação deve usar `json.loads(...)`.

## Identidade do cliente

### `computer_id`

- Deve ser gerado uma única vez.
- Deve ser persistido localmente.
- Deve sobreviver a reinicializações da máquina e do serviço.
- Não deve ser recalculado a cada execução.

### `computer_name`

- Pode existir como informação auxiliar dentro do `payload`.
- Não deve ser usado como chave de autenticação, rastreamento ou deduplicação.

Exemplo:

```json
{
  "version": "1.0",
  "id": "bc55697a-1ea4-4a89-a491-8dfb991ee8cc",
  "timestamp": "2026-08-02T15:20:00Z",
  "type": "status",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "computer_name": "PC-ESTOQUE-01",
    "service_version": "0.1.0"
  }
}
```

## Cliente -> Servidor

### `auth`

Usada para autenticar o cliente após conexão ou reconexão.

Payload obrigatório:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `computer_name` | `string` | Não | Nome atual da máquina. |
| `service_version` | `string` | Sim | Versão da aplicação cliente. |
| `capabilities` | `array[string]` | Sim | Capacidades disponíveis. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "2276306d-2bb2-4f59-9e8c-91a98f70b3d3",
  "timestamp": "2026-08-02T15:30:00Z",
  "type": "auth",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "computer_name": "PC-ESTOQUE-01",
    "service_version": "0.1.0",
    "capabilities": [
      "print",
      "cancel",
      "heartbeat",
      "status"
    ]
  }
}
```

### `heartbeat`

Usada para manter a conexão ativa e informar saúde mínima do cliente.

Payload obrigatório:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `status` | `string` | Sim | Estado geral da estação. |
| `queue_size` | `integer` | Sim | Quantidade de jobs pendentes localmente. |

Payload opcional:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `default_printer` | `string` | Não | Impressora padrão configurada. |
| `printer_online` | `boolean` | Não | Disponibilidade local conhecida. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "0c63220e-f521-4d64-9a87-f9c6e84058f2",
  "timestamp": "2026-08-02T15:31:00Z",
  "type": "heartbeat",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "status": "online",
    "queue_size": 2,
    "default_printer": "Argox OS-214 Plus",
    "printer_online": true
  }
}
```

### `ack`

Confirma o recebimento e o enfileiramento de uma mensagem recebida do servidor.

Payload obrigatório:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `message_id` | `string` | Sim | Identificador da mensagem do servidor. |
| `job_id` | `string` | Sim | Identificador local do job gerado. |
| `status` | `string` | Sim | Estado inicial do job. Valor esperado: `queued`. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "db1d4fd2-b1af-4de5-bcc3-485ddc6d8e62",
  "timestamp": "2026-08-02T15:32:00Z",
  "type": "ack",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "message_id": "srv-5ec1118d-7f17-4d5f-940e-5afef91691dc",
    "job_id": "job-1f7e7fbb-0c3a-41f9-8d14-7f5d8f844ddb",
    "status": "queued"
  }
}
```

### `completed`

Informa finalização bem-sucedida do job.

Payload obrigatório:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `job_id` | `string` | Sim | Identificador local do job. |
| `printed_at` | `string` | Sim | Data/hora de conclusão em UTC. |
| `status` | `string` | Sim | Valor esperado: `printed`. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "37f9f08b-2d39-4aad-a442-b96c83984d32",
  "timestamp": "2026-08-02T15:33:00Z",
  "type": "completed",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "job_id": "job-1f7e7fbb-0c3a-41f9-8d14-7f5d8f844ddb",
    "printed_at": "2026-08-02T15:33:00Z",
    "status": "printed"
  }
}
```

### `failed`

Informa falha de processamento ou impressão.

Payload obrigatório:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `job_id` | `string` | Sim | Identificador local do job. |
| `reason` | `string` | Sim | Motivo legível da falha. |
| `code` | `string` | Sim | Código padronizado de erro. |
| `status` | `string` | Sim | Valor esperado: `failed`. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "c29bcfc5-cf57-4e8f-8f52-f07cb74c7139",
  "timestamp": "2026-08-02T15:34:00Z",
  "type": "failed",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "job_id": "job-1f7e7fbb-0c3a-41f9-8d14-7f5d8f844ddb",
    "reason": "Printer offline",
    "code": "PRINTER_OFFLINE",
    "status": "failed"
  }
}
```

### `status`

Usada para publicar estado operacional mais completo.

Payload obrigatório:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `service_status` | `string` | Sim | Estado geral do serviço. |
| `queue_size` | `integer` | Sim | Quantidade de jobs na fila local. |

Payload opcional:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `active_job_id` | `string` | Não | Job atualmente em processamento. |
| `printer_status` | `string` | Não | Estado da impressora. |
| `last_error` | `string` | Não | Último erro relevante. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "aef61c09-88f0-4128-80af-6a1ced9cd15e",
  "timestamp": "2026-08-02T15:35:00Z",
  "type": "status",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "service_status": "running",
    "queue_size": 1,
    "active_job_id": "job-1f7e7fbb-0c3a-41f9-8d14-7f5d8f844ddb",
    "printer_status": "ready",
    "last_error": null
  }
}
```

## Servidor -> Cliente

### `print`

Comando para enfileirar impressão.

Payload obrigatório:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `external_job_id` | `string` | Sim | Identificador do job no CRM/servidor. |
| `printer_name` | `string` | Sim | Nome lógico ou físico da impressora de destino. |
| `template` | `string` | Sim | Template de etiqueta. |
| `copies` | `integer` | Sim | Quantidade de cópias. |
| `content` | `object` | Sim | Dados da etiqueta. |

Payload opcional:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `priority` | `integer` | Não | Prioridade do job. |
| `metadata` | `object` | Não | Dados adicionais do CRM. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "srv-5ec1118d-7f17-4d5f-940e-5afef91691dc",
  "timestamp": "2026-08-02T15:32:00Z",
  "type": "print",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "external_job_id": "crm-000123",
    "printer_name": "Argox OS-214 Plus",
    "template": "default",
    "copies": 1,
    "content": {
      "codigo": "789000111",
      "descricao": "Produto Exemplo",
      "preco": "19,90"
    },
    "priority": 10,
    "metadata": {
      "origin": "crm"
    }
  }
}
```

### `cancel`

Comando para cancelar um job já conhecido pelo cliente.

Payload obrigatório:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `job_id` | `string` | Não | Identificador local do job, quando conhecido. |
| `external_job_id` | `string` | Não | Identificador do job no CRM. |
| `reason` | `string` | Não | Motivo do cancelamento. |

Regra:

- Pelo menos um entre `job_id` e `external_job_id` deve ser informado.

Exemplo:

```json
{
  "version": "1.0",
  "id": "srv-113efca3-22f3-4d72-8596-4d32e745fd15",
  "timestamp": "2026-08-02T15:36:00Z",
  "type": "cancel",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "external_job_id": "crm-000123",
    "reason": "Pedido cancelado"
  }
}
```

### `config`

Comando para atualizar configurações remotas permitidas.

Payload obrigatório:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `changes` | `object` | Sim | Alterações pretendidas. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "srv-b5fd39cf-a44a-4e64-80fd-3c701cb95ae0",
  "timestamp": "2026-08-02T15:37:00Z",
  "type": "config",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "changes": {
      "heartbeat_interval_seconds": 15,
      "default_printer": "Argox OS-214 Plus"
    }
  }
}
```

### `ping`

Comando usado pelo servidor para verificar responsividade imediata.

Payload opcional:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `request_id` | `string` | Não | Identificador auxiliar de correlação. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "srv-bcc19f53-d401-4f85-9c36-c55452aef70c",
  "timestamp": "2026-08-02T15:38:00Z",
  "type": "ping",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "request_id": "health-001"
  }
}
```

### `update`

Comando reservado para acionar fluxo de atualização do cliente.

Payload obrigatório:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `target_version` | `string` | Sim | Versão alvo. |
| `package_url` | `string` | Não | Endereço do pacote. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "srv-21f2906d-c6d8-4ae6-9be3-c60186642d12",
  "timestamp": "2026-08-02T15:39:00Z",
  "type": "update",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "target_version": "0.2.0",
    "package_url": "https://example.com/gsn-print-service-0.2.0.zip"
  }
}
```

### `restart`

Comando reservado para reinício controlado do serviço.

Payload opcional:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `reason` | `string` | Não | Motivo operacional. |
| `delay_seconds` | `integer` | Não | Atraso antes do reinício. |

Exemplo:

```json
{
  "version": "1.0",
  "id": "srv-9f96d487-3b98-4dc9-86d4-26a5576ed0b5",
  "timestamp": "2026-08-02T15:40:00Z",
  "type": "restart",
  "computer_id": "4f5ab1d9-1d95-4d82-93a0-0bc8a0d0c3ef",
  "company_id": "acme-001",
  "token": "demo-token",
  "payload": {
    "reason": "Aplicar nova configuração",
    "delay_seconds": 5
  }
}
```

## Estados padronizados

### Estados do serviço

- `starting`
- `authenticating`
- `online`
- `degraded`
- `offline`
- `stopping`

### Estados do job

- `queued`
- `processing`
- `printing`
- `printed`
- `failed`
- `canceled`

## Códigos de erro padronizados

| Código | Significado |
|---|---|
| `INVALID_MESSAGE` | Envelope inválido ou JSON malformado. |
| `UNSUPPORTED_VERSION` | Versão do protocolo não suportada. |
| `AUTH_FAILED` | Token inválido ou autenticação recusada. |
| `UNAUTHORIZED_COMMAND` | Cliente não autorizado para o comando. |
| `UNKNOWN_COMMAND` | Tipo de mensagem desconhecido. |
| `JOB_NOT_FOUND` | Job não encontrado localmente. |
| `PRINTER_OFFLINE` | Impressora indisponível. |
| `PRINT_ERROR` | Falha genérica de impressão. |
| `CONFIG_INVALID` | Configuração recebida inválida. |
| `TIMEOUT` | Tempo limite excedido. |
| `INTERNAL_ERROR` | Erro interno não classificado. |

## Regras de ACK e rastreabilidade

- Todo comando `print` recebido deve gerar um `ack` após o job ser persistido localmente com sucesso.
- O `ack` não confirma impressão; confirma apenas enfileiramento.
- Quando o processamento terminar com sucesso, o cliente deve enviar `completed`.
- Quando houver falha terminal, o cliente deve enviar `failed`.
- O par `message_id` + `computer_id` deve permitir deduplicação.
- O `job_id` é sempre gerado pelo cliente.
- O `external_job_id` é sempre fornecido pelo servidor quando aplicável.

## Compatibilidade e versionamento

- Mudanças compatíveis devem incrementar versão secundária, exemplo: `1.1`.
- Mudanças incompatíveis devem incrementar versão principal, exemplo: `2.0`.
- Campos opcionais podem ser adicionados sem quebrar clientes existentes.
- Campos obrigatórios novos exigem mudança incompatível de versão.

## Timeouts e expectativas operacionais

- O cliente deve autenticar logo após o estabelecimento da conexão.
- O cliente deve responder a mensagens `ping` com `status` ou `heartbeat`, conforme estratégia definida na implementação.
- O cliente deve enviar `heartbeat` periodicamente enquanto conectado.
- O cliente deve tratar mensagens duplicadas com segurança.
- O cliente deve tratar reconexão sem perda de jobs já persistidos.

## Encaminhamento arquitetural para implementação

Para evitar acoplamento excessivo no cliente WebSocket, a implementação da Sprint 5 deve seguir este fluxo:

```text
WebSocketClient
  -> MessageDispatcher
  -> CommandHandler
  -> JobService
```

Diretrizes:

- `WebSocketClient` conhece conexão, transporte, auth, timeout, heartbeat e reconexão.
- `MessageDispatcher` conhece roteamento por `type`.
- `CommandHandler` conhece casos de uso por comando.
- `JobService` permanece responsável por enfileiramento e status de jobs.

## Itens fora do escopo desta versão

- Serviço Windows
- Tray
- Atualizador funcional completo
- Preview remoto
- Streaming binário
- Assinatura criptográfica avançada

## Observações finais

- Este documento define o contrato-alvo inicial da Sprint 5.
- Ajustes futuros devem ser feitos primeiro neste arquivo e só depois refletidos no código.
