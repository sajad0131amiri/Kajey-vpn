import asyncio
import ssl
import struct
import websockets

UUID = bytes.fromhex("31116f307e2243a2a1d1a8a64fa0ebb7")  # خط‌تیره‌ها پاک شدن
SERVER = "www.google.com"
PORT = 443
PATH = "/sajadvpn"
HOST_HEADER = "xray-relay-227060539200.us-central1.run.app"
SNI = "google.com"
ALPN = ["h2", "http/1.1"]

def build_vless_header(target_addr: str, target_port: int) -> bytes:
    """VLESS TCP request header (encryption=none)."""
    header = b"\x00"
    header += UUID
    header += b"\x00"
    header += b"\x01"
    header += struct.pack(">H", target_port)
    header += b"\x02"
    addr_bytes = target_addr.encode()
    header += bytes([len(addr_bytes)]) + addr_bytes
    return header

async def vless_connect(target_addr: str, target_port: int):
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.set_alpn_protocols(ALPN)

    uri = f"wss://{SERVER}:{PORT}{PATH}"
    ws = await websockets.connect(
        uri,
        ssl=ssl_ctx,
        server_hostname=SNI,
        extra_headers={"Host": HOST_HEADER},
    )

    header = build_vless_header(target_addr, target_port)
    await ws.send(header)
    return ws
