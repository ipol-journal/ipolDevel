from archive.router import archiveRouter
from blobs.router import blobsRouter
from conversion.router import conversionRouter
from core.router import coreRouter
from demoinfo.router import demoinfoRouter
from dispatcher.router import dispatcherRouter
from fastapi import FastAPI

app = FastAPI(root_path="/api")


app.include_router(coreRouter)
app.include_router(demoinfoRouter)
app.include_router(dispatcherRouter)
app.include_router(conversionRouter)
app.include_router(archiveRouter)
app.include_router(blobsRouter)
