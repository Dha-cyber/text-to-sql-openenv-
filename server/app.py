"""
server/app.py — OpenEnv multi-mode deployment entry point.
Exposes the FastAPI app and a callable main() for the validator.
"""
import uvicorn
from app.main import app  # noqa: F401

__all__ = ["app", "main"]


def main():
    """Callable entry point required by OpenEnv validator."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=7860,
        reload=False,
    )


if __name__ == "__main__":
    main()
