import os
import posixpath
from typing import Annotated

from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()


class ConfigModel(BaseModel):
    store_location: str = "./uploads"
    access_token: str = "114514"


def load_config(location: str = "config.json"):
    with open(location, "rb") as fp:
        return ConfigModel.model_validate_json(fp.read())


config = load_config()
os.makedirs(config.store_location, exist_ok=True)


async def verify_token(authorization: str = Header("")):
    if len(_ := authorization.split(maxsplit=1)) == 2:
        token = _[1]
    elif _:
        token = _[0]
    else:
        raise HTTPException(403, "不是哥们，你 token 呢")
    if token.strip() != config.access_token.strip():
        raise HTTPException(403, "不是哥们，你的 token 错辣")
    return authorization


AcTokenDep = Annotated[str, Depends(verify_token)]


@app.post("/upload")
async def upload_file(
    _: AcTokenDep,
    file: UploadFile = File(...),
):
    filename = posixpath.basename(file.filename)
    filepath = posixpath.join(config.store_location, filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())
    return {"path": posixpath.normpath(posixpath.abspath(filepath))}


@app.post("/files")
async def list_files(_: AcTokenDep):
    files = os.listdir(config.store_location)
    return {"files": files}


class DownloadRequest(BaseModel):
    path: str


@app.get("/download")
async def download_file(delr: DownloadRequest):
    if not posixpath.exists(delr.path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(delr.path)


class DeleteRequest(BaseModel):
    path: str


@app.post("/delete")
async def delete_file(delete_request: DeleteRequest, _: AcTokenDep):
    path = delete_request.path
    if not posixpath.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    os.remove(path)
    return "ok"
