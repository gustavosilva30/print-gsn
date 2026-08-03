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

## Sprint 6 - Integração de impressão real

### Arquivos alterados
- [app/services/print_service.py](app/services/print_service.py)
- [app/services/print_manager.py](app/services/print_manager.py)
- [app/application/application_container.py](app/application/application_container.py)
- [app/infrastructure/websocket/command_handler.py](app/infrastructure/websocket/command_handler.py)
- [app/infrastructure/printers/argox.py](app/infrastructure/printers/argox.py)
- [app/infrastructure/printers/windows_generic.py](app/infrastructure/printers/windows_generic.py)
- [app/infrastructure/printers/brother.py](app/infrastructure/printers/brother.py)
- [app/infrastructure/printers/elgin.py](app/infrastructure/printers/elgin.py)
- [app/infrastructure/printers/zebra.py](app/infrastructure/printers/zebra.py)
- [app/infrastructure/printers/pdf.py](app/infrastructure/printers/pdf.py)
- [tests/test_container.py](tests/test_container.py)
- [tests/test_print_manager_integration.py](tests/test_print_manager_integration.py)

### Arquivos criados
- [tests/test_print_service_integration.py](tests/test_print_service_integration.py)

### Motivo das alterações
- Conectar o worker de fila (`PrintService`) ao `PrinterManager` e ao `LabelBuilder`.
- Enviar notificações `completed` / `failed` ao servidor via WebSocket.
- Respeitar `mock_mode` (salva payload RAW em arquivo, sem hardware).
- Drivers Argox/Windows Generic com envio RAW real no Windows e mock em outros ambientes.
- Aceitar campos do protocolo (`printer_name`, `content`) no `PrintCommandHandler`.

### Problemas corrigidos
- `process_job()` apenas simulava impressão com `time.sleep`
- Ausência de feedback `completed`/`failed` para o CRM
- Drivers stub sem suporte a `mock`
- `Argox.print_raw` validava payload mas não enviava ao spooler

### Pendências
- Serviço Windows
- Tray
- Atualizador
- Validação física em Argox OS-214 Plus
- Servidor mock WebSocket para E2E completo

### Testes realizados
- `python -m pytest -q`
- Resultado: 33 passed

## Sprint 6.1 - Driver Argox OS-214 Plus

### Arquivos alterados
- [app/infrastructure/printers/argox.py](app/infrastructure/printers/argox.py)
- [app/services/label_builder.py](app/services/label_builder.py)
- [app/services/print_manager.py](app/services/print_manager.py)
- [app/services/print_service.py](app/services/print_service.py)
- [app/config/settings.py](app/config/settings.py)
- [app/config/config.json](app/config/config.json)
- [PRINT_ENGINE.md](PRINT_ENGINE.md)

### Arquivos criados
- [tests/test_argox_driver.py](tests/test_argox_driver.py)

### Motivo
Configurar o driver Argox para o modelo OS-214 Plus com perfil de hardware, PPLA/PPLB corretos, opções de DPI/escuridão/velocidade e configuração persistente.

### Testes
- `python -m pytest -q` → 39 passed

## Sprint 7 - Windows Service + Tray

### Arquivos criados
- [app/infrastructure/windows_service/__init__.py](app/infrastructure/windows_service/__init__.py)
- [app/infrastructure/windows_service/service.py](app/infrastructure/windows_service/service.py)
- [scripts/install_service.py](scripts/install_service.py)
- [tests/test_windows_service_module.py](tests/test_windows_service_module.py)
- [tests/test_tray_module.py](tests/test_tray_module.py)
- [tests/test_main_cli.py](tests/test_main_cli.py)
- [SPRINT7_REPORT.md](SPRINT7_REPORT.md)

### Arquivos alterados
- [app/application/application.py](app/application/application.py)
- [app/main.py](app/main.py)
- [app/ui/tray/tray.py](app/ui/tray/tray.py)
- [app/ui/windows/settings_window.py](app/ui/windows/settings_window.py)
- [app/config/settings.py](app/config/settings.py)
- [app/config/config.json](app/config/config.json)
- [requirements.txt](requirements.txt)
- [tests/test_application.py](tests/test_application.py)

### Motivo
Permitir execução residente com ícone na bandeja e instalação como Windows Service para uso em PCs de produção.

### Como usar
```bash
# Modo tray (interativo)
python -m app.main --tray

# Headless
python -m app.main --headless

# Windows Service (admin)
python -m app.main --install-service
python -m app.main --start-service
python -m app.main --stop-service
python -m app.main --uninstall-service
```

## Sprint 8 - Homologação E2E + Instalador

### Arquivos criados
- [tools/mock_websocket_server.py](tools/mock_websocket_server.py)
- [tests/test_e2e_print_flow.py](tests/test_e2e_print_flow.py)
- [installer/setup.iss](installer/setup.iss)
- [DEPLOY.md](DEPLOY.md)
- [SPRINT8_REPORT.md](SPRINT8_REPORT.md)

### Arquivos alterados
- [app/config/config.json](app/config/config.json) — aponta para mock local `ws://127.0.0.1:8765`
- [gsn_print_service.spec](gsn_print_service.spec)
- [release.bat](release.bat)
- [README.md](README.md)

### Motivo
Fechar o ciclo de homologação sem hardware (mock CRM) e preparar instalador Windows completo com opção de serviço e tray.

## Integração CRM Loja — bridge HTTP :5555

### Arquivos criados
- [app/infrastructure/local_http/print_bridge.py](app/infrastructure/local_http/print_bridge.py)
- [docs/CRM_INTEGRATION.md](docs/CRM_INTEGRATION.md)
- [tests/test_crm_http_bridge.py](tests/test_crm_http_bridge.py)

### Motivo
O CRM mobile-estoque já envia etiquetas via HTTP para `raw_print_server.py` na porta 5555.
O GSN Print Service passa a expor o mesmo contrato e atua como intermediário drop-in.
