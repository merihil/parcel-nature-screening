from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_db: str = "naturedb"
    postgres_user: str = "nature"
    postgres_password: str = "nature"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    mml_api_key: str | None = None

    # Public WFS endpoints, fixed for these data sources — not secrets, don't
    # vary by environment. Given real defaults so nothing needs to be filled
    # in .env, but still overridable there if a source ever changes.
    syke_natura_wfs_url: str = "https://paikkatiedot.ymparisto.fi/geoserver/inspire_ps/ows"
    syke_natura_sci_typename: str = "inspire_ps:PS.ProtectedSitesProposedSiteOfCommunityImportance"
    syke_natura_spa_typename: str = "inspire_ps:PS.ProtectedSitesSpecialProtectionArea"
    syke_natura_sac_typename: str = "inspire_ps:PS.ProtectedSitesSpecialAreaOfConservation"

    forest_stand_wfs: str = "https://avoin.metsakeskus.fi/rajapinnat/v1/stand/wfs"
    forest_stand_typename: str = "v1:stand"

    special_habitat_wfs: str = "https://avoin.metsakeskus.fi/rajapinnat/v1/habitat/wfs"
    special_habitat_typename: str = "v1:habitat"

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
