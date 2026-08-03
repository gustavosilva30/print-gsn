Você assumirá o desenvolvimento de um projeto existente.



NÃO reescreva a arquitetura.



NÃO gere um novo projeto.



NÃO substitua componentes existentes sem necessidade.



Sua missão é CONTINUAR o desenvolvimento exatamente do ponto onde o projeto parou.



=========================================================

PROJETO

=========================================================



Nome:



GSN Print Service



Objetivo:



Criar um serviço Windows responsável por receber eventos do CRM via WebSocket e imprimir automaticamente etiquetas em impressoras térmicas (inicialmente Argox OS-214 Plus).



O sistema deverá ser reutilizável por diversos clientes e diversos sistemas ERP/CRM.



Arquitetura:



Python



Clean Architecture



Application Container



Dependency Injection



PyInstaller



SQLite



Win32Print



WebSocket



JSON Config



Logs



Thread-safe



=========================================================

FUNCIONAMENTO FINAL ESPERADO

=========================================================



Fluxo completo:



Aplicativo de estoque



↓



CRM



↓



Servidor



↓



WebSocket



↓



GSN Print Service



↓



Fila SQLite



↓



PrintManager



↓



Driver Argox



↓



Impressora



↓



Etiqueta impressa automaticamente



=========================================================

STATUS ATUAL

=========================================================



O projeto NÃO está mais em fase inicial.



Existe uma arquitetura pronta.



O projeto já compila.



O executável é gerado.



Existe Application Container.



Existe ciclo de vida da aplicação.



Existe bootstrap.



Existe PrintManager.



Existe estrutura de drivers.



Existe JobService.



Existe SQLite.



Existe configuração.



Existe sistema de testes.



=========================================================

SPRINTS CONCLUÍDAS

=========================================================



Sprint 1



✔ Ciclo de vida da aplicação



✔ Application



✔ start()



✔ stop()



✔ shutdown()



✔ gerenciamento de threads



✔ logs



✔ compilação funcional



\---------------------------------------------------------



Sprint 2



✔ Application Container



✔ Dependency Injection



✔ Bootstrap organizado



✔ Registro centralizado dos serviços



\---------------------------------------------------------



Sprint 3



(parcial)



Bootstrap reorganizado.



Preparação para integração dos módulos.



\---------------------------------------------------------



Sprint 4



✔ PrintManager



✔ PrinterInfo



✔ PrinterDriver



✔ Driver Argox



✔ Driver Windows Generic



✔ Configuração de impressoras



✔ Integração ao Container



✔ Testes automatizados



=========================================================

TESTES

=========================================================



Todos os testes atuais passam.



pytest



Resultado:



8 passed



Nunca quebre os testes existentes.



=========================================================

AUDITORIA REALIZADA

=========================================================



Já foi feita uma auditoria completa.



Conclusões:



✔ Arquitetura correta



✔ Bootstrap funcional



✔ Application Container funcional



✔ Processo permanece ativo



✔ Threads controladas



✔ Projeto evoluindo incrementalmente



=========================================================

O QUE AINDA NÃO EXISTE

=========================================================



WebSocket completo



Heartbeat



Reconexão



Fila offline



Autenticação



Serviço Windows



Tray



Atualizador



LabelBuilder profissional



Engine de etiquetas



Preview



Diagnóstico



PrintManager completo



Impressão física validada



Drivers completos



Logs avançados



=========================================================

IMPORTANTE

=========================================================



Neste momento NÃO existe impressora instalada.



Portanto:



NÃO dependa de hardware.



Todo desenvolvimento deve funcionar utilizando:



MockPrinter



Mocks de Win32Print



Preview em PNG



Preview em PDF



Payload RAW salvo em arquivo



Testes automatizados



O código deve estar preparado para validar posteriormente em uma máquina com Argox OS-214 Plus.



=========================================================

PRÓXIMA ETAPA

=========================================================



Implementar Sprint 5.



Objetivo:



Criar um WebSocket totalmente profissional.



Requisitos:



\- conexão persistente

\- heartbeat

\- autenticação por token

\- reconexão automática

\- exponential backoff

\- fila offline

\- confirmação de recebimento

\- tratamento de timeout

\- logs detalhados

\- integração com JobService

\- integração com Application Container



NÃO implemente ainda:



Serviço Windows



Tray



Atualizador



=========================================================

REGRAS

=========================================================



Nunca reescreva módulos prontos.



Sempre reutilize a arquitetura existente.



Sempre explique quais arquivos serão alterados.



Sempre justificar cada alteração.



Ao final:



1\. Executar pytest



2\. Garantir que todos os testes continuem passando



3\. Atualizar CHANGELOG.md



4\. Gerar SPRINT5\_REPORT.md contendo:



Arquivos criados



Arquivos alterados



Fluxograma



Cobertura



Pendências



Próxima Sprint



=========================================================

PADRÃO DE CÓDIGO

=========================================================



Utilizar:



\- SOLID

\- Clean Architecture

\- Dependency Injection

\- Interfaces

\- Protocols

\- Dataclasses quando apropriado

\- Tipagem completa

\- Logging estruturado

\- Código documentado

\- Sem duplicação

\- Sem acoplamento desnecessário



Antes de escrever qualquer código, faça uma leitura completa do projeto existente para entender a arquitetura, identifique os pontos de integração e apresente um plano de implementação da Sprint 5. Só então inicie as alterações.

