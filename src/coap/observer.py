"""
Module 1 Assignment — Task 2.2
CoAP Observer Client
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import aiocoap
from aiocoap import Message

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
log = logging.getLogger(__name__)

SERVER_BASE = "coap://localhost"
OBSERVE_DURATION = 60


class FactoryObserver:
    """Observes CoAP sensor resources and reassembles Block2 transfers."""

    def __init__(self):
        self._ctx = None
        self._last_seq: dict[str, int] = {}
        self._stale_count: dict[str, int] = {}

    async def start(self) -> None:
        self._ctx = await aiocoap.Context.create_client_context()

    async def stop(self) -> None:
        if self._ctx:
            await self._ctx.shutdown()

    async def observe_resource(self, uri: str) -> None:
        request = Message(code=aiocoap.GET, uri=uri)
        request.opt.observe = 0

        pr = self._ctx.request(request)

        try:
            response = await pr.response
            self._handle_notification(uri, response)

            async def notification_loop():
                async for response in pr.observation:
                    self._handle_notification(uri, response)

            task = asyncio.create_task(notification_loop())

            try:
                await asyncio.sleep(OBSERVE_DURATION)
            finally:
                pr.observation.cancel()
                task.cancel()
                log.info(f"Deregistered from {uri}")

        except Exception as e:
            log.error(f"Observation failed for {uri}: {e}")

    def _is_stale(self, seq: int, last: int) -> bool:
        return seq <= last

    def _handle_notification(self, uri: str, response: Message) -> None:
        seq = response.opt.observe

        if seq is None:
            seq = 0

        last = self._last_seq.get(uri)

        if last is not None and self._is_stale(seq, last):
            self._stale_count[uri] = self._stale_count.get(uri, 0) + 1
            log.warning(f"STALE notification on {uri}: seq={seq} <= last={last}")
            return

        self._last_seq[uri] = seq

        try:
            payload = json.loads(response.payload.decode())
        except Exception:
            log.error(f"Could not parse payload from {uri}")
            return

        value = payload.get("value")
        unit = payload.get("unit", "")
        timestamp = payload.get("ts") or datetime.now(timezone.utc).isoformat()

        log.info(f"[OBSERVE] {uri}  seq={seq}  val={value} {unit}  @ {timestamp}")

    async def fetch_manifest(self) -> None:
        uri = f"{SERVER_BASE}/factory/manifest"
        request = Message(code=aiocoap.GET, uri=uri)

        response = await self._ctx.request(request).response
        payload = response.payload

        log.info(f"Manifest received: {len(payload)} bytes")

        data = json.loads(payload.decode())
        entries = data.get("entries", [])
        log.info(f"Firmware entries in manifest: {len(entries)}")
        log.info("Block2 transfer complete")

    async def run(self) -> None:
        await self.start()

        try:
            uris = [
                f"{SERVER_BASE}/factory/line1/temperature",
                f"{SERVER_BASE}/factory/line2/temperature",
            ]

            await asyncio.gather(
                *(self.observe_resource(uri) for uri in uris)
            )

            await self.fetch_manifest()

            print("── Stale Notification Summary ─────────")
            for uri in uris:
                print(f"{uri}: {self._stale_count.get(uri, 0)} stale notifications")
            print("───────────────────────────────────────")

        finally:
            await self.stop()


if __name__ == "__main__":
    observer = FactoryObserver()
    asyncio.run(observer.run())