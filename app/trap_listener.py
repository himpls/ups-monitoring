import os
import psycopg2
from dotenv import load_dotenv
from pysnmp.entity import engine, config
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv

load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))

snmpEngine = engine.SnmpEngine()

config.add_transport(
    snmpEngine,
    udp.DOMAIN_NAME,
    udp.UdpTransport().open_server_mode(('0.0.0.0', 1162))
)

config.add_v1_system(snmpEngine, 'my-area', 'public')


def cbFun(snmpEngine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
    print("\n--- Получен Trap ---")

    event_type = None
    message = None

    for name, val in varBinds:
        oid_str = name.prettyPrint()
        val_str = val.prettyPrint()
        print(f"{oid_str} = {val_str}")

        # Пропускаем служебные OID (uptime и snmpTrapOID),
        # берём только "полезную нагрузку" — наш собственный OID из PS-MIB
        if oid_str.startswith("1.3.6.1.4.1.46056"):
            event_type = oid_str
            message = val_str

    if event_type is None:
        print("Не найдено полезных данных в trap, пропускаю сохранение")
        return

    # Упрощение: пока считаем, что trap всегда от device_id=1 —
    # в реальной системе нужно сопоставлять по IP-адресу отправителя
    device_id = 1

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events (device_id, event_type, message)
        VALUES (%s, %s, %s)
        """,
        (device_id, event_type, message)
    )
    conn.commit()
    cur.close()
    print(f"Сохранено в БД: device_id={device_id}, event_type={event_type}, message={message}")


ntfrcv.NotificationReceiver(snmpEngine, cbFun)

print("Слушаю Trap на порту 1162...")
snmpEngine.transport_dispatcher.job_started(1)

try:
    snmpEngine.open_dispatcher()
except Exception:
    snmpEngine.close_dispatcher()
    raise
