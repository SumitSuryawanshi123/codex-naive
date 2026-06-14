import os

from app.config import Settings


def test_OPENAI_API_KEY_env_populates_llm_api_key() -> None:
    original_gpt_key = os.environ.get("OPENAI_API_KEY")
    original_openai_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ.pop("OPENAI_API_KEY", None)

    try:
        settings = Settings(_env_file=None)
    finally:
        if original_gpt_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = original_gpt_key
        if original_openai_key is not None:
            os.environ["OPENAI_API_KEY"] = original_openai_key

    assert settings.openai_api_key == "test-key"
