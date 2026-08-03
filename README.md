# GSN Print Service

GSN Print Service é uma aplicação Windows para receber trabalhos de impressão de múltiplos sistemas, enfileirar e imprimir automaticamente em impressoras locais instaladas.

## Arquitetura

- Domain: entidades e regras de negócio
- Application: serviços de caso de uso
- Infrastructure: adaptadores para impressoras, websocket, atualização e repositório
- Presentation: interface tray e telas simples
- Config: configuração e ambiente
- Core: abstrações e utilidades compartilhadas

## Fluxo

1. O serviço inicia e descobre as impressoras instaladas.
2. Registra-se no servidor remoto.
3. Mantém conexão WebSocket.
4. Recebe trabalhos, salva em fila local e imprime quando possível.

## Instalação

```bash
python -m pip install -r requirements.txt
```

## Execução

```bash
python -m app.main
```

## Empacotamento

Windows:

```bat
build.bat
release.bat
```
