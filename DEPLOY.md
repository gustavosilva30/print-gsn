# Guia de deploy — GSN Print Service

## Objetivo

Instalar o GSN Print Service em um PC Windows para receber jobs via WebSocket e imprimir etiquetas (Argox OS-214 Plus ou mock).

## 1. Desenvolvimento / homologação (sem impressora)

```bat
pip install -r requirements.txt

REM Terminal 1 — mock do CRM
python tools\mock_websocket_server.py --auto-print

REM Ajuste app\config\config.json:
REM   "server_url": "ws://127.0.0.1:8765"
REM   "token": "demo-token"
REM   "mock_mode": true

REM Terminal 2 — cliente
python -m app.main --tray
```

No mock server, digite `print` para enviar um job. No cliente, confira logs em `app\logs\`.

## 2. Build do executável

```bat
release.bat
```

Saída: `dist\gsn-print-service\`

## 3. Instalador (Inno Setup)

1. Instale [Inno Setup 6](https://jrsoftware.org/isinfo.php)
2. Abra `installer\setup.iss`
3. Compile (Build → Compile)
4. Instalador gerado em `dist\installer\gsn-print-service-setup-0.1.0.exe`

Opções do assistente:

- Instalar como Serviço Windows (recomendado em produção)
- Atalho na área de trabalho
- Abrir tray após instalar

## 4. Produção com Argox

1. Instale o driver Windows da Argox OS-214 Plus
2. Anote o nome exato em Configurações → Impressoras
3. Em `config.json` (pasta de instalação):

```json
{
  "server_url": "wss://seu-crm.exemplo.com/ws",
  "token": "TOKEN_REAL",
  "default_printer": "Nome Exato Da Argox",
  "printer_type": "Argox",
  "command_language": "PPLB",
  "mock_mode": false,
  "auto_reconnect": true
}
```

4. Reinicie o serviço:

```bat
gsn-print-service.exe --stop-service
gsn-print-service.exe --start-service
```

Ou use `services.msc` → GSN Print Service.

## 5. Comandos úteis

| Ação | Comando |
|---|---|
| Tray | `gsn-print-service.exe --tray` |
| Headless | `gsn-print-service.exe --headless` |
| Instalar serviço | `gsn-print-service.exe --install-service` (Admin) |
| Iniciar serviço | `gsn-print-service.exe --start-service` |
| Parar serviço | `gsn-print-service.exe --stop-service` |
| Remover serviço | `gsn-print-service.exe --uninstall-service` |
| Mock CRM | `python tools\mock_websocket_server.py` |

## 6. Checklist de conclusão

- [x] WebSocket profissional
- [x] Fila SQLite + impressão (mock/real)
- [x] Driver Argox configurado
- [x] Tray + configurações
- [x] Windows Service
- [x] Mock server E2E
- [x] Instalador Inno Setup
- [ ] Validação física na Argox do cliente
- [ ] CRM real alinhado a `docs/PROTOCOL.md`

## 7. Logs

- `{app}\app\logs\gsn-print-service.log`
- `{app}\app\logs\printer_operations.log`
