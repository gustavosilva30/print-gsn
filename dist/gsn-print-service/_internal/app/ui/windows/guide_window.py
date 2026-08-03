from __future__ import annotations

import tkinter as tk
from tkinter import ttk


GUIDE_TEXT = """GSN PRINT SERVICE — GUIA COMPLETO DE CONFIGURAÇÃO
================================================

1) OBJETIVO
-----------
Este programa roda no PC ligado à Argox OS-214 Plus e recebe pedidos de
impressão do app Estoque Mobile (rede local, porta 5555) e, no futuro,
do CRM via WebSocket.

Fluxo atual (loja):
  App mobile  →  HTTP :5555  →  GSN Print Service  →  Argox


2) PRÉ-REQUISITOS NO WINDOWS
----------------------------
• Impressora Argox OS-214 Plus instalada e funcionando no Windows
• Nome da impressora visível em: Configurações → Bluetooth e dispositivos → Impressoras
• Anote o NOME EXATO (ex.: "Argox OS-214 Plus")
• PC e celular do estoque na MESMA rede Wi-Fi / LAN
• Firewall: permitir porta TCP 5555 de entrada (rede privada)


3) CONFIGURAÇÃO BÁSICA (primeira vez)
-------------------------------------
Abra "Configurações" no ícone da bandeja e preencha:

  Impressora padrão     = nome EXATO da Argox no Windows
  Tipo de impressora    = Argox
  Linguagem             = PPLB  (ou o que a Argox já usa hoje)
  Modelo Argox          = OS-214 Plus
  Mock mode             = false   ← IMPORTANTE em produção
  WebSocket             = false   ← deixe false se só usa o app mobile
  HTTP local            = true
  Porta HTTP            = 5555

Salve e reinicie o programa (Sair + abrir de novo, ou reiniciar o serviço).


4) TESTE RÁPIDO NO PC
---------------------
No Prompt de Comando:

  curl http://127.0.0.1:5555/ping

Deve retornar algo como:
  {"ok": true, "printer": "...", "service": "gsn-print-service", "mock_mode": false}

Teste de etiqueta:

  curl -X POST http://127.0.0.1:5555/print -H "Content-Type: application/json" -d "{\\"sku\\":\\"TEST\\",\\"nome\\":\\"Peca\\",\\"localizacao\\":\\"A1\\",\\"condicao\\":\\"Usado\\"}"

Ou use no tray: "Testar impressão".


5) APP ESTOQUE MOBILE
---------------------
1. Abra o app → Configurações
2. IP do PC da impressora = IP deste computador na rede
   (descubra com: ipconfig  → IPv4, ex. 192.168.1.10)
3. Marque "Imprimir etiqueta automaticamente ao cadastrar peça"
4. Salvar & Testar

Ao cadastrar uma peça no mobile, a etiqueta deve sair na Argox.


6) SERVIÇO WINDOWS (produção)
-----------------------------
Para ficar sempre ligado (mesmo sem usuário logado):

  gsn-print-service.exe --install-service
  gsn-print-service.exe --start-service

(Execute o Prompt como Administrador.)

Verificar: services.msc → "GSN Print Service" → Em execução


7) WEBSOCKET (OPCIONAL — CRM nuvem)
-----------------------------------
Só ligue se o backend do CRM tiver endpoint de agente de impressão.

  websocket_enabled = true
  server_url        = wss://api.seu-dominio.com/ws/print-agent
  token             = token combinado com o CRM
  auto_reconnect    = true

Enquanto o CRM não tiver esse endpoint, mantenha websocket_enabled = false
para evitar erros de conexão no log.


8) LOGS E PROBLEMAS
-------------------
Logs:
  pasta_de_instalacao\\app\\logs\\gsn-print-service.log
  pasta_de_instalacao\\app\\logs\\printer_operations.log

Problema                    | Solução
----------------------------|------------------------------------------
curl /ping falha            | Programa/serviço não está rodando
Mobile não acha o PC        | IP errado ou Wi-Fi diferente; liberar 5555
Etiqueta não sai            | mock_mode ainda true? Nome da impressora?
Nome impressora inválido    | Copiar nome EXATO de Impressoras do Windows
Serviço para sozinho        | Ver logs; reinstalar serviço como Admin


9) CHECKLIST "100% PRONTO"
--------------------------
[ ] Argox imprime teste pelo Windows
[ ] mock_mode = false
[ ] default_printer = nome exato da Argox
[ ] local_http_port = 5555 e /ping responde
[ ] Testar impressão no tray OK (papel sai)
[ ] App mobile com IP correto e teste OK
[ ] Cadastro de peça no mobile gera etiqueta
[ ] (Opcional) Serviço Windows em execução automática
[ ] (Opcional) WebSocket só se o CRM tiver o endpoint


10) SUPORTE RÁPIDO
------------------
Documentação no projeto:
  DEPLOY.md
  docs/CRM_INTEGRATION.md
  docs/PROTOCOL.md
"""


class GuideWindow:
    """Guia de configuração embutido (bandeja → Guia de configuração)."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("GSN Print Service — Guia de configuração")
        self.root.geometry("720x560")
        self.root.minsize(560, 400)

        toolbar = ttk.Frame(self.root, padding=8)
        toolbar.pack(fill=tk.X)
        ttk.Label(toolbar, text="Guia completo — leia na ordem", font=("", 11, "bold")).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Fechar", command=self.root.destroy).pack(side=tk.RIGHT)

        frame = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        frame.pack(fill=tk.BOTH, expand=True)

        text = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 10), undo=False)
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.insert("1.0", GUIDE_TEXT)
        text.configure(state=tk.DISABLED)

    def show(self) -> None:
        self.root.mainloop()
