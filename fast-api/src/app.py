from fastapi import FastAPI,HTTPException,File, UploadFile,Form,Depends
import src.data as data
from src.schemas import PostCreate, PostResponce
from src.db import Post,get_session,create_db_and_table

from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_table()
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/posts")
def getAllPosts(limit: int = None):
    if limit:
        sliced_items = list(data.testprojects.items())[:limit]
        return {key: val for key, val in sliced_items}
    return data.testprojects

@app.get("/posts/{id}") 
def getSpecificPost(id:int) -> PostResponce:
    if id not in data.testprojects :
        raise HTTPException(status_code=404,detail="Post Not found")
    return data.testprojects.get(id)

@app.post("/posts")
def createPosts(post: PostCreate) -> PostResponce:
    new_post = {"title":post.title , "content": post.content}
    data.testprojects[max(data.testprojects.keys())+1]=new_post
    return new_post