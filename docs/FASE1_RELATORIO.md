# AMI CONNECT — Relatório da Fase 1 (RASCUNHO)

Estado: **rascunho de 2026-10-18**. Está capturado só um estado do carro, e esse estado não foi registado:
os valores do painel não foram fornecidos. Faltam as capturas com o carro em "Ready" e a carregar
(secção 9).

Legenda:
- **OBSERVADO**: visto no dispositivo ou no telemóvel.
- **CONFIRMADO**: observado e validado com o painel do carro. Ainda não há nenhum.
- **HIPÓTESE**: interpretação por validar.

## 1. Resumo

| Pergunta | Resposta |
|---|---|
| O que é o dispositivo? | Periférico **só BLE**, com chip/stack **Nordic Semiconductor**, Bluetooth 4.2, com o nome anunciado "R5118926". Não expõe o serviço Device Information. HIPÓTESE: é o dongle Bluetooth oficial do Ami, que o EVCC descreve na porta OBD a trabalhar com a app da Citroën (`mreschka/Citroen-AMI-evcc-Connector`, `README.md:38`, "AMI-Bluetooth-Dongle"). Fabricante e modelo por confirmar. |
| Que protocolo usa? | GATT com **um único serviço próprio** e **uma única característica WRITE + INDICATE**. A forma é a de um canal de pedido/resposta (HIPÓTESE). O protocolo da aplicação é desconhecido. |
| Aberto ou encriptado? | A ligação BLE **não pede emparelhamento nem encriptação** (OBSERVADO). Não se sabe se a camada da aplicação é encriptada, porque não chega nenhum dado para analisar. |
| Que dados chegam sem pedir nada? | Só os **anúncios**: Service Data `0x27D5` com dois conteúdos que alternam e não mudaram em 75 min. Nas indicações chegaram **0 mensagens em 120 s**. |
| Bate com `docs/CAN_REFERENCIA.md`? | **Não.** Nenhum dado observado contém IDs CAN (0x580, 0x581, 0x582, 0x593, 0x594, 0x713, 0x714) nem valores reconhecíveis. |
| A MyCitroën usa o dispositivo? | **Hoje não.** A MyCitroën só se ligou a um botão Flic (o utilizador confirmou) e nunca ao R5118926 (secção 7). Não se sabe se o faz noutras condições, por exemplo com o carro ligado ou noutro ecrã da app. |

Conclusão provisória: **o R5118926 não entrega dados do carro de forma passiva.** Para tirar dados dele
seria preciso escrever comandos de um protocolo desconhecido na característica 0x2701. As regras do projeto
(`CLAUDE.md`) não o permitem. A alternativa está na secção 8.

## 2. Ambiente

| | |
|---|---|
| Data | 2026-10-18, entre as 14:28 e as 16:06 (hora local) |
| Mac | MacBook Air (Mac17,3), macOS 26.5.1, Bluetooth Apple N1; Python 3.14.7 e bleak 3.0.2 no `.venv` |
| Telemóvel | Samsung SM-S938B, Android 16 (API 36); nRF Connect 4.29.1; MyCitroën 1.55.1 |
| Estado do carro | **não registado** (parado; painel não fornecido) |
| Ferramentas | `tools/ble_discover.py` (scan/watch/dump/listen); `tools/snooz_extract.py` (resumo HCI do `dumpsys`) |

Nota sobre o macOS: o Bluetooth não funciona a partir do shell do Claude Code, porque o processo responsável
(`claude`) não declara `NSBluetoothAlwaysUsageDescription` e o TCC termina o Python com SIGABRT. Funciona no
painel Terminal da app Claude.

## 3. Identificação (OBSERVADO)

| Campo | Valor | Origem |
|---|---|---|
| Nome anunciado | `R5118926` (Complete Local Name) | anúncios no Mac e no telemóvel |
| Endereço | `FA:24:AC:xx:xx:32`, **aleatório estático** (address type 1; os 2 bits de topo de 0xFA são `11`). O `dumpsys` mostra "(Public)", mas o pacote HCI diz o contrário. | HCI LE Advertising Report e LE Connection Complete |
| Identificador no macOS | `0F0FEB26-75AD-F08A-D32C-FAC437507AE4` (UUID local do CoreBluetooth) | bleak |
| Tipo | **só LE**: flags `0x06` = LE General Discoverable + **BR/EDR Not Supported**; não há Classic/SPP | anúncio |
| Controlador remoto | LL version 8 (**Bluetooth 4.2**), Company ID **0x0059 = Nordic Semiconductor**, subversão 129 | HCI Read Remote Version |
| LE features | `0x01`: só LE Encryption | HCI LE Read Remote Features |
| Emparelhamento | nenhum: não está emparelhado com o telemóvel nem com o Mac; nenhum evento HCI de encriptação | `dumpsys`, HCI |

## 4. Anúncio (OBSERVADO)

- O tipo é ADV_IND (ligável e scannable). A resposta de scan vem **vazia**: 146 respostas `0x1b` sem dados.
- O Mac recebeu cerca de **8,2 anúncios/s**. O RSSI ficou entre −60 e −77 dBm junto do carro.
- Há **dois conteúdos que alternam**, ambos com Service Data de UUID 16-bit `0x27D5`. Este UUID não é um
  serviço normalizado pela Bluetooth SIG.

| Conteúdo | AD completo (hex) | Duração típica de cada bloco |
|---|---|---|
| A (longo) | `02 01 06` `0b 16 d5 27 95 88 9b 1f 88 01 8f f2` `09 09 52 35 31 31 38 39 32 36` | mediana 0,89 s |
| B (curto) | `02 01 06` `05 16 d5 27 01 00` `09 09 52 35 31 31 38 39 32 36` | mediana 0,27 s |

- O conteúdo A foi **idêntico** às 14:43 (telemóvel) e às 15:57 (Mac).
- **Variantes passageiras**:
  - 14:43:52 (telemóvel): `ff ff ff ff ff ff ff f8` → `ff f8 9b 1f ff ff ff f8` → `95 88 9b 1f f8 01 8f f2` → A.
  - 15:57:31–34 (Mac): 19 anúncios como `01 a8 03 1f 88 01 8f f2`, `95 88 03 1f …` e `95 88 93 1f …`, e depois A.
  - HIPÓTESE: o buffer do anúncio é reescrito a meio de uma emissão. Não parecem dados novos.

## 5. GATT (OBSERVADO, `dump` às 15:59)

| Serviço | Característica | Handle | Propriedades | Descritores |
|---|---|---|---|---|
| `00002700-1212-efde-1523-785fef13d123` | `00002701-1212-efde-1523-785fef13d123` | 10 | **WRITE, INDICATE** | CCCD (implícito no INDICATE) |

- O macOS esconde os serviços 0x1800 (GAP) e 0x1801 (GATT). Não existe 0x180A (Device Information) nem 0x180F (Battery).
- As descrições "unitless" e "length (metre)" que o bleak mostra estão erradas: confundem os UUIDs 0x2700/0x2701 com unidades da SIG.
- A base `-1212-efde-1523-785fef13d123` é a base genérica dos exemplos da Nordic e muitos produtos sem
  relação a usam (pesquisa no GitHub). Não identifica o fabricante. Também não há características de
  serial-over-BLE típicas de ELM327 (FFE0/FFE1, FFF0, Nordic UART 6E400001…).

## 6. Leituras e indicações (OBSERVADO)

- **Leituras:** nenhuma, porque não existem características READ.
- **Indicações:** subscrição da 0x2701 às 16:04:25. Isto escreveu `0x0002` no CCCD do dongle e nada no
  barramento CAN. Em 120 s chegaram **0 indicações**.
- **Escritas na característica:** nenhuma. Nunca foi escrito nada na 0x2701.

## 7. A MyCitroën e o R5118926 (OBSERVADO, `dumpsys bluetooth_manager`)

- Hoje só o **nRF Connect** abriu ligações GATT ao R5118926, às 14:28–14:39 e às 14:43:55–15:00:53.
  A segunda caiu por *supervision timeout* (motivo 0x08).
- A **MyCitroën** registou um cliente GATT só para um **botão Flic** ("Flic BH25-…", chip Nordic, BT 5.1),
  com o qual se emparelhou e desemparelhou às 14:35–14:37. O utilizador confirmou que o botão serve para
  controlar a MyCitroën.
- Consequência: a utilização de hoje da MyCitroën **não revela** o protocolo do R5118926. Só valerá a pena
  um HCI snoop log se a MyCitroën se ligar ao R5118926 noutras condições, por exemplo com o carro em Ready.
  Nesse caso, o log mostraria os comandos que a app escreve na 0x2701 e se vão encriptados.
- O HCI snoop log está **desligado** no telemóvel. O resumo em memória do `dumpsys` tem só eventos HCI
  (sem ACL), por isso não mostra tráfego GATT.

## 8. Cruzamento com `docs/CAN_REFERENCIA.md` e alternativa

- Nada do que o R5118926 envia sem pedir corresponde aos sinais da referência. Os sinais de
  `CAN_REFERENCIA.md` continuam todos HIPÓTESE.
- Segundo `CAN_REFERENCIA.md`, os frames úteis são **de difusão periódica a 500 kbit/s** nos pinos 6/14
  (TOPO `main.cpp:39,531`; AMID `main.cpp:602`). Basta **escutar** o barramento, sem pedir nada.
- **Alternativa proposta**, segundo as regras: um adaptador CAN em **modo de escuta** na porta OBD.
  - **WiCAN**: é o que o EVCC usa para ler o CAN do Ami e interpretar no próprio módulo SoC, autonomia e
    estado (`mreschka/Citroen-AMI-evcc-Connector`, `README.md:6,10,72`). Antes de comprar, confirmar na
    documentação do WiCAN que tem um modo de escuta sem transmissão; o README do EVCC não o diz.
  - **ELM327 BLE** de boa qualidade (por exemplo, OBDLink CX): configura-se só o adaptador (`ATSP6` = CAN
    11 bit 500 kbit/s) e monitoriza-se com `ATMA`, sem pedidos PID/UDS.
  - Placa **ESP32 + transceiver CAN** em modo silencioso, como no TOPO e no AMID.
- **Porta OBD:** segundo o EVCC, o dongle Bluetooth da Citroën e o WiCAN funcionam em paralelo com um
  **cabo OBD duplo** (`README.md:38`). Falta confirmar fisicamente que o R5118926 está na porta OBD.

## 9. Limitações e o que falta para fechar a Fase 1

1. **Valores do painel e estado do carro** não registados. Sem eles nada pode passar a CONFIRMADO.
2. **Repetir o `watch`** com o carro em "Ready" (parado, travão puxado) e, se possível, a carregar. É a única
   forma passiva de ver se o Service Data `0x27D5` muda com o estado do carro.
3. **Identificar o produto:** etiqueta ou fotografia do dongle, origem (veio com o carro, concessionário,
   outro), app ou documentação associada. Se o fabricante publicar o protocolo, a decisão de o usar volta
   para o utilizador.
4. **Ver se a MyCitroën usa o dongle com o carro em Ready.** Se o `dumpsys` mostrar uma ligação da
   MyCitroën ao `FA:24:AC:xx:xx:32`, repetir com o HCI snoop log ativo (só leitura) para ver o protocolo.
5. A nota ELM327/Classic (Fase 1, passo 4) **não se aplica**: o dispositivo é só BLE e não tem serial-over-BLE.

## 10. Anexos (em `logs/`, fora do git)

| Ficheiro | Conteúdo |
|---|---|
| `fase0_20261018_dumpsys_bluetooth_manager.txt` | `dumpsys bluetooth_manager` do telemóvel (15:50) |
| `fase0_20261018_snooz_R5118926.jsonl` | anúncios e eventos de ligação do R5118926 extraídos do resumo HCI (`tools/snooz_extract.py`) |
| `ami_ble_20261018_155548.jsonl`, `…_155630.jsonl` | `scan` de 10 s no Mac; o segundo já inclui o Service Data |
| `ami_ble_20261018_155723.jsonl` | `watch R5118926 60`: 489 anúncios |
| `ami_ble_20261018_155926.jsonl` | `dump`: serviços e características |
| `ami_ble_20261018_160425.jsonl` | `listen` de 120 s: subscrição, 0 indicações |
