# Arquitetura GSN Print Service

## Camadas

- Domain: entidades, status e contratos de impressoras
- Application: serviços de fila e fluxo de impressão
- Infrastructure: repositório SQLite, WebSocket, discovery de impressoras e atualização
- Presentation: interface tray e janelas simples
- Config: configurações e logging
- Core: utilidades compartilhadas

## Fluxo de impressão

1. O serviço inicia e carrega as configurações.
2. O bootstrap inicializa logging, fila e cliente WebSocket.
3. O WebSocket recebe um payload e cria um job na fila local.
4. A fila é persistida em SQLite e processada por um worker de impressão.
