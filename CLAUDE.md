# AMI CONNECT — instruções para o Claude Code

App Android (Kotlin) que lê dados em tempo real de um Citroën Ami através de um dispositivo OBD
Bluetooth que aparece no nRF Connect como **R5118926** (hipótese não confirmada: caixa DAT@AMI da Citroën).

- Repositório: `zeusquant/ami-app` (**PÚBLICO**), clone local em `~/ami-app`.
- Ramo de trabalho: `ccr-5704fc34-nwjmp5`.
- Plano completo por fases: `docs/PROMPT_SESSAO_LOCAL.md`.
- Referência CAN (tudo HIPÓTESE até ser validado): `docs/CAN_REFERENCIA.md`. Não refazer a análise do zero;
  confirmar citações nos repositórios de referência quando preciso e citar sempre o ficheiro de origem.
  Não inventar IDs, offsets nem fórmulas.
- Ferramentas: `tools/ble_discover.py` (Python, `bleak` no `.venv`: `source .venv/bin/activate`).

## REGRAS OBRIGATÓRIAS (prioridade máxima)

- Trabalhar só em modo de leitura passiva. Não enviar frames CAN, não enviar pedidos OBD de escrita,
  não fazer resets de ECU e não usar comandos de diagnóstico que alterem estado.
- Antes de enviar QUALQUER comando ao dispositivo (incluindo comandos AT de configuração), mostrar o
  comando ao utilizador, explicar o que faz e esperar pela confirmação.
- Ligar ao dongle, ler características e ativar notificações BLE contam como comandos. Ativar
  notificações escreve no descritor CCCD do próprio dongle (não no barramento CAN); explicar isso e
  esperar pela confirmação.
- Num adaptador ELM327/compatível, usar só comandos de configuração do próprio adaptador e de
  monitorização passiva (por exemplo, monitorizar o barramento). Pedidos PID/UDS ao carro só com
  aprovação explícita do utilizador, um a um.
- Não contornar autenticação, emparelhamento ou mecanismos de segurança. Se o DAT@AMI estiver
  fechado/encriptado, parar e propor a alternativa (adaptador WiCAN/ELM327 em modo de escuta).
- Telemóvel por adb: ver o ecrã (screencap/scrcpy) é livre. Qualquer toque (`adb shell input`) que
  ligue ao dongle, leia ou ative notificações segue a regra da confirmação. Nunca tocar em Write (↑)
  no nRF Connect.
- Não instalar ferramentas novas no Mac nem no telemóvel sem perguntar.
- Os logs brutos ficam em `logs/` (ignorado pelo git) e só vão para o git com autorização do
  utilizador: podem conter o VIN e o repositório é público.
- Nunca apresentar valores simulados como reais. Na interface, os dados simulados ficam claramente
  marcados.
- Separar sempre o que está CONFIRMADO (visto no dispositivo e validado com o painel do carro) do que
  é HIPÓTESE.
- Os testes fazem-se com o carro parado. Nunca pedir testes durante a condução.
- Git: trabalhar no ramo `ccr-5704fc34-nwjmp5`, com commits pequenos e mensagens claras. Não fazer
  push para outro ramo.
- Avisar o utilizador antes de ser preciso levar o Mac para junto do carro.

## Ordem das fases

0. Verificar o ambiente (só leitura).
1. Descoberta do dispositivo ao vivo → `docs/FASE1_RELATORIO.md`. **Parar no fim e esperar aprovação.**
2. Descodificação (descodificador em Kotlin puro + testes com logs reais).
3. App Android de diagnóstico (Compose, MVVM, coroutines/Flow).
4. Dashboard (só sinais confirmados; os outros aparecem como "indisponível").
5. Histórico (Room, viagens, estatísticas), só depois das anteriores funcionarem.

Não avançar para a app antes de haver dados reais do dispositivo. Compilar com `./gradlew assembleDebug`;
`adb install` só com autorização.
