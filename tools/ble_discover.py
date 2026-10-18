#!/usr/bin/env python3
"""AMI CONNECT - Fase 1: descoberta BLE PASSIVA do dispositivo OBD.

Só faz: scan, enumeração GATT, leitura de características 'read' e subscrição
de características 'notify'/'indicate'. NUNCA escreve em nenhuma característica.
Tudo é gravado em JSONL com timestamps.

Uso (macOS: o bleak instala-se com pip num ambiente virtual, não com brew):
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r tools/requirements.txt
  python3 ble_discover.py scan                      # lista dispositivos BLE
  python3 ble_discover.py dump  <MAC|UUID>          # serviços/características + leituras
  python3 ble_discover.py listen <MAC|UUID> [segundos]  # subscreve notify e grava
"""
import asyncio, json, sys, time
from pathlib import Path
from bleak import BleakClient, BleakScanner

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"  # ignorado pelo git (pode conter o VIN)
LOG_DIR.mkdir(exist_ok=True)
LOG = LOG_DIR / f"ami_ble_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"

def log(event, **kw):
    rec = {"ts": time.time(), "iso": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **kw}
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec))

async def scan():
    found = await BleakScanner.discover(timeout=10.0, return_adv=True)
    for addr, (dev, adv) in found.items():
        log("device", address=addr, name=dev.name or adv.local_name, rssi=adv.rssi,
            service_uuids=adv.service_uuids,
            manufacturer_data={str(k): v.hex() for k, v in adv.manufacturer_data.items()})

async def dump(addr):
    async with BleakClient(addr) as c:
        for s in c.services:
            log("service", uuid=s.uuid, description=s.description)
            for ch in s.characteristics:
                log("characteristic", service=s.uuid, uuid=ch.uuid, handle=ch.handle,
                    properties=ch.properties, description=ch.description)
                if "read" in ch.properties:
                    try:
                        v = await c.read_gatt_char(ch)
                        log("read", uuid=ch.uuid, hex=v.hex(), ascii=v.decode("ascii", "replace"))
                    except Exception as e:
                        log("read_error", uuid=ch.uuid, error=str(e))

async def listen(addr, secs):
    async with BleakClient(addr) as c:
        subs = []
        for s in c.services:
            for ch in s.characteristics:
                if {"notify", "indicate"} & set(ch.properties):
                    def cb(sender, data, u=ch.uuid):
                        log("notify", uuid=u, hex=data.hex(), len=len(data))
                    try:
                        await c.start_notify(ch, cb); subs.append(ch)
                        log("subscribed", uuid=ch.uuid)
                    except Exception as e:
                        log("subscribe_error", uuid=ch.uuid, error=str(e))
        await asyncio.sleep(secs)
        for ch in subs:
            await c.stop_notify(ch)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan": asyncio.run(scan())
    elif cmd == "dump": asyncio.run(dump(sys.argv[2]))
    elif cmd == "listen": asyncio.run(listen(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 120))
    print(f"log: {LOG}")
