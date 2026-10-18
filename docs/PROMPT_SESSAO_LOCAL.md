# AMI CONNECT — App Android para o meu Citroën Ami (sessão local no Mac)

## Contexto
Quero criar uma app Android em Kotlin chamada AMI CONNECT. A app lê dados em tempo real do meu Citroën Ami através de um dispositivo ligado à porta OBD, que comunica por Bluetooth. Na app nRF Connect o dispositivo aparece como **R5118926**. A hipótese, ainda por confirmar, é que se trata da caixa DAT@AMI da Citroën.

Esta sessão corre no meu Mac. Tens acesso ao Bluetooth do Mac e ao meu telemóvel Android por USB (adb). Levo o Mac para junto do carro quando for preciso; avisa-me antes.

Atua como engenheiro sénior de Android/Kotlin, Bluetooth (BLE/GATT e Classic/SPP), CAN Bus e engenharia reversa de protocolos.

## O que já tenho

**No Mac (MacBook Air, macOS, Bluetooth integrado):**
- Claude Code (esta sessão).
- Homebrew, git e Python 3.
- Android Studio com o SDK Android, o emulador, o `adb` e o Java incluído. Locais habituais: SDK em `~/Library/Android/sdk` e Java em `/Applications/Android Studio.app/Contents/jbr/Contents/Home`.
- Ambiente virtual Python `.venv` na pasta do projeto, com o `bleak` instalado (ativa-se com `source .venv/bin/activate`).
- scrcpy, para espelhar o ecrã do telemóvel.

**No telemóvel Android (confirma na Fase 0):**
- App nRF Connect, onde vejo o R5118926.
- Opções de programador e depuração USB ligadas, com o telemóvel ligado ao Mac por cabo.
- Registo de rastreio HCI do Bluetooth (HCI snoop log), se já o tiver ativado.

**No repositório `zeusquant/ami-app`, ramo `ccr-5704fc34-nwjmp5` (feito numa sessão anterior):**
- `docs/CAN_REFERENCIA.md`: IDs CAN, taxa do barramento (500 kbit/s) e fórmulas extraídas dos 4 repositórios de referência, com ficheiro e linha de cada informação e as divergências entre eles. Tudo marcado como HIPÓTESE.
- `docs/FASE1_nRF_Connect_instrucoes.md`: guia de descoberta passiva com o nRF Connect.
- `tools/ble_discover.py` e `tools/requirements.txt`: scan BLE, lista de serviços/características com leituras, e escuta de notificações, tudo gravado em JSONL com timestamps. O script nunca escreve em características.
- Ainda **não há dados reais** do dispositivo.

## Referências técnicas
1. https://github.com/servicemensch/TopolinoInfoDisplay
2. https://github.com/flrahe/AMI-Display
3. https://github.com/mreschka/Citroen-AMI-evcc-Connector
4. https://github.com/stwoowts/Citroen-Ami-Opel-Rocks-e-OBD

Já foram analisadas em `docs/CAN_REFERENCIA.md`. Não refazes a análise do zero: lês esse ficheiro, confirmas as citações nos repositórios quando precisares e completas o que faltar. Cita sempre o ficheiro de onde vem cada informação. Não inventes IDs, offsets nem fórmulas.

## REGRAS OBRIGATÓRIAS (prioridade máxima)
- Trabalha só em modo de leitura passiva. Não envias frames CAN, não envias pedidos OBD de escrita, não fazes resets de ECU e não usas comandos de diagnóstico que alterem estado.
- Antes de enviares QUALQUER comando ao dispositivo (incluindo comandos AT de configuração), mostras-me o comando, explicas o que faz e esperas pela minha confirmação.
- Ligar ao dongle, ler características e ativar notificações BLE contam como comandos. Ativar notificações escreve no descritor CCCD do próprio dongle (não no barramento CAN); explicas isso e esperas pela minha confirmação.
- Num adaptador ELM327/compatível, só usas comandos de configuração do próprio adaptador e de monitorização passiva (por exemplo, monitorizar o barramento). Pedidos PID/UDS ao carro só com a minha aprovação explícita, um a um.
- Não contornas autenticação, emparelhamento ou mecanismos de segurança. Se o DAT@AMI estiver fechado/encriptado, paras e propões a alternativa (adaptador WiCAN/ELM327 em modo de escuta).
- Telemóvel por adb: podes ver o ecrã (screencap/scrcpy) livremente. Qualquer toque (`adb shell input`) que ligue ao dongle, leia ou ative notificações segue a regra da confirmação. Nunca tocas em Write (↑) no nRF Connect.
- Não instalas ferramentas novas no Mac nem no telemóvel sem me perguntar.
- Os logs brutos ficam em `logs/` e só vão para o git com a minha autorização (podem conter o VIN).
- Nunca apresentas valores simulados como reais. Na interface, os dados simulados ficam claramente marcados.
- Separas sempre o que está CONFIRMADO (visto no dispositivo e validado com o painel do carro) do que é HIPÓTESE.
- Os testes fazem-se com o carro parado. Não pedes testes durante a condução.
- Git: trabalhas no ramo `ccr-5704fc34-nwjmp5`, com commits pequenos e mensagens claras. Não fazes push para outro ramo.

Primeira tarefa: cria um `CLAUDE.md` na raiz do projeto com estas regras, para valerem em todas as sessões seguintes.

## FASE 0 — Verificar o ambiente (só leitura)
1. `git pull`, confirma o ramo e lê `docs/CAN_REFERENCIA.md` e `tools/ble_discover.py`.
2. Confirma as ferramentas: `bleak` no `.venv`, `adb version`, `adb devices` (telemóvel autorizado?), `scrcpy --version` e o Java/SDK do Android Studio.
3. Diz-me o que falta (por exemplo, autorização de Bluetooth para o Terminal no macOS, ou o telemóvel por autorizar no adb) e espera que eu resolva.

## FASE 1 — Descoberta do dispositivo (ao vivo)
1. Faz um scan BLE no Mac com `tools/ble_discover.py scan`. Lista nome, identificador, RSSI e dados de anúncio de cada dispositivo. No macOS o bleak mostra um UUID em vez do MAC; o MAC vê-se no nRF Connect. Pergunta-me qual é o do carro se houver dúvida.
2. Determina se o dispositivo é BLE, Classic ou dual-mode (pelo nRF Connect e por `system_profiler SPBluetoothDataType`).
3. Se for BLE: lista todos os serviços, características e propriedades (read/notify/write). Lê só as características read e subscreve só as notify/indicate, com a minha aprovação. Regista tudo com timestamps.
4. Se for Classic/SPP: identifica se responde como ELM327 (pedes-me autorização antes do primeiro comando AT de identificação).
5. Se for útil, analisa o HCI snoop log do telemóvel (extraído com `adb bugreport`) para ver que serviços e características a app oficial MyCitroën usa. Só leitura.
6. Faz as capturas em 2 ou 3 estados: carro desligado, ligado em "Ready" e parado, e a carregar (se possível). Antes de cada captura, pede-me os valores do painel: bateria %, autonomia, km e mudança.
7. Grava todos os dados brutos em `logs/` (JSONL/CSV) para análise.
8. Entrega o relatório `docs/FASE1_RELATORIO.md`: o que é o dispositivo, que protocolo usa, se está aberto ou encriptado, que dados chegam sem pedir nada, o que bate com os IDs CAN de `docs/CAN_REFERENCIA.md` e que limitações encontraste.

Paras no fim da Fase 1 e esperas pela minha aprovação.

## FASE 2 — Descodificação
- Cruza os frames capturados com os IDs CAN de `docs/CAN_REFERENCIA.md` e resolve as divergências entre repositórios com os dados reais.
- Cria um descodificador independente e testável, em Kotlin puro (para ser reutilizado na app), com testes unitários que usam os logs reais. Um por sinal: bateria %, velocidade, autonomia, quilometragem, potência/consumo, estado de carregamento, tempo restante de carga e mudança (D/N/R).
- Valida cada sinal comigo contra o painel do carro ou a app MyCitroën. Fazes uma tabela com o sinal, a origem, a fórmula, o estado (confirmado/hipótese) e a nota.

## FASE 3 — App Android de diagnóstico (Kotlin)
- Jetpack Compose, arquitetura MVVM e coroutines/Flow.
- Camada de transporte abstrata (interface) com implementações BLE e Classic/SPP, conforme o que a Fase 1 revelou.
- Pede apenas as permissões necessárias (BLUETOOTH_SCAN, BLUETOOTH_CONNECT e localização só se for mesmo preciso).
- Ecrãs: scan → ligação → serviços/características → log ao vivo com timestamps → exportar log.
- Reconexão automática e tratamento de erros.
- Compilas com Gradle (`./gradlew assembleDebug`) e só instalas no telemóvel com `adb install` depois de eu autorizar.

## FASE 4 — Dashboard
Valores reais confirmados: bateria, autonomia, velocidade, potência/consumo, carregamento e mudança. Usa um design moderno e legível num tablet/telemóvel montado no carro. Os sinais não confirmados não aparecem ou aparecem como "indisponível".

## FASE 5 — Histórico (só depois das anteriores funcionarem)
Base de dados local Room, registo automático de viagens (com GPS do telemóvel), estatísticas diárias/semanais, histórico da bateria e alertas de bateria fraca. Sincronização cloud opcional, no fim.

## Validação final
Testa a estabilidade da ligação, a reconexão, o consumo de bateria do telemóvel e confirma que não há qualquer escrita no barramento. Documenta num README as funcionalidades confirmadas, as limitações e como compilar/instalar.

Começa pela Fase 0. Não avances para a app antes de termos dados reais do dispositivo.
