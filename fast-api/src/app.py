from fastapi import FastAPI,HTTPException
import src.data as data
from src.schemas import PostCreate

app = FastAPI()

@app.get("/posts")
def getAllPosts(limit: int = None):
    if limit:
        sliced_items = list(data.testprojects.items())[:limit]
        return {key: val for key, val in sliced_items}
    return data.testprojects

@app.get("/posts/{id}")
def getSpecificPost(id:int):
    if id not in data.testprojects :
        raise HTTPException(status_code=404,detail="Post Not found")
    return data.testprojects.get(id)

@app.post("/posts")
def createPosts(post: PostCreate):
    new_post = {"title":post.title , "content": post.content}
    data.testprojects[max(data.testprojects.keys())+1]=new_post
    return new_post