from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from kafka import KafkaProducer, KafkaConsumer
import threading, json, os, logging

TOPIC = "event-topic"
BROKER = os.getenv("KAFKA_BROKERS", "kafka:9092")

app = FastAPI()

producer = KafkaProducer(
    bootstrap_servers=BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

logging.basicConfig(level=logging.INFO)


@app.get("/api/events/health")
def health_check():
    return {"status": True}


@app.post("/api/events/{event_type}")
async def send_event(event_type: str, req: Request):
    try:
        body = await req.body()
        if not body:
            logging.error("[ERROR] Empty request body")
            return JSONResponse(status_code=400, content={"status": "error", "detail": "Empty request body"})

        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            logging.error(f"[JSON ERROR] Invalid JSON: {e}")
            return JSONResponse(status_code=400, content={"status": "error", "detail": "Invalid JSON"})

        event = {"type": event_type, "payload": data}
        producer.send(TOPIC, event)
        logging.info(f"[Produced] {event}")
        return JSONResponse(status_code=201, content={"status": "success"})

    except Exception as e:
        logging.error(f"[ERROR] Failed to handle event: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})


def consume():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id="events-group"
    )
    for msg in consumer:
        logging.info(f"[Consumed] {msg.value}")


threading.Thread(target=consume, daemon=True).start()
