from fastapi import FastAPI,HTTPException
import src.data as data

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
def createPosts():
    return 0