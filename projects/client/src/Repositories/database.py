from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from settings import config


class Database:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.engine = cls._instance._create_engine()
            cls._instance.SessionLocal = sessionmaker(
                bind=cls._instance.engine,
                autoflush=False,
                autocommit=False
            )
 
        return cls._instance

    def _create_engine(self):
        db_url = (
            f"postgresql+psycopg2://{config.db_username}:"
            f"{config.db_password}@"
            f"{config.db_host}:"
            f"{config.db_port}/"
            f"{config.db_name}"
        )
        return create_engine(db_url)
    
get_db = Database().SessionLocal()

