from sqlalchemy import Table, Column, Integer, String, Float, Boolean, MetaData, DateTime, ForeignKey, TIMESTAMP

metadata = MetaData()


call_info_table = Table(
    'call_info',
    metadata,
    Column('operator_id', Integer, ForeignKey('operator.id'), nullable=False),  # Operator ID
    Column('client_id', Integer, ForeignKey('client.id'), nullable=False),  # Client ID
    Column('operator_txt', String, nullable=True),
    Column('client_txt', String, nullable=True),
    Column('dialog_txt', String, nullable=True),
    Column('status_ai', String, nullable=True),
    Column('status_1c', String, nullable=True),
    Column('datetime', String, nullable=True),
    Column('order_id', String, nullable=True),
    Column('call_id', String, nullable=True),
    Column('call_info', String, nullable=True),
    Column('audio_path', String, nullable=True),
)

operator_table = Table(
    'operator',
    metadata,
    Column('id', Integer, primary_key=True, index=True, autoincrement=True),
    Column('name', String, nullable=False),
)


client_table = Table(
    'client',
    metadata,
    Column('id', Integer, primary_key=True, index=True, autoincrement=True),
    Column('name', String, nullable=False),
    Column('phone', String, nullable=False),
)