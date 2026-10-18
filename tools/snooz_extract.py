#!/usr/bin/env python3
"""AMI CONNECT - extrai de um `adb shell dumpsys bluetooth_manager` (ficheiro local) o resumo HCI em
memória (BTSNOOP_LOG_SUMMARY, formato btsnooz do AOSP) e grava em JSONL os anúncios e os eventos de
ligação de um dispositivo, procurado pelo nome anunciado.

Só lê o ficheiro: não fala com o telemóvel nem com o dongle. O resumo tem só comandos e eventos HCI
(sem ACL), por isso não mostra tráfego GATT.

Uso:
  python3 tools/snooz_extract.py logs/<dumpsys>.txt R5118926 [logs/<saida>.jsonl]
"""
import base64, datetime as dt, json, struct, sys, zlib


def snooz_records(path):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    start = next(i for i, l in enumerate(lines) if "BEGIN:BTSNOOP_LOG_SUMMARY" in l)
    end = next(i for i, l in enumerate(lines) if "END:BTSNOOP_LOG_SUMMARY" in l)
    blob = base64.b64decode("".join(l.strip() for l in lines[start + 1:end]))
    version, last_us = blob[0], struct.unpack_from("<q", blob, 1)[0]
    data, recs, off = zlib.decompress(blob[9:]), [], 0
    while off < len(data):
        if version == 1:
            length, delta = struct.unpack_from("<HI", data, off); off += 6
        else:
            length, _plen, delta = struct.unpack_from("<HHI", data, off); off += 8
        recs.append([delta, data[off], data[off + 1: off + length]]); off += length
    # deltas em µs, acumulados para trás a partir do último registo; o Android guarda a hora local
    t = last_us
    for r in reversed(recs):
        r.append(t); t -= r[0]
    wall = lambda us: dt.datetime.fromtimestamp(us / 1e6, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    return [(wall(us), typ, pkt) for _d, typ, pkt, us in recs]


def adv_reports(p):
    """Devolve (evt_type, addr_type, addr, rssi, ad) dos LE Advertising Reports (legado 0x02 e estendido 0x0d)."""
    out, n, off = [], p[3], 4
    for _ in range(n):
        if p[2] == 0x0d:
            if off + 24 > len(p): break
            et, at, addr = struct.unpack_from("<H", p, off)[0], p[off + 2], p[off + 3:off + 9]
            rssi, dlen = struct.unpack_from("<b", p, off + 13)[0], p[off + 23]
            ad = p[off + 24:off + 24 + dlen]; off += 24 + dlen
        else:
            if off + 9 > len(p): break
            et, at, addr, dlen = p[off], p[off + 1], p[off + 2:off + 8], p[off + 8]
            ad = p[off + 9:off + 9 + dlen]
            rssi = struct.unpack_from("<b", p, off + 9 + dlen)[0] if off + 9 + dlen < len(p) else None
            off += 10 + dlen
        out.append((et, at, addr, rssi, ad))
    return out


def main(src, name, dst):
    recs = snooz_records(src)
    needle, mac, handles, n_adv = name.encode(), None, set(), 0
    with open(dst, "w") as f:
        def log(t, event, **kw):
            f.write(json.dumps({"t_local": t, "event": event, **kw}) + "\n")
        for t, typ, p in recs:
            if typ != 0x10 or len(p) < 3:  # só eventos HCI recebidos
                continue
            ev, sub = p[0], (p[2] if p[0] == 0x3e else None)
            h = lambda o: struct.unpack_from("<H", p, o)[0] & 0x0FFF
            u16 = lambda o: struct.unpack_from("<H", p, o)[0]
            if sub in (0x02, 0x0d):
                for et, at, addr, rssi, ad in adv_reports(p):
                    if mac is None and needle in ad:
                        mac = addr
                    if addr == mac:
                        n_adv += 1
                        log(t, "adv", report=hex(sub), evt_type=hex(et), addr=addr[::-1].hex(":"), addr_type=at,
                            rssi=rssi, ad_hex=ad.hex())
            elif sub in (0x01, 0x0a, 0x29) and mac and p[8:14] == mac:
                handles.add(h(4))
                o = 14 if sub == 0x01 else 26
                log(t, "le_conn_complete", status=p[3], handle=h(4), role=p[6], peer_addr_type=p[7],
                    peer=mac[::-1].hex(":"), interval_ms=u16(o) * 1.25, latency=u16(o + 2), timeout_ms=u16(o + 4) * 10)
            elif sub == 0x03 and h(4) in handles:
                log(t, "le_conn_update", status=p[3], handle=h(4), interval_ms=u16(6) * 1.25, latency=u16(8),
                    timeout_ms=u16(10) * 10)
            elif sub == 0x04 and h(4) in handles:
                log(t, "le_remote_features", status=p[3], handle=h(4), features=p[6:14].hex())
            elif sub == 0x07 and h(3) in handles:
                log(t, "le_data_length", handle=h(3), max_tx=u16(5), max_rx=u16(9))
            elif ev == 0x0c and h(3) in handles:
                log(t, "remote_version", status=p[2], handle=h(3), ll_version=p[5], company_id=hex(u16(6)),
                    subversion=u16(8))
            elif ev in (0x08, 0x59, 0x30) and h(3) in handles:
                log(t, "encryption", hci_event=hex(ev), status=p[2], handle=h(3), raw=p.hex())
            elif ev == 0x05 and h(3) in handles:
                log(t, "disconnection", status=p[2], handle=h(3), reason=hex(p[5]))
                handles.discard(h(3))
    print(f"registos HCI: {len(recs)} ({recs[0][0]} → {recs[-1][0]}, hora local)")
    print(f"{name}: endereço={mac[::-1].hex(':') if mac else None}, anúncios={n_adv}")
    print(f"gravado: {dst}")


if __name__ == "__main__":
    src, name = sys.argv[1], sys.argv[2]
    main(src, name, sys.argv[3] if len(sys.argv) > 3 else src.rsplit(".", 1)[0] + f"_{name}.jsonl")
