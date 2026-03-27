import argparse
import json
import time
import uuid

import paho.mqtt.client as mqtt


def now_ms() -> int:
    return int(time.time() * 1000)


def main() -> None:
    p = argparse.ArgumentParser(description="MQTT QoS publisher (v3.1.1)")
    p.add_argument("--host", default="mosquitto")
    p.add_argument("--port", type=int, default=1883)
    p.add_argument("--topic", default="qos/sim")
    p.add_argument("--qos", type=int, choices=[0, 1, 2], default=1)
    p.add_argument("--count", type=int, default=100)
    p.add_argument("--interval-ms", type=int, default=100)
    p.add_argument("--client-id", default=f"pub-{uuid.uuid4().hex[:8]}")
    p.add_argument("--clean-session", action="store_true")
    args = p.parse_args()

    client = mqtt.Client(client_id=args.client_id, clean_session=args.clean_session, protocol=mqtt.MQTTv311)

    client.connect(args.host, args.port, keepalive=30)
    client.loop_start()
    try:
        for seq in range(1, args.count + 1):
            payload = {"seq": seq, "sent_ts_ms": now_ms(), "publisher_id": args.client_id}
            info = client.publish(args.topic, json.dumps(payload).encode("utf-8"), qos=args.qos, retain=False)
            if args.qos in (1, 2):
                info.wait_for_publish(timeout=5)
            print(f"[publisher] sent seq={seq} qos={args.qos} mid={info.mid}")
            time.sleep(args.interval_ms / 1000.0)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
