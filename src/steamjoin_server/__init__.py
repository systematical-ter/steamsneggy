from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/join/")
def join(id1: int, id2: int, id3: int):
    return RedirectResponse(f"steam://joinlobby/{id1}/{id2}/{id3}")