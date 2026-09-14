from sqlalchemy import Column, Integer, String, Numeric, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    host = Column(String(100), nullable=False)
    port = Column(Integer, nullable=False)
    community = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class MetricValue(Base):
    __tablename__ = "metric_values"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric, nullable=False)
    recorded_at = Column(TIMESTAMP, server_default=func.now())
    quality = Column(String(20), server_default="good")
    source = Column(String(20), server_default="polling")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    event_type = Column(String(100), nullable=False)
    message = Column(Text)
    occurred_at = Column(TIMESTAMP, server_default=func.now())

class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200))
    unit = Column(String(20))
    oid = Column(String(100))
