# Print Engine

## Fluxo
1. O PrintManager resolve a impressora padrão ou a selecionada.
2. O LabelBuilder monta o payload de etiqueta em PPLA ou PPLB.
3. O driver correspondente envia o payload para a impressora (RAW / Win32).
4. O resultado e o erro são registrados em logs.

## Driver Argox (OS-214 Plus)

Perfil padrão:
- Modelo: `OS-214 Plus`
- DPI: `203`
- Linguagem de comando: `PPLB` (compatível ZPL-II via RAW)
- Escuridão: `10`
- Velocidade: `3`
- Tamanho de etiqueta sugerido: `50x30` mm

Configuração em `app/config/config.json`:

```json
{
  "default_printer": "Argox OS-214 Plus",
  "printer_type": "Argox",
  "command_language": "PPLB",
  "argox_model": "OS-214 Plus",
  "argox_dpi": 203,
  "argox_darkness": 10,
  "argox_speed": 3,
  "paper_width": 50,
  "paper_height": 30,
  "mock_mode": true
}
```

### Mock
Com `mock_mode: true` o driver grava o payload em `logs/mock_print_jobs/` e no log de operações, sem depender de hardware.

### Produção (Windows)
1. Instale o driver Windows da Argox OS-214 Plus.
2. Anote o nome exato da impressora no Windows.
3. Defina `default_printer` com esse nome.
4. Defina `mock_mode: false`.
5. O envio é feito em modo **RAW** via Win32Print.

### PPLB vs PPLA
- **PPLB** (padrão): sintaxe compatível com ZPL-II (`^XA` … `^XZ`). Recomendado para OS-214 Plus.
- **PPLA**: conjunto clássico Argox/Datamax (`I8,A,001` … `P1`). Use se o firmware estiver em PPLA.

## Drivers
- Argox
- Zebra
- Brother
- Elgin
- Generic/Windows

## RAW
O fluxo RAW envia bytes diretos ao spooler, sem renderização GDI.

## Como adicionar novas impressoras
1. Crie um novo driver em `app/infrastructure/printers`.
2. Implemente `connect`, `disconnect`, `print_raw`, `print_test` e `print_label`.
3. Registre o tipo correspondente em `PrinterManager`.
