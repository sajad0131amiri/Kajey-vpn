import asyncio
from urllib.parse import urlparse
from vless_transport import vless_connect

async def handle_http(reader, writer):
    try:
        request_line = await reader.readline()
        if not request_line:
            writer.close()
            return
        parts = request_line.decode().split()
        if len(parts) < 3:
            writer.close()
            return
        method, url, version = parts

        if method == "CONNECT":
            # درخواست HTTPS (تونل)
            host, port = url.split(":")
            port = int(port)
            try:
                ws = await vless_connect(host, port)
            except:
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                writer.close()
                return
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await writer.drain()

            async def client_to_server():
                while True:
                    data = await reader.read(8192)
                    if not data:
                        break
                    await ws.send(data)

            async def server_to_client():
                try:
                    async for msg in ws:
                        writer.write(msg)
                        await writer.drain()
                except:
                    pass
                finally:
                    writer.close()

            await asyncio.gather(client_to_server(), server_to_client())
        else:
            # درخواست HTTP معمولی
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or 80
            path = parsed.path + ("?" + parsed.query if parsed.query else "")
            try:
                ws = await vless_connect(host, port)
            except:
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                writer.close()
                return

            req = f"{method} {path} {version}\r\n"
            while True:
                line = await reader.readline()
                if line == b"\r\n":
                    break
                if line.lower().startswith(b"proxy-") or line.lower().startswith(b"connection:"):
                    continue
                req += line.decode()
            req += "Connection: close\r\n\r\n"
            await ws.send(req.encode())

            try:
                async for msg in ws:
                    writer.write(msg)
                    await writer.drain()
            except:
                pass
            finally:
                writer.close()
    except Exception as e:
        print("Error:", e)
    finally:
        try:
            writer.close()
        except:
            pass

async def main():
    server = await asyncio.start_server(handle_http, "0.0.0.0", 1080)
    print("HTTP Proxy on port 1080")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
