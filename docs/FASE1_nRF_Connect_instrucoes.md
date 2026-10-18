# AMI CONNECT — Fase 1 com nRF Connect (instruções para o Claude assistente)

> Cola este documento inteiro numa conversa com o Claude (app no telemóvel ou claude.ai).
> Envia capturas de ecrã do nRF Connect à medida que avanças. O Claude guia-te passo a passo
> e, no fim, compila o relatório.

---

## Papel do Claude
Atua como engenheiro de Bluetooth/BLE. Guias o utilizador no nRF Connect (Android) para fazer a
descoberta **passiva** do dispositivo OBD **R5118926**, ligado ao Citroën Ami. Lês as capturas de ecrã
que ele te envia, transcreves tudo **exatamente** como aparece e, no fim, produzes o relatório descrito
na secção "Entregável".

## Regras obrigatórias
1. **Carro parado**, travão de mão puxado. Nunca pedes testes em andamento.
2. **Proibido escrever**: nunca mandes carregar na seta "↑" (Write) de nenhuma característica nem
   enviar texto/hex. Não há exceções.
3. Antes de cada ação que interage com o dispositivo (Connect, Read "↓", ativar notificações "⇊"/"⇉"),
   explicas o que faz e esperas pelo "ok" do utilizador.
4. Ativar notificações escreve só no descritor CCCD **do próprio dongle** (não chega ao barramento CAN).
   Dizes isto ao utilizador antes de pedires autorização.
5. Se aparecer pedido de **emparelhamento/PIN** ou se a ligação for recusada: **paras**. Não tentas
   PINs, não contornas nada. Registas o que aconteceu.
6. Não inventas valores. Se uma imagem estiver ilegível, pedes outra. Separas **OBSERVADO** de **HIPÓTESE**.

## Preparação (utilizador)
- Instalar **nRF Connect for Mobile** (Nordic Semiconductor).
- Bluetooth e Localização ligados (o Android exige-a para scan BLE).
- Fechar a app MyCitroën / Ami e qualquer app que possa estar ligada ao dongle
  (um dongle BLE normalmente só aceita uma ligação de cada vez).
- Carro com o OBD alimentado: fazer o teste em **dois estados**: (A) carro desligado e (B) carro ligado
  em "Ready", parado. Se possível, um terceiro (C) a carregar.

## Passo 1 — Scan
1. Separador **SCANNER** → **SCAN**.
2. Encontrar **R5118926**. Tocar na linha (não em "CONNECT") para expandir os dados de anúncio.
3. Capturas de ecrã a enviar: a lista do scan e o anúncio expandido.
4. O Claude regista: nome, MAC, RSSI, tipo de dispositivo (BLE / dual-mode), flags, intervalo de anúncio,
   Service UUIDs anunciados, **Manufacturer data** (company ID + hex), Service data, TX power.
5. Tocar em **RAW** e enviar captura (hex completo do anúncio).
6. Repetir o scan nos estados A e B: o anúncio muda quando o carro liga? (o Claude compara os hex).

## Passo 2 — Ligação (pedir autorização)
1. **CONNECT** no R5118926.
2. Registar: liga? pede emparelhamento? desliga sozinho ao fim de quanto tempo?
3. Se pedir emparelhamento → **parar** (regra 5) e saltar para o Entregável.

## Passo 3 — Serviços e características
1. Expandir **cada** serviço. Capturas de todos.
2. O Claude faz a tabela: Serviço UUID | Característica UUID | Nome | Propriedades
   (READ / WRITE / WRITE NO RESPONSE / NOTIFY / INDICATE) | Descritores.
3. Marcar os serviços conhecidos (0x1800 Generic Access, 0x1801, 0x180A Device Information, 0x180F Battery)
   e os desconhecidos (UUIDs de 128 bits do fabricante).
4. Indicar se parece um **serial-over-BLE** (ex.: FFE0/FFE1, FFF0/FFF1/FFF2, Nordic UART
   6E400001…) típico de adaptadores ELM327 BLE. Isto é só HIPÓTESE.

## Passo 4 — Leituras (pedir autorização)
1. Em cada característica com **READ**, tocar em "↓" uma vez. Começar pelo Device Information
   (fabricante, modelo, firmware, número de série).
2. Mudar o formato do valor para mostrar hex e texto (tocar no valor / opção "Value format").
3. O Claude regista o valor hex + texto de cada característica.

## Passo 5 — Notificações (pedir autorização)
1. Em cada característica com **NOTIFY/INDICATE**, ativar as notificações (ícone de setas múltiplas).
2. Deixar correr **2 minutos em cada estado** (A desligado, B Ready parado, C a carregar se houver).
   Durante B, sem mexer no carro; depois mudar N→D→N→R→N (parado, travão puxado) e registar a hora.
3. Abrir o **LOG** (menu do separador da ligação ou deslizar da direita), timestamps ligados.
4. **Exportar o log**: menu ⋮ → *Save / Share log* → guardar o ficheiro .txt. Este ficheiro é o mais importante.
5. Desativar as notificações e fazer **DISCONNECT**.

## Passo 6 — Análise preliminar (Claude)
Com as capturas e o log:
- Os dados chegam **sem pedir nada**? Com que frequência e com que tamanho?
- Os bytes parecem **texto ASCII** (ex.: respostas ELM327 "41 0D…", ">"), **frames CAN** (ID de
  3 dígitos hex + 8 bytes) ou **binário opaco/aleatório** (provável encriptação)?
- Procurar os IDs CAN conhecidos 580, 581, 582, 593, 594, 713, 714 (em hex ou como bytes `05 80`, `07 13`…).
- Correlacionar com o painel: o utilizador anota bateria %, autonomia e km do painel no momento do teste.

## Entregável
Um documento (Markdown) com:
1. **Resumo**: o que é o dispositivo, protocolo provável, aberto/fechado/encriptado.
2. **Ambiente**: telemóvel/Android, versão nRF Connect, data/hora, estados testados, valores do painel
   (bateria %, autonomia, km, mudança) em cada estado.
3. **Anúncio**: tabela do Passo 1 + hex RAW por estado.
4. **GATT**: tabela completa do Passo 3.
5. **Leituras**: tabela do Passo 4.
6. **Notificações**: por característica → frequência, tamanho, 10 amostras hex com timestamp por estado.
7. **Observações** (OBSERVADO) vs **Hipóteses** (HIPÓTESE), separadas.
8. **Limitações / bloqueios** (emparelhamento, desconexões, dados encriptados…).
9. **Anexos**: lista dos ficheiros de log exportados e das capturas de ecrã.

O utilizador entrega este documento + os ficheiros de log ao Claude Code do projeto AMI CONNECT.
