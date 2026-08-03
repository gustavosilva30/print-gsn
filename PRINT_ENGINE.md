# Print Engine

## Fluxo
1. O PrintManager resolve a impressora padrão ou a selecionada.
2. O LabelBuilder monta o payload de etiqueta em PPLA/PPLB.
3. O driver correspondente envia o payload para a impressora.
4. O resultado e o erro são registrados em logs.

## Drivers
- Argox
- Zebra
- Brother
- Elgin
- Generic/Windows

## RAW
O fluxo RAW é o canal básico de envio para a impressora. O payload é tratado como bytes e enviado pelo driver.

## PPLA/PPLB
O LabelBuilder gera um payload textual compatível com etiquetas térmicas com base em comandos simples para validação.

## Win32Print
Em ambiente Windows, o driver genérico usa Win32Print para enviar o payload para a impressora selecionada.

## Como adicionar novas impressoras
1. Crie um novo driver em app/infrastructure/printers.
2. Implemente connect, disconnect, print_raw, print_test e print_label.
3. Registre o tipo correspondente em PrinterManager.
