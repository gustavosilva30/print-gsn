# Sprint 8 Report — E2E + Instalador

## Entregas

1. **Mock WebSocket CRM** (`tools/mock_websocket_server.py`)
   - Auth, print sob demanda, ping, log de ack/completed/failed
   - `--auto-print` envia job após autenticação

2. **Teste E2E** (`tests/test_e2e_print_flow.py`)
   - Servidor mock → cliente → ACK → PrintService (mock) → completed

3. **Instalador Inno Setup** (`installer/setup.iss`)
   - Copia build PyInstaller
   - Opção instalar/iniciar Windows Service
   - Atalhos tray/headless
   - Desinstalação remove serviço

4. **DEPLOY.md** — guia completo de homologação e produção

## Como homologar agora (sem impressora)

```bat
pip install -r requirements.txt
python tools\mock_websocket_server.py --auto-print
python -m app.main --tray
```

## Pendência residual (ambiente do cliente)

- Validar impressão física Argox (`mock_mode: false`)
- Conectar ao CRM real (`docs/PROTOCOL.md`)
