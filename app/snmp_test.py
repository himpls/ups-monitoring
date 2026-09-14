import asyncio
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, get_cmd
)


async def get_snmp_value(host, port, community, oid):
    snmpEngine = SnmpEngine()
    errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
        snmpEngine,
        CommunityData(community, mpModel=1),  # mpModel=1 значит v2c
        await UdpTransportTarget.create((host, port)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    if errorIndication:
        print(f"Ошибка: {errorIndication}")
    elif errorStatus:
        print(f"Ошибка статуса: {errorStatus.prettyPrint()}")
    else:
        for varBind in varBinds:
            print(f"{varBind[0]} = {varBind[1]}")

    snmpEngine.close_dispatcher()


if __name__ == "__main__":
    # psVoltInput - входное напряжение
    asyncio.run(get_snmp_value("127.0.0.1", 1161, "ps1", "1.3.6.1.4.1.46056.2.6"))
