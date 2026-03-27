import argparse
import json
import time

import paho.mqtt.client as mqtt


def now_ms() -> int:
    return int(time.time() * 1000)


class Stats:
    def __init__(self) -> None:
        self.received = 0
        self.duplicates = 0
        self.gaps = 0
        self.last_seq = 0
        self.seen = set()

    def record(self, seq: int) -> None:
        self.received += 1
        if seq in self.seen:
            self.duplicates += 1
        else:
            self.seen.add(seq)
        if self.last_seq and seq > self.last_seq + 1:
            self.gaps += (seq - self.last_seq - 1)
        if seq > self.last_seq:
            self.last_seq = seq

    def summary(self) -> str:
        return f"received={self.received} duplicates={self.duplicates} gaps={self.gaps}"


def main() -> None:
    p = argparse.ArgumentParser(description="MQTT QoS subscriber (v3.1.1)")
    p.add_argument("--host", default="mosquitto")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--topic", default="qos/sim")
    p.add_argument("--qos", type=int, choices=[0, 1, 2], default=1)
    p.add_argument("--client-id", required=True)
    p.add_argument("--clean-session", action="store_true")
    args = p.parse_args()

    stats = Stats()
    client = mqtt.Client(client_id=args.client_id, clean_session=args.clean_session, protocol=mqtt.MQTTv311)

    def on_connect(c, userdata, flags, rc):
        print(f"[subscriber] connected rc={rc} flags={flags} client_id={args.client_id} clean_session={args.clean_session}")
        c.subscribe(args.topic, qos=args.qos)

    def on_message(c, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            seq = int(data.get("seq"))
        except Exception:
            seq = stats.last_seq + 1
        stats.record(seq)
        print(f"[subscriber] recv seq={seq} qos={msg.qos} :: {stats.summary()}")

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(args.host, args.port, keepalive=30)
    client.loop_forever()


if __name__ == "__main__":
    main()
