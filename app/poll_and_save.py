import asyncio
import os
import psycopg2
from dotenv import load_dotenv
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, get_cmd
)

load_dotenv()

OIDS = {
    "psState": "1.3.6.1.4.1.46056.2.1",
    "psVoltInput": "1.3.6.1.4.1.46056.2.6",
    "psVoltageOutput": "1.3.6.1.4.1.46056.2.8",
    "psTempInside": "1.3.6.1.4.1.46056.2.11",
    "psChargeBatt": "1.3.6.1.4.1.46056.2.22",
}


async def poll_device(host, port, community):
    """Опрашивает устройство по SNMP и возвращает значения + статус качества каждой метрики."""
    snmpEngine = SnmpEngine()
    transport = await UdpTransportTarget.create((host, port))

    results = {}
    quality = {}

    for name, oid in OIDS.items():
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            snmpEngine,
            CommunityData(community, mpModel=1),
            transport,
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )

        if errorIndication:
            print(f"[{name}] Ошибка: {errorIndication}")
            results[name] = 0.0
            quality[name] = "timeout"
        elif errorStatus:
            print(f"[{name}] Ошибка статуса: {errorStatus.prettyPrint()}")
            results[name] = 0.0
            quality[name] = "invalid"
        else:
            for varBind in varBinds:
                results[name] = float(varBind[1])
                quality[name] = "good"

    snmpEngine.close_dispatcher()
    return results, quality


def get_devices_from_db(conn):
    """Достаёт список устройств из таблицы devices."""
    cur = conn.cursor()
    cur.execute("SELECT id, name, host, port, community FROM devices")
    devices = cur.fetchall()
    cur.close()
    return devices


def save_metrics_to_db(conn, device_id, metrics: dict, quality: dict):
    """Сохраняет словарь метрик в таблицу metric_values, с учётом качества каждого значения."""
    cur = conn.cursor()
    for metric_name, value in metrics.items():
        q = quality.get(metric_name, "good")
        cur.execute(
            """
            INSERT INTO metric_values (device_id, metric_name, metric_value, quality, source)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (device_id, metric_name, value, q, "polling")
        )
    conn.commit()
    cur.close()


async def poll_all_devices(conn):
    """Опрашивает все устройства из БД один раз."""
    devices = get_devices_from_db(conn)
    print(f"Найдено устройств в БД: {len(devices)}")

    for device_id, name, host, port, community in devices:
        print(f"\nОпрашиваю: {name} ({host}:{port})")
        metrics, quality = await poll_device(host, port, community)
        print(f"Получено значений: {sum(1 for q in quality.values() if q == 'good')}/{len(metrics)}")

        save_metrics_to_db(conn, device_id, metrics, quality)
        print(f"Сохранено в базу для устройства '{name}'")


async def main():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", 30))

    try:
        while True:
            await poll_all_devices(conn)
            print(f"\nЖду {poll_interval} секунд до следующего опроса...\n{'-'*40}")
            await asyncio.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nОстановка по Ctrl+C")
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())
