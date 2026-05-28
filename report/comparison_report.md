# Module 1 Assignment — Protocol Comparison Report

**Student Name:** Seyedeh Rojan Razavi
**Student ID:**   101001141
**Date:**        2026/05/28
---

## 5.1 QoS Comparison Results Table

> Run `pytest tests/mqtt/test_qos_loss.py -v -s` and paste the output table here.

| Protocol / QoS | Sent | Received | Lost (%) | Duplicates | Avg Latency (ms) |
|----------------|------|----------|----------|------------|-----------------|
| MQTT QoS 0 |100|100|0.0%|0|1.9|
| MQTT QoS 1 |100 |100 | 0.0%| 0| 2.1|
| MQTT QoS 2 | 100|100 |0.0% | 0| 5.0|
| CoAP NON |N/A |N/A | N/A|N/A | N/A|
| CoAP CON |N/A | N/A|N/A | N/A|N/A |
| AMQP (confirms off) | N/A| N/A|N/A |N/A |N/A |

**Analysis Questions:**

1. **Why does QoS 0 lose messages while QoS 1 and 2 do not?** *(2–3 sentences)*

   > QoS 0 uses a fire-and-forget delivery model and does not require acknowledgements from the broker. If a packet is lost during transmission, it is not retransmitted. In contrast, QoS 1 and QoS 2 use acknowledgement mechanisms that ensure messages are retransmitted if delivery is not confirmed.

2. **QoS 1 may show duplicates. Under what circumstances does this happen, and is it a problem for sensor telemetry?** *(2–3 sentences)*

   > Duplicates can occur when the sender retransmits a PUBLISH message because the PUBACK was lost or delayed. For sensor telemetry, occasional duplicates are usually acceptable because newer sensor readings quickly replace older ones and applications can filter duplicate sequence numbers if necessary.

3. **QoS 2 has higher latency than QoS 1. What causes this, and when is the trade-off worth it?** *(2–3 sentences)*

   > QoS 2 requires a four-step handshake (PUBLISH, PUBREC, PUBREL, PUBCOMP) to guarantee exactly-once delivery. The additional protocol exchanges increase latency compared to QoS 1. This trade-off is worthwhile for critical operations where duplicate processing could cause serious problems, such as financial transactions or safety-critical actuator commands.

---

## 5.2 CoAP–HTTP Proxy Mapping

It is not available in the provided starter kit.

> Run `pytest tests/coap/test_proxy.py -v -s` and record the observed HTTP headers.

| HTTP Header | CoAP Option | Your Observed Value |
|-------------|-------------|---------------------|
| Content-Type | | |
| Cache-Control: max-age | | |
| ETag | | |
| Location | | |

---

## 5.3 Protocol Selection Recommendation

*(500–700 words. Justify each recommendation with specific technical evidence from your implementation and packet captures.)*

### Data Path Recommendations

| Data Path | Recommended Protocol | Justification |
|-----------|---------------------|---------------|
| Sensor → Cloud (high frequency, <100 ms latency) |MQTT | MQTT provides low latency, lightweight messaging, and efficient publish-subscribe communication. The QoS experiment showed low latency (1.9–5.0 ms) and reliable delivery.|
| Actuator commands (safety-critical, exactly-once) |MQTT QoS 2 | QoS 2 guarantees exactly-once delivery through a four-step handshake, reducing the risk of duplicate or lost actuator commands.|
| Backend service-to-service routing |AMQP | AMQP provides advanced routing, acknowledgements, dead-letter queues, and message persistence, making it suitable for enterprise backend communication.|
| OTA firmware delivery to constrained MCU (Class 2) |CoAP | CoAP is specifically designed for constrained devices and supports block-wise transfer, reducing memory and bandwidth requirements during firmware delivery.|

### Detailed Justification

> MQTT and CoAP were evaluated through implementation, testing, and packet analysis. Both protocols demonstrated different strengths and are suitable for different IoT communication scenarios.

For high-frequency sensor-to-cloud communication, MQTT is the most suitable protocol. MQTT uses a lightweight publish-subscribe architecture with low protocol overhead, making it efficient for transmitting frequent telemetry data. During the QoS experiment, MQTT achieved average latencies of approximately 1.9 ms for QoS 0, 2.1 ms for QoS 1, and 5.0 ms for QoS 2 while maintaining reliable message delivery. The packet capture also showed compact packet structures and efficient message exchange. These characteristics make MQTT an excellent choice for real-time monitoring applications where low latency and efficient bandwidth usage are important.

For safety-critical actuator commands, MQTT with QoS 2 is recommended. QoS 2 provides exactly-once delivery through additional acknowledgement exchanges. Although this increases latency compared to QoS 0 and QoS 1, it minimizes the possibility of duplicate processing or message loss. In industrial environments, incorrect actuator behaviour may lead to operational or safety issues, making delivery guarantees more important than raw speed.

For over-the-air (OTA) firmware delivery to constrained microcontrollers, CoAP is the preferred protocol. CoAP was specifically designed for constrained devices and low-power networks. During implementation, CoAP resources, observation mechanisms, and block-wise transfer functionality were used to support communication with resource-constrained devices. Packet analysis showed that CoAP uses a compact binary format with significantly lower overhead than traditional web protocols. Block-wise transfer allows large firmware files to be transmitted in smaller chunks, making firmware delivery practical even on devices with limited memory and processing power.

The packet captures also highlighted important differences between MQTT and CoAP. MQTT relies on a broker-based publish-subscribe model, while CoAP follows a lightweight request-response architecture similar to HTTP. MQTT is therefore more suitable for continuous telemetry streaming, whereas CoAP is well suited for direct device interaction, resource access, and firmware distribution.

Overall, MQTT is recommended for telemetry collection and cloud connectivity because of its low latency, reliability options, and efficient publish-subscribe model. CoAP is recommended for constrained IoT devices, direct resource access, and firmware delivery because of its small packet size and support for block-wise transfer. The implementation experience and packet analysis demonstrated that protocol selection should be based on application requirements, reliability needs, network constraints, and device capabilities.


---

## 5.4 Reflection

*(300–400 words addressing all three prompts below.)*

### Technical Challenge

> One of the biggest technical challenges I encountered during this assignment was capturing and analyzing CoAP traffic correctly. Unlike MQTT, CoAP packets were more difficult to identify and interpret in Wireshark. Several times, my packet captures did not contain the expected GET requests or Observe notifications, which required me to repeat the capture process and carefully verify the traffic. I eventually resolved the issue by restarting the CoAP server and observer, recapturing the traffic, and using Wireshark filters to locate the required packets. This process helped me better understand how CoAP messages, acknowledgements, tokens, and observation sequences work.

### Most Surprising Protocol Difference

> The most surprising difference I observed was how differently MQTT and CoAP handle communication. MQTT uses a broker-based publish-subscribe model where devices communicate through topics, while CoAP uses a lightweight request-response model similar to HTTP. I found the CoAP Observe feature particularly interesting because it allows clients to receive updates automatically after a single request. This made CoAP feel like a combination of traditional request-response communication and event-based messaging.

### Most Complex Protocol to Implement

> The most complex protocol to implement and analyze was CoAP. MQTT was relatively straightforward because publishing and subscribing to topics could be implemented easily and the packet structure was simpler to understand. In contrast, CoAP required understanding additional concepts such as Confirmable (CON) messages, Acknowledgements (ACK), Message IDs, Tokens, Observe notifications, and block-wise transfers. Troubleshooting CoAP traffic in Wireshark was also more challenging because identifying the correct packets and matching requests with responses required careful analysis. Although CoAP was more difficult, working with it provided a much deeper understanding of lightweight IoT communication protocols and constrained-device networking.

*Module 1 Assignment — Real-Time Data Analytics for IoT*
