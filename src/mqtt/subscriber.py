"""
Module 1 Assignment — Task 1.2
MQTT Wildcard Subscriber
"""

import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

BROKER_HOST = "localhost"
BROKER_PORT = 1883
CLIENT_ID = "smartfactory-subscriber-001"

TOPIC_ALL = "factory/#"
TOPIC_TEMP = "factory/+/temperature"

CRITICAL_TEMP = 85.0
SUMMARY_INTERVAL = 30


class SmartFactorySubscriber:
    """Subscribes to SmartFactory sensor topics and processes incoming data."""

    def __init__(self, broker_host: str = BROKER_HOST, broker_port: int = BROKER_PORT):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self._client = mqtt.Client(client_id=CLIENT_ID, clean_session=False)
        self._msg_counts: dict[str, int] = defaultdict(int)
        self._last_summary = time.time()
        self._alerts_fired = 0

        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message

    def on_connect(self, client, userdata, flags: dict, rc: int) -> None:
        if rc == 0:
            log.info("Connected to broker")
            client.subscribe(TOPIC_ALL, qos=1)
            client.subscribe(TOPIC_TEMP, qos=2)
            log.info(f"Subscribed to {TOPIC_ALL} and {TOPIC_TEMP}")
        else:
            log.error(f"Connection failed: {rc}")

    def on_message(self, client, userdata, msg: mqtt.MQTTMessage) -> None:
        self._msg_counts[msg.topic] += 1

        raw_payload = msg.payload.decode(errors="replace")

        try:
            payload: Any = json.loads(raw_payload)
        except json.JSONDecodeError:
            payload = raw_payload

        self._print_message(msg, payload)

        if msg.topic.endswith("/temperature"):
            self._check_temperature_alert(msg.topic, payload)

        now = time.time()
        if now - self._last_summary >= SUMMARY_INTERVAL:
            self._print_summary()
            self._last_summary = now

    def _print_message(self, msg: mqtt.MQTTMessage, payload: Any) -> None:
        now = datetime.now(timezone.utc).strftime("%H:%M:%S")

        if isinstance(payload, dict) and "value" in payload:
            unit = payload.get("unit", "")
            value_text = f"{payload['value']} {unit}".strip()
        else:
            value_text = str(payload)

        print(
            f"[{now}] {msg.topic}  "
            f"val={value_text}  QoS={msg.qos}  retain={msg.retain}"
        )

    def _check_temperature_alert(self, topic: str, payload: Any) -> None:
        if not isinstance(payload, dict):
            return

        value = payload.get("value")

        if value is None:
            return

        try:
            temp_value = float(value)
        except (TypeError, ValueError):
            return

        if temp_value > CRITICAL_TEMP:
            self._alerts_fired += 1
            timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()

            print("╔══════════════════════════════════════╗")
            print(f"║  ⚠ CRITICAL ALERT — {topic}")
            print(f"║  Temperature: {temp_value}°C  (threshold: {CRITICAL_TEMP}°C)")
            print(f"║  Time: {timestamp}")
            print("╚══════════════════════════════════════╝")

    def _print_summary(self) -> None:
        print("── Message Summary ──────────────────────")

        for topic, count in sorted(self._msg_counts.items()):
            print(f"{topic:<50}  {count:>6} msgs")

        total = sum(self._msg_counts.values())
        print(f"Total: {total} messages  |  Alerts fired: {self._alerts_fired}")
        print("─────────────────────────────────────────")

    def run(self) -> None:
        self._client.connect(self.broker_host, self.broker_port, keepalive=60)
        log.info("Listening for messages (Ctrl-C to stop)")

        try:
            self._client.loop_forever()
        except KeyboardInterrupt:
            log.info("Subscriber stopped")
        finally:
            self._client.disconnect()


if __name__ == "__main__":
    sub = SmartFactorySubscriber()
    sub.run()