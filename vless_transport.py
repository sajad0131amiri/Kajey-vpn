import asyncio
import ssl
import struct
import websockets

UUID = bytes.fromhex("31116f30-7e22-43a2-a1d1-a8a64fa0ebb7")
SERVER = "www.google.com"
PORT = 443
PATH = "/sajadvpn"
HOST_HEADER = "xray-relay-227060539200.us-central1.run.app"
SNI = "google.com"
ALPN = ["h2", "http/1.1"]   # از alpn=h2,http/1.1

def build_vless_header(target_addr: str, target_port: int) -> bytes:
    """VLESS TCP request header (encryption=none)."""
    # version (0)
    header = b"\x00"
    # uuid (16 bytes)
    header += UUID
    # addons (0x00 = no mux, no flow)
    header += b"\x00"
    # command: 0x01 = TCP
    header += b"\x01"
    # port (2 bytes big-endian)
    header += struct.pack(">H", target_port)
    # address type: 0x02 = domain
    header += b"\x02"
    addr_bytes = target_addr.encode()
    header += bytes([len(addr_bytes)]) + addr_bytes
    return header

async def vless_connect(target_addr: str, target_port: int):
    """
    Returns a websocket connection ready for bidirectional data transfer.
    """
    ssl_ctx = ssl.create_default_context()
    # SNI = google.com
    ssl_ctx.check_hostname = False
    ssl_ctx.set_alpn_protocols(ALPN)

    uri = f"wss://{SERVER}:{PORT}{PATH}"
    ws = await websockets.connect(
        uri,
        ssl=ssl_ctx,
        server_hostname=SNI,                # SNI
        extra_headers={"Host": HOST_HEADER},
    )

    header = build_vless_header(target_addr, target_port)
    await ws.send(header)
    return ws
