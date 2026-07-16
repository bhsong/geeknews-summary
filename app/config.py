"""애플리케이션 설정

pydantic-settings가 .env 로딩 담당. OS 환경변수가 .env 보다 우선이며,
(.env, .env.local) 순으로 읽어 뒤 파일이 앞 파일을 덮어쓴다 (비밀값은 .env.local)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "production"
    db_host: str = "localhost"
    db_name: str = ""
    db_name_test: str = ""
    db_user: str = ""
    db_pass: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    @property
    def database_name(self) -> str:
        if self.app_env == "testing":
            return self.db_name_test or f"{self.db_name}_test"
        return self.db_name

    @property
    def database_url(self) -> str:
        """SQLAlchemy(PyMySQL) 접속 URL. database_name으로 testing 분기 상속"""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}/{self.database_name}?charset=utf8mb4"
        )
