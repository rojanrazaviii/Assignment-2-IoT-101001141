"""
Module 1 Assignment — Task 2.1
CoAP Sensor Resource Server
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timezone

import aiocoap
import aiocoap.resource as resource
from aiocoap import Code, Message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s"
)
log = logging.getLogger(__name__)

SENSOR_CONFIG = {
    "temperature": {"unit": "C", "base": 70.0, "noise": 3.0},
    "vibration": {"unit": "mm/s", "base": 1.2, "noise": 0.3},
    "power": {"unit": "kW", "base": 45.0, "noise": 5.0},
}


def _sim(sensor: str) -> dict:
    cfg = SENSOR_CONFIG[sensor]
    return {
        "value": round(cfg["base"] + random.gauss(0, cfg["noise"]), 3),
        "unit": cfg["unit"],
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def _json(data: dict) -> bytes:
    return json.dumps(data).encode()


class SensorResource(resource.ObservableResource):
    def __init__(self, line: str, sensor_type: str):
        super().__init__()
        self.line = line
        self.sensor_type = sensor_type
        self._reading = _sim(sensor_type)
        asyncio.ensure_future(self._update_loop())

    async def _update_loop(self) -> None:
        while True:
            await asyncio.sleep(5)
            self._reading = _sim(self.sensor_type)
            self.updated_state()

    async def render_get(self, request: Message) -> Message:
        payload = _json({
            "line": self.line,
            "sensor": self.sensor_type,
            **self._reading,
        })
        return Message(code=Code.CONTENT, payload=payload, content_format=50)


class ActuatorResource(resource.Resource):
    def __init__(self):
        super().__init__()
        self._state = "OFF"

    async def render_get(self, request: Message) -> Message:
        return Message(
            code=Code.CONTENT,
            payload=_json({"state": self._state}),
            content_format=50,
        )

    async def render_put(self, request: Message) -> Message:
        try:
            data = json.loads(request.payload.decode())
            state = data.get("state")
        except Exception:
            return Message(
                code=Code.BAD_REQUEST,
                payload=b'{"error":"invalid payload"}',
                content_format=50,
            )

        if state not in ["ON", "OFF"]:
            return Message(
                code=Code.BAD_REQUEST,
                payload=b'{"error":"state must be ON or OFF"}',
                content_format=50,
            )

        self._state = state
        return Message(
            code=Code.CHANGED,
            payload=_json({"state": self._state}),
            content_format=50,
        )


class ManifestResource(resource.Resource):
    async def render_get(self, request: Message) -> Message:
        entries = []

        for i in range(60):
            entries.append({
                "device_id": f"sensor-{i}",
                "firmware_version": f"v2.{i}",
                "checksum": f"abc123{i}",
                "update_url": f"https://updates.local/sensor-{i}.bin",
                "sensor_type": ["temperature", "vibration", "power"][i % 3],
                "required": bool(i % 2),
            })

        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entries": entries,
        }

        payload = json.dumps(manifest).encode()

        if len(payload) < 3072:
            manifest["padding"] = "X" * (3072 - len(payload))
            payload = json.dumps(manifest).encode()

        return Message(code=Code.CONTENT, payload=payload, content_format=50)


async def build_server() -> aiocoap.Context:
    root = resource.Site()

    root.add_resource(["factory", "line1", "temperature"], SensorResource("line1", "temperature"))
    root.add_resource(["factory", "line1", "vibration"], SensorResource("line1", "vibration"))
    root.add_resource(["factory", "line1", "power"], SensorResource("line1", "power"))
    root.add_resource(["factory", "line2", "temperature"], SensorResource("line2", "temperature"))
    root.add_resource(["actuator", "line1", "fan"], ActuatorResource())
    root.add_resource(["factory", "manifest"], ManifestResource())

    root.add_resource(
        [".well-known", "core"],
        resource.WKCResource(root.get_resources_as_linkheader),
    )

    context = await aiocoap.Context.create_server_context(
        root,
        bind=("localhost", 5683),
    )

    return context


async def main() -> None:
    await build_server()
    log.info("CoAP server running on coap://localhost:5683")
    await asyncio.get_event_loop().create_future()


if __name__ == "__main__":
    asyncio.run(main())