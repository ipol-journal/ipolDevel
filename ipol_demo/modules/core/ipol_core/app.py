from .conversion.router import conversionRouter
from .core.router import coreRouter
from .demoinfo.router import demoinfoRouter
from .dispatcher.router import dispatcherRouter
from fastapi import FastAPI

app = FastAPI(root_path="/api")


app.include_router(coreRouter)
app.include_router(demoinfoRouter)
app.include_router(dispatcherRouter)
app.include_router(conversionRouter)
