# Sprint 7 Report — Windows Service + Tray

## Resumo

Implementados o modo bandeja do sistema (pystray) e a integração com Windows Service (pywin32), reutilizando `Application` / `ApplicationContainer` sem reescrever a arquitetura.

## Modos de execução

| Modo | Comando | Uso |
|---|---|---|
| Tray | `python -m app.main --tray` | Operador local, menu de status/teste/config |
| Headless | `python -m app.main --headless` | Processo em foreground / scripts |
| Service host | `python -m app.main --service` | SCM do Windows |
| Install service | `python -m app.main --install-service` | Admin Windows |

## Tray

- Ícone gerado em memória (Pillow)
- Menu: Status, Testar impressão, Configurações, Sair
- Fallback headless se pystray/Pillow indisponíveis

## Windows Service

- Nome: `GSNPrintService`
- Display: `GSN Print Service`
- Host inicia `Application.start()` e responde a stop do SCM
- Instalação/remoção protegidas fora do Windows

## Config

- `enable_tray` em settings/config.json

## Pendências

- Validação física Argox
- Instalador Inno Setup apontando serviço + atalho tray
- Assinatura do executável
- Servidor CRM real

## Testes

`python -m pytest -q`
