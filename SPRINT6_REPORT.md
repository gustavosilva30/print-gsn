# Sprint 6 Report — Integração de impressão real

## Resumo

O `PrintService` deixa de simular impressão e passa a usar o `PrinterManager` + `LabelBuilder`. Ao concluir ou falhar, envia envelopes `completed` / `failed` pelo mesmo canal WebSocket usado pelos command handlers. O modo `mock_mode` (padrão em config) grava payloads RAW em disco e não depende de hardware.

## Fluxo

```
WebSocket print
  → PrintCommandHandler → JobService.enqueue (SQLite) → ACK
PrintService._loop
  → get_pending_jobs
  → PrinterManager.print_job
       → resolve printer (job / default / mock)
       → LabelBuilder (ou raw/commands do payload)
       → Driver.connect / print_label (× copies) / disconnect
  → update_status PRINTED | FAILED
  → send completed | failed
```

## Arquivos criados / alterados

Ver CHANGELOG.md (Sprint 6).

## Cobertura de testes

- `test_print_service_integration.py`: sucesso + notificação completed; falha + failed; payload estruturado; payload RAW
- Testes existentes de PrintManager / container ajustados
- Total: **33 passed**

## Como validar sem hardware

1. `mock_mode: true` em `app/config/config.json`
2. Enfileirar job (via WebSocket ou teste)
3. Verificar `logs/printer_operations.log` e arquivos em `logs/mock_print_jobs/` (drivers)

## Pendências para produção no PC

1. Windows Service
2. Tray + configuração inicial
3. Instalador completo
4. Teste físico Argox OS-214 Plus (`mock_mode: false`)
5. Servidor CRM alinhado a `docs/PROTOCOL.md`

## Próxima sprint sugerida

Sprint 7 — Serviço Windows + Tray operacional
