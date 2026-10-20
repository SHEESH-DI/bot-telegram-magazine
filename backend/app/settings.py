from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = (
        "postgresql://catalog:catalog-local-password@postgres:5432/catalog"
    )
    s3_endpoint: str = "minio:9000"
    s3_access_key: str = "catalog"
    s3_secret_key: str = "catalog-local-secret"
    s3_bucket: str = "products"
    s3_secure: bool = False
    bot_token: str = ""
    admin_ids: str = ""
    webhook_secret: str = ""
    public_url: str = "http://localhost:8095"
    cookie_secure: bool = False

    @property
    def admins(self) -> set[int]:
        return {
            int(value.strip()) for value in self.admin_ids.split(",") if value.strip()
        }


settings = Settings()
