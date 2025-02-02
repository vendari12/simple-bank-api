import asyncio
from contextlib import asynccontextmanager

import typer
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from server.config.settings import settings
from server.models.user import User
from server.routes.router import router
from rq import Worker, Connection
from server.utils.queues import QueueManager
from server.utils.cache import get_sync_redis_client
from server.utils.constants import SERVICE_PORT
from server.utils.db import AsyncSession, async_session, init_models
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware


@asynccontextmanager
async def setup_db(app: FastAPI):
    await init_models()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V2_STR}/openapi.json",
    docs_url=f"{settings.API_V2_STR}",
    redoc_url=f"{settings.API_V2_STR}/redocs",
    lifespan=setup_db,
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


app.include_router(router, prefix=settings.API_V2_STR)


# TODO: Use a regex to validate URL pattern from requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

cli = typer.Typer()


@cli.command()
def runserver():
    uvicorn.run(
        "manage:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,
        log_level="info",
    )


@cli.command()
def load_default_users():
    loop = asyncio.get_event_loop()

    # Database Midleware session
    async def get_session() -> AsyncSession:
        async with async_session() as session:
            await User.load_default_users(session)

    loop.run_until_complete(get_session())



@cli.command()
def run_task_queue():
    # Define the list of queues to listen to
    listen = ["default"]
    queue = QueueManager.get_queue()
    with Connection(get_sync_redis_client()):
        worker = Worker(map(queue, listen))
        worker.work()


if __name__ == "__main__":
    cli()
