# Checklist — PC com Argox (produção)

## Já feito no GSN
- [x] Bridge HTTP `:5555` compatível com mobile-estoque
- [x] Driver Argox / RAW Windows
- [x] Mock mode para homologação
- [x] Tray + configurações + **Guia de configuração**
- [x] Serviço Windows (install/start/stop)
- [x] Instalador Inno Setup (`installer/setup.iss`)

## No PC da impressora (você)
1. Confirmar que a Argox já imprime pelo Windows (driver OK)
2. Anotar o **nome exato** da impressora
3. Instalar o GSN (ou rodar o exe)
4. Configurações:
   - `default_printer` = nome exato
   - `mock_mode` = **false**
   - `local_http_enabled` = true, porta **5555**
   - `websocket_enabled` = **false** (enquanto CRM não tiver WS de print)
5. Tray → **Testar impressão** → papel deve sair
6. `curl http://127.0.0.1:5555/ping` → ok
7. (Recomendado) Instalar como serviço Windows
8. Liberar porta 5555 no firewall (rede privada)
9. Anotar IP do PC para o app mobile

## Config.json de referência (produção)
```json
{
  "default_printer": "Argox OS-214 Plus",
  "printer_type": "Argox",
  "command_language": "PPLB",
  "argox_model": "OS-214 Plus",
  "mock_mode": false,
  "websocket_enabled": false,
  "local_http_enabled": true,
  "local_http_port": 5555,
  "paper_width": 50,
  "paper_height": 25
}
```
