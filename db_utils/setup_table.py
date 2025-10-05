from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.orm import declarative_base
import tomllib

# Load connection string from config/env.toml
with open('config/env.toml', 'rb') as f:
    config = tomllib.load(f)
connection_string = config['dev']['connection_string']

engine = create_engine(connection_string)
Base = declarative_base()

class Wishlist(Base):
    __tablename__ = 'wishlist'
    user_id = Column(String(255), primary_key=True)
    item_name = Column(String(255), primary_key=True)
    item_comment = Column(Text)
    item_link = Column(String(512))

class SecretSanta(Base):
    __tablename__ = 'secret_santa'
    giver = Column(String(255), primary_key=True)
    receiver = Column(String(255), nullable=False)

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tables created successfully.")
