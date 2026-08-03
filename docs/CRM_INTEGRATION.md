# Integração GSN Print Service ↔ CRM Loja (Dourados AP)

## Como o CRM imprime hoje

O app **mobile-estoque** já trata o PC da loja como intermediário:

```text
App mobile / conferência
        │  HTTP POST
        ▼
PC da loja :5555  (raw_print_server.py)
        │  Win32 RAW
        ▼
Argox OS-214 Plus
```

Contrato HTTP atual (`mobile-estoque/src/services/printer.ts`):

- `GET  http://{IP_PC}:5555/ping`
- `POST http://{IP_PC}:5555/print`

Body JSON:

```json
{
  "sku": "35012",
  "nome": "Motor 1.0 Flex",
  "localizacao": "A-12-03",
  "condicao": "Usado",
  "marca": "VW",
  "modelo": "Gol"
}
```

O WebSocket do backend (`/ws`) é só para **WhatsApp**, não para impressão.

## Papel do GSN Print Service

Substitui o `raw_print_server.py` com o **mesmo contrato HTTP**, e ainda oferece:

- mock sem impressora
- fila SQLite
- Windows Service / tray
- WebSocket (para CRM futuro na nuvem)

```text
App mobile  ──HTTP :5555──►  GSN Print Service  ──► Argox
CRM nuvem   ──WS (futuro)──►  GSN Print Service  ──► Argox
```

## Configuração no PC da loja

`app/config/config.json`:

```json
{
  "local_http_enabled": true,
  "local_http_port": 5555,
  "default_printer": "Argox OS-214 Plus",
  "printer_type": "Argox",
  "mock_mode": true,
  "paper_width": 50,
  "paper_height": 25
}
```

No app mobile: **IP do PC da impressora** = IP local do PC (igual ao que já usam).

Não precisa mudar o código do mobile se a porta continuar **5555**.

## Teste sem Argox

```bat
python -m app.main --tray
curl http://127.0.0.1:5555/ping
curl -X POST http://127.0.0.1:5555/print -H "Content-Type: application/json" -d "{\"sku\":\"35012\",\"nome\":\"Teste\",\"localizacao\":\"A1\",\"condicao\":\"Usado\"}"
```

## Evolução futura (opcional)

Para imprimir a partir do CRM web na nuvem (não só rede local):

1. Backend FastAPI publica job de etiqueta (Redis/WS dedicado a print agents)
2. GSN conecta em `wss://api.douradosap.com.br/...` com token da loja
3. Envelope `print` do `PROTOCOL.md` com `content` = dados da peça

Até lá, o intermediário HTTP local já resolve o fluxo de estoque/conferência.
