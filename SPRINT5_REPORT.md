# Sprint 5 Report — WebSocket Profissional

## Resumo

A Sprint 5 implementou um cliente WebSocket profissional, reconstruindo a camada de comunicação sobre contrato formal e arquitetura desacoplada. O `WebSocketClient` não conhece mais `JobService` nem `PrintService` diretamente — a rota é `WebSocketClient -> MessageDispatcher -> CommandHandler -> JobService`, permitindo expansão futura para `cancel`, `ping`, `config`, `update` e `restart` sem alterar o núcleo do socket.

## Arquivos criados

| Arquivo | Propósito |
|---|---|
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | Contrato oficial Cliente-Servidor: envelope versionado, tipos de mensagem, estados, códigos de erro e exemplos completos |
| [app/infrastructure/websocket/messages.py](app/infrastructure/websocket/messages.py) | `ProtocolEnvelope` com `from_json`/`to_json`, `build_envelope` helper, `job_status_to_protocol_status` |
| [app/infrastructure/websocket/backoff.py](app/infrastructure/websocket/backoff.py) | `ExponentialBackoff` reutilizável (websocket, updater, downloads) |
| [app/infrastructure/websocket/command_handler.py](app/infrastructure/websocket/command_handler.py) | Handlers desacoplados: `PrintCommandHandler`, `CancelCommandHandler`, `PingCommandHandler`, `ConfigCommandHandler`, `UpdateCommandHandler`, `RestartCommandHandler` |
| [app/infrastructure/websocket/dispatcher.py](app/infrastructure/websocket/dispatcher.py) | `MessageDispatcher` com roteamento por `type` e `default_handler` |
| [tests/test_websocket_client.py](tests/test_websocket_client.py) | Testes do WebSocketClient: lifecycle, send_queue, disconnect, URL validation |
| [tests/test_dispatcher.py](tests/test_dispatcher.py) | Testes do MessageDispatcher: roteamento, tipo desconhecido, default handler |
| [tests/test_messages.py](tests/test_messages.py) | Testes do ProtocolEnvelope: parse, validação, roundtrip, auto-id |
| [tests/test_backoff.py](tests/test_backoff.py) | Testes do ExponentialBackoff: progressão, cap, reset |

## Arquivos alterados

| Arquivo | Alterações |
|---|---|
| [app/infrastructure/websocket/client.py](app/infrastructure/websocket/client.py) | Reescrita completa: conexão persistente, auth, heartbeat, receive loop, sender loop assíncrono, exponential backoff, interruptible sleep, sem dependência de `JobService`/`PrintService` |
| [app/application/application_container.py](app/application/application_container.py) | Singletons para `Settings`, `SQLiteJobRepository`, `JobService`, `PrinterManager`, `PrintService`, `WebSocketClient`. Criação de `MessageDispatcher` com todos os handlers e lazy `send_callback` para envio de respostas |
| [app/application/service_registry.py](app/application/service_registry.py) | Adicionados `register_singleton` e `register_instance` para compartilhamento de estado |
| [app/application/services/job_service.py](app/application/services/job_service.py) | Adicionados `count_pending_jobs`, `get_by_id`, `get_by_remote_message_id`, `get_by_external_job_id`, `cancel` |
| [app/config/settings.py](app/config/settings.py) | Adicionados `protocol_version`, `company_id`, `computer_id`, `connect_timeout_seconds`, `read_timeout_seconds`, `reconnect_*`, `max_pending_outbound_messages`, `service_version`. Persistência automática do `computer_id` via config.json |
| [app/config/config.json](app/config/config.json) | Novos campos de configuração WebSocket |
| [app/domain/job.py](app/domain/job.py) | Adicionados `metadata`, `remote_message_id`, `external_job_id`, `company_id` |
| [app/infrastructure/repository/sqlite_repository.py](app/infrastructure/repository/sqlite_repository.py) | `json.dumps()`/`json.loads()` fiel, novas colunas com `ALTER TABLE` migração, `get_by_id`, `get_by_remote_message_id`, `get_by_external_job_id` |
| [tests/test_print_manager_integration.py](tests/test_print_manager_integration.py) | Corrigido assert de `connected` (bug pré-existente: `disconnect()` no `finally` resetava o estado) |

## Fluxograma

```
┌─────────────────────────────────────────────────────────┐
│ APPLICATION CONTAINER (singletons)                       │
│                                                          │
│  Settings ──► SQLiteJobRepository ──► JobService         │
│     │                                       │            │
│     │                          ┌────────────┘            │
│     ▼                          ▼                         │
│  WebSocketClient          PrintService                   │
│     │                          │                         │
│     │ send_queue                │ process_job()           │
│     ▼                          │                         │
│  sender_loop                   ▼                         │
│     │                     PrinterManager                 │
│     ▼                                                    │
│  ┌──────────────────┐                                    │
│  │ websocket.create  │◄─── ws://...                      │
│  │ _connection       │                                    │
│  └──────┬───────────┘                                    │
│         │ recv()                                          │
│         ▼                                                │
│  MessageDispatcher                                        │
│         │                                                │
│    ┌────┼────────────┬──────────┬────────┐               │
│    ▼    ▼            ▼          ▼        ▼               │
│  print cancel  ping  config  update  restart             │
│    │                                                        │
│    └────► JobService.enqueue() ──► SQLite                   │
│              │                                              │
│              └──► PrintService._loop() ──► process_job()    │
│                                                    │        │
│                                          ┌─────────┘        │
│                                          ▼                  │
│                                    PrinterManager           │
│                                          │                  │
│                                          ▼                  │
│                                     Impressora              │
└─────────────────────────────────────────────────────────┘

SERVIDOR (CRM)
     │
     ├──► PRINT ──► Cliente enfileira e responde ACK
     ├──► CANCEL ──► Cliente cancela job local
     ├──► PING ──► Cliente responde PONG
     ├──► CONFIG ──► Cliente responde STATUS com configuração
     ├──► UPDATE ──► Cliente reconhece comando de update
     └──► RESTART ──► Cliente reconhece comando de restart

CLIENTE
     │
     ├──► AUTH ──► Autenticação na conexão
     ├──► HEARTBEAT ──► Sinal de vida periódico
     ├──► ACK ──► Confirmação de jobs recebidos
     ├──► COMPLETED ──► Job impresso com sucesso
     └──► FAILED ──► Job falhou com razão
```

## Cobertura

| Módulo | Testes | Status |
|---|---|---|
| `WebSocketClient` | `test_websocket_client.py` (4) | Passed |
| `MessageDispatcher` | `test_dispatcher.py` (3) | Passed |
| `ProtocolEnvelope` | `test_messages.py` (6) | Passed |
| `ExponentialBackoff` | `test_backoff.py` (4) | Passed |
| `ApplicationContainer` | `test_container.py` (1) | Passed |
| `Application` | `test_application.py` (1) | Passed |
| `JobService` | `test_job_service.py` (1) | Passed |
| `Settings` | `test_settings.py` (1) | Passed |
| `PrinterManager` | `test_print_manager_integration.py` (6) | Passed |
| `PrinterManager` | `test_printer_manager.py` (1) | Passed |
| Discovery | `test_discovery.py` (1) | Passed |
| Template | `test_template.py` (1) | Passed |
| **Total** | **29** | **Passed** |

## Pendências

- Impressão real via PrintManager com hardware Argox OS-214 Plus
- Serviço Windows (instalação como serviço do sistema)
- Tray (ícone na bandeja com menu de contexto)
- Atualizador automático
- Integração com servidor CRM (lado servidor do WebSocket)
- Corrigir warning `datetime.utcnow()` no `print_manager.py`

## Próxima Sprint

**Sprint 6 — Integração e Validação**

Sugestões para a próxima sprint:

1. Criar um servidor WebSocket mock em Python para testes de integração fim-a-fim
2. Integrar `PrintService` com `PrinterManager` (hoje `process_job()` é simulado)
3. Implementar `completed` e `failed` notifications do cliente para o servidor
4. Adicionar testes de integração `WebSocket -> Dispatcher -> Handler -> JobService -> PrintService`
5. Preparar ambiente de homologação com servidor CRM mock

## Compatibilidade validada

- `pytest`: 29 passed, 1 warning (pré-existente)
- Protocolo documentado em `docs/PROTOCOL.md`
- `computer_id` persistente gerado automaticamente
- Exponential backoff com reset em conexão bem-sucedida
- Thread-safe: `send_queue` + `ws_lock`
- Sem dependência de hardware (mockável)
- Arquitetura extensível: novos comandos = novo `CommandHandler` + `dispatcher.register()`
