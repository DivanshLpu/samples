from fastapi import FastAPI,HTTPException
import src.data as data

app = FastAPI()

@app.get("/posts")
def getAllPosts():
    return data.testprojects

@app.get("/posts/{id}")
def getSpecificPost(id:int):
    return data.testprojects.get(id)