from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_db: str = "naturedb"
    postgres_user: str = "nature"
    postgres_password: str = "nature"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    mml_api_key: str | None = None

    syke_natura_wfs_url: str | None = None
    syke_natura_sci_typename: str | None = None
    syke_natura_spa_typename: str | None = None
    syke_natura_sac_typename: str | None = None

    forest_stand_wfs: str | None = None
    forest_stand_typename: str = "v1:stand"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
