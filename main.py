from fastapi import FastAPI

# Create a FastAPI instance
app = FastAPI()

# Define a root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to your FastAPI application!"}

# Define a sample endpoint
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
