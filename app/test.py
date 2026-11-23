from fastapi import FastAPI

app=FastAPI()

@app.get("/")
def test():
    return{
        "message":"This is my portfolio Api"
    }