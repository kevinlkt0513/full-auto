from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .backend.routes import setup as setup_routes
from .backend.routes import auth as auth_routes
from .backend.routes import wizard as wizard_routes
from .backend.routes import preflight as preflight_routes
from .backend.routes import sniff as sniff_routes
from .backend.routes import config as config_routes
from .backend.routes import run as run_routes


FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="Gpt-Agreement-Payment webui")
    api_routers = (
        setup_routes.router,
        auth_routes.router,
        wizard_routes.router,
        preflight_routes.router,
        sniff_routes.router,
        config_routes.router,
        run_routes.router,
    )
    for router in api_routers:
        app.include_router(router)
        app.include_router(router, prefix="/webui")

    @app.get("/api/healthz")
    def healthz():
        return {"status": "ok"}

    if FRONTEND_DIST.exists():
        assets_dir = FRONTEND_DIST / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
            app.mount("/webui/assets", StaticFiles(directory=assets_dir), name="webui-assets")

        @app.get("/{full_path:path}")
        def spa(full_path: str):
            if full_path.startswith("api/"):
                # Should not reach here — APIRouters claim /api/* — but guard just in case
                return FileResponse(FRONTEND_DIST / "index.html", status_code=404)
            f = FRONTEND_DIST / full_path
            try:
                f.resolve().relative_to(FRONTEND_DIST.resolve())
            except ValueError:
                # Path escapes dist — serve index.html instead
                return FileResponse(FRONTEND_DIST / "index.html")
            if f.is_file():
                return FileResponse(f)
            return FileResponse(FRONTEND_DIST / "index.html")

    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=8765)
