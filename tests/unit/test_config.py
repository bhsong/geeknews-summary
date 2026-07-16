"""app.config.Settings 단위 테스트.

src/db.php의 getDbName()·getDb() 동작을 characterization으로 이식한다.
Settings는 명시 kwargs로 생성해 실제 .env에 의존하지 않게 한다(_env_file=None).
"""

from app.config import Settings


def _settings(**overrides: str) -> Settings:
    """hermetic Settings 생성 헬퍼.

    DB 관련 6개 필드를 명시로 넘긴다. pydantic-settings 우선순위(init 인자 >
    OS env > .env)상 init 인자가 최우선이라, 실제 .env/OS env가 있어도 결과가
    결정적이다. gemini_* 필드는 여기서 검증하지 않으므로 넘기지 않는다(실 .env
    값이 들어오지만 database_* 결과에 영향이 없다).
    """
    base: dict[str, str] = {
        "app_env": "production",
        "db_host": "localhost",
        "db_name": "geeknews",
        "db_name_test": "",
        "db_user": "user",
        "db_pass": "pass",
    }
    base.update(overrides)
    return Settings(**base)


def test_testing_env_uses_test_db_name() -> None:
    """APP_ENV=testing이면 DB_NAME_TEST를 데이터베이스명으로 쓴다."""
    settings = _settings(app_env="testing", db_name_test="geeknews_test")

    assert settings.database_name == "geeknews_test"


def test_testing_env_falls_back_to_db_name_suffix() -> None:
    """APP_ENV=testing인데 DB_NAME_TEST가 없으면 DB_NAME + "_test"를 쓴다."""
    settings = _settings(app_env="testing", db_name="geeknews", db_name_test="")

    assert settings.database_name == "geeknews_test"


def test_database_url_uses_pymysql_and_database_name() -> None:
    """database_url은 pymysql 드라이버 + database_name으로 조립한다(비-testing)."""
    settings = _settings(
        app_env="production",
        db_host="dbhost",
        db_name="geeknews",
        db_user="user",
        db_pass="secret",
    )

    assert (
        settings.database_url
        == "mysql+pymysql://user:secret@dbhost/geeknews?charset=utf8mb4"
    )
