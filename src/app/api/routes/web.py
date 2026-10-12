"""Static web client (ADR 0007).

Files are served by name from WEB_FILES, never by directory, so a stray file in web/
(tests, notes, editor backups) is never exposed. A new client file is served only once
it is listed here.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse, RedirectResponse, Response

logger = logging.getLogger(__name__)

WEB_FILES: dict[str, str] = {
    "": "text/html; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
    "api.js": "text/javascript; charset=utf-8",
    "views.js": "text/javascript; charset=utf-8",
    "process-views.js": "text/javascript; charset=utf-8",
    "analysis-views.js": "text/javascript; charset=utf-8",
    "format.js": "text/javascript; charset=utf-8",
    "styles.css": "text/css; charset=utf-8",
    "icon.svg": "image/svg+xml",
}

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
)

SECURITY_HEADERS = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-cache",
}


def mount_web_client(app: FastAPI, web_dir: Path) -> None:
    """Serve the client under /ui/. Without web_dir the API runs on its own."""
    if not (web_dir / "index.html").is_file():
        logger.info("web_client_disabled", extra={"web_dir": str(web_dir)})
        return

    router = APIRouter(include_in_schema=False)

    @router.get("/")
    def root() -> RedirectResponse:
        return RedirectResponse("/ui/", status_code=307)

    @router.get("/ui")
    def ui_without_slash() -> RedirectResponse:
        return RedirectResponse("/ui/", status_code=307)

    @router.api_route("/ui/{name:path}", methods=["GET", "HEAD"])
    def asset(name: str) -> Response:
        media_type = WEB_FILES.get(name)
        if media_type is None:
            return Response("Not found", status_code=404, headers=SECURITY_HEADERS)
        return FileResponse(
            web_dir / (name or "index.html"), media_type=media_type, headers=SECURITY_HEADERS
        )

    app.include_router(router)
