import asyncio
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, get_cmd
)

OIDS = {
    "psState": "1.3.6.1.4.1.46056.2.1",
    "psVoltInput": "1.3.6.1.4.1.46056.2.6",
    "psVoltageOutput": "1.3.6.1.4.1.46056.2.8",
    "psTempInside": "1.3.6.1.4.1.46056.2.11",
    "psChargeBatt": "1.3.6.1.4.1.46056.2.22",
}


async def poll_device(host, port, community):
    snmpEngine = SnmpEngine()
    transport = await UdpTransportTarget.create((host, port))

    results = {}
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
        elif errorStatus:
            print(f"[{name}] Ошибка статуса: {errorStatus.prettyPrint()}")
        else:
            for varBind in varBinds:
                results[name] = varBind[1]

    snmpEngine.close_dispatcher()
    return results


if __name__ == "__main__":
    data = asyncio.run(poll_device("127.0.0.1", 1161, "ps1"))
    print("\n--- Результат опроса устройства ---")
    for name, value in data.items():
        print(f"{name}: {value}")
