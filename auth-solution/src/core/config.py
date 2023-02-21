from pydantic import BaseSettings, Field, PostgresDsn


class Database(BaseSettings):
    db: str = Field(..., env='AUTH_POSTGRES_DB')
    user: str = Field(..., env='AUTH_POSTGRES_USER')
    password: str = Field(..., env='AUTH_POSTGRES_PASSWORD')
    host: str = Field(..., env='AUTH_POSTGRES_HOST')
    port: int = Field('5433', env='AUTH_POSTGRES_PORT')

class Settings(BaseSettings):
    SECRET_KEY: str = Field(..., env='SECRET_KEY')
    
    AUTH_REDIS_HOST: str = Field(..., env='AUTH_REDIS_HOST')
    AUTH_REDIS_PORT: str = Field(6380, env='AUTH_REDIS_PORT')

    SECURITY_TOKEN_AUTHENTICATION_HEADER: str = Field(..., env='SECURITY_TOKEN_AUTHENTICATION_HEADER')
    SECURITY_PASSWORD_SALT: str = Field(..., env='SECURITY_PASSWORD_SALT')

    pg_db = Database()
    SQLALCHEMY_DATABASE_URI: PostgresDsn = f'postgresql+psycopg2://{pg_db.user}:{pg_db.password}@{pg_db.host}:{pg_db.port}/{pg_db.db}'


settings = Settings()