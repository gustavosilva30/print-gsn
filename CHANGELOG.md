# CHANGELOG

## Sprint 1 - Serviço residente

### Arquivos alterados
- [app/main.py](app/main.py)
- [app/infrastructure/bootstrap.py](app/infrastructure/bootstrap.py)
- [app/services/print_service.py](app/services/print_service.py)
- [app/infrastructure/websocket/client.py](app/infrastructure/websocket/client.py)
- [app/application/application.py](app/application/application.py)
- [tests/test_application.py](tests/test_application.py)

### Arquivos criados
- [app/application/application.py](app/application/application.py)
- [tests/test_application.py](tests/test_application.py)

### Motivo das alterações
- Implementar um ciclo de vida da aplicação para que o processo permaneça vivo.
- Introduzir um evento de parada compartilhado para encerrar threads de forma controlada.
- Substituir o comportamento de execução efêmera por um fluxo de serviço residente.

### Problemas corrigidos
- encerramento prematuro do processo
- dependência de threads daemon
- ausência de um ponto central de inicialização e parada

### Pendências
- WebSocket totalmente funcional
- impressão real
- tray funcional
- serviço Windows

### Testes realizados
- `python -m pytest -q`
- Resultado: 4 passed

## Sprint 2 - Application Container

### Arquivos alterados
- [app/application/application.py](app/application/application.py)
- [app/application/application_container.py](app/application/application_container.py)
- [app/application/service_registry.py](app/application/service_registry.py)
- [app/application/lifecycle.py](app/application/lifecycle.py)
- [tests/test_container.py](tests/test_container.py)

### Arquivos criados
- [app/application/application_container.py](app/application/application_container.py)
- [app/application/service_registry.py](app/application/service_registry.py)
- [app/application/lifecycle.py](app/application/lifecycle.py)
- [tests/test_container.py](tests/test_container.py)

### Motivo das alterações
- Centralizar a montagem de dependências em um container explícito.
- Reduzir acoplamento entre serviços.
- Preparar a base para a próxima fase de impressão real.

### Problemas corrigidos
- dependência direta entre serviços
- inicialização espalhada pelo bootstrap
- ausência de um mecanismo explícito de dependência

### Pendências
- print manager funcional
- impressão real Argox
- WebSocket operacional real

### Testes realizados
- `python -m pytest -q`
- Resultado: 5 passed

## Sprint 5 - WebSocket Profissional

### Arquivos alterados
- [app/application/application_container.py](app/application/application_container.py)
- [app/application/service_registry.py](app/application/service_registry.py)
- [app/application/services/job_service.py](app/application/services/job_service.py)
- [app/config/settings.py](app/config/settings.py)
- [app/config/config.json](app/config/config.json)
- [app/domain/job.py](app/domain/job.py)
- [app/infrastructure/repository/sqlite_repository.py](app/infrastructure/repository/sqlite_repository.py)
- [app/infrastructure/websocket/client.py](app/infrastructure/websocket/client.py)
- [tests/test_print_manager_integration.py](tests/test_print_manager_integration.py)

### Arquivos criados
- [docs/PROTOCOL.md](docs/PROTOCOL.md)
- [app/infrastructure/websocket/messages.py](app/infrastructure/websocket/messages.py)
- [app/infrastructure/websocket/backoff.py](app/infrastructure/websocket/backoff.py)
- [app/infrastructure/websocket/command_handler.py](app/infrastructure/websocket/command_handler.py)
- [app/infrastructure/websocket/dispatcher.py](app/infrastructure/websocket/dispatcher.py)
- [tests/test_websocket_client.py](tests/test_websocket_client.py)
- [tests/test_dispatcher.py](tests/test_dispatcher.py)
- [tests/test_messages.py](tests/test_messages.py)
- [tests/test_backoff.py](tests/test_backoff.py)
- [SPRINT5_REPORT.md](SPRINT5_REPORT.md)

### Motivo das alterações
- Implementar WebSocket profissional com autenticação, heartbeat, reconexão automática com exponential backoff e fila de envio.
- Introduzir arquitetura de mensagens com `MessageDispatcher` + `CommandHandler` para desacoplar WebSocket do domínio de jobs.
- Padronizar protocolo de comunicação via envelope versionado (`ProtocolEnvelope`) com `computer_id` persistente.
- Corrigir persistência SQLite para `json.dumps()`/`json.loads()` fiel, sem `str(payload)`.
- Adicionar suporte a singletons no `ServiceRegistry` para estado compartilhado consistente.
- Documentar contrato oficial Cliente-Servidor em `docs/PROTOCOL.md`.

### Problemas corrigidos
- WebSocketClient inflado com conhecimento de JobService e PrintService
- payload SQLite serializado como `str()` em vez de JSON fiel
- ausência de deduplicação de mensagens via `remote_message_id`
- ausência de contrato formal entre Cliente e Servidor
- container recriando serviços a cada `resolve()` (sem singletons)
- `connected` verificado após `disconnect()` no teste `test_print_manager_print_test_uses_selected_printer`

### Pendências
- Impressão real via PrintManager (aguardando hardware Argox)
- Serviço Windows
- Tray
- Atualizador
- Integração com CRM (servidor WebSocket)

### Testes realizados
- `python -m pytest -q`
- Resultado: 29 passed
