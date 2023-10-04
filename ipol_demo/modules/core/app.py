from conversion.router import conversionRouter
from demoinfo.router import demoinfoRouter
from dispatcher.router import dispatcherRouter
from fastapi import FastAPI

from core.router import coreRouter

app = FastAPI(root_path="/api")


app.include_router(coreRouter)
app.include_router(demoinfoRouter)
app.include_router(dispatcherRouter)
app.include_router(conversionRouter)
