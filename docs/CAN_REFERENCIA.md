# AMI CONNECT — Referência CAN (extraída dos repositórios)

Estado de **todas** as linhas: **HIPÓTESE** (documentado por terceiros, ainda não visto no nosso carro nem validado com o painel).

Abreviaturas de origem:
- **TOPO** = `servicemensch/TopolinoInfoDisplay` → `src/main.cpp`
- **AMID** = `flrahe/AMI-Display` → `src/main.cpp`, `CAN_information/Ami_Rocks-e.dbc`
- **EVCC** = `mreschka/Citroen-AMI-evcc-Connector` → `README.md` (tabela WiCAN, linhas 80-86)
- **OBD** = `stwoowts/Citroen-Ami-Opel-Rocks-e-OBD` → `Ami_Rocks-e.dbc`, `Ami,Rocks-e Canbus.xlsx`

## Barramento
- 500 kbit/s, IDs de 11 bits: TOPO `main.cpp:39,531` (`CAN_500Kbs`), AMID `main.cpp:602` (`convertSpeed(500)`).
- Pinos OBD: o xlsx (OBD, folha "CAN ID") lista dois barramentos, "6;14" (CAN normal do OBD) e "10;11". Todos os sinais úteis abaixo estão em **6;14**.
- Todos os frames são de difusão periódica → leitura 100 % passiva, sem pedidos.

## Sinais (bytes `d[0..7]`, little-endian salvo indicação)

| ID | Sinal | Fórmula | Origem | Notas / divergências |
|---|---|---|---|---|
| 0x580 | Corrente bateria 48 V | `int16(d1<<8\|d0) / 10` A (+ = carga) | TOPO 645-656, AMID 806, OBD dbc (0.1, offset −6553.5) | O DBC usa unsigned+offset; o código usa int16 com sinal. Equivalente só aproximadamente — validar. |
| 0x580 | Tensão bateria 48 V | `(d3<<8\|d2) / 100` V | TOPO 658-663, AMID 808, OBD dbc | TOPO só aceita 42,00–65,00 V. |
| 0x580 | SoC % | `d5` | TOPO 666, AMID 878, OBD dbc (bit 40), EVCC (1408, bit 40) | Concordam todos. |
| 0x580 | Potência | `V × I` (derivado) | AMID 813-816 | Não é sinal CAN; cálculo. |
| 0x581 | Odómetro | `(d6<<16\|d5<<8\|d4) / 10` km | AMID 890, OBD dbc (scale 0.1) | **TOPO 574 não divide por 10**; EVCC diz que o odómetro precisa de byte-swap (README 20, 74). Validar com o painel. |
| 0x581 | Velocidade | `d7` km/h | TOPO 582, AMID 893, OBD dbc | Concordam. |
| 0x582 | Tempo restante de carga | `d1<<8\|d0` (segundos) | TOPO 594-596 (`/60` → min, >600 min = não carrega), AMID 902, EVCC (1410, "charge_time_sec") | DBC sem unidade. Xlsx: "Zeit bis 100% geladen". |
| 0x591 | Potência OBC % | — | OBD xlsx ("OBC Leistung %") | Sem fórmula documentada. |
| 0x593 | Bateria 12 V | `(d1<<8\|d0) / 100` V | TOPO 603-608 | **OBD dbc tem scale 1** — divergência. |
| 0x594 | Temp. bateria 1 / 2 | `int8(d0)`, `int8(d3)` °C | TOPO 613-640, AMID 908 | OBD dbc usa 16 bits — divergência. |
| 0x713 | Mudança | `((d1&1)<<1)\|(d0>>7)`: 0=R 1=N 2=D 3=—/X | TOPO 681-701, AMID 63,794 | Concordam. |
| 0x713 | Autonomia (km) | `d0 & 0x7F` (AMID 797) **ou** `d0 & 0x3F` (TOPO 705) | AMID, TOPO, EVCC (1811, bit 1, 7 bits) | Três versões diferentes. AMID: o carro envia 0 durante carga/desligar. |
| 0x713 | Ready | `d2 & 0x07 == 0b101` (TOPO 712-722) / `d2 & 4` (AMID 799) | TOPO, AMID, EVCC (1811, bit 21) | |
| 0x713 | Travão de mão | `d3 & 0x20` | AMID 801 | TOPO usa 0x714 `d0==1` (728-741). |
| 0x710–0x712 | VIN | ASCII | OBD xlsx | |
| — | Estado de carga | Heurística: I>0, travão de mão, velocidade 0, durante 20 frames | AMID 914-935 | **Não existe sinal CAN direto documentado.** |

## Nota sobre o OBD repo
`UDS_Scans/` contém sessões de diagnóstico, *security access* e *Clear DTC*. **Não serão usados** (regras: só leitura passiva).
