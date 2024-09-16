from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from shihab.config import SessionLocal, create_tables, engine, Base
from shihab.services.auth import init_auth_routes
from shihab.services.messages import init_message_routes
from shihab.graph_db import queryGraph
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

init_auth_routes(app)
init_message_routes(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# Initialize routes
# init_auth_routes(app)
# init_message_routes(app)

@app.post("/query")
async def post_data(query: str):
    return "hello world"
    # return queryGraph(query=query)

# Define the request body model
class QueryModel(BaseModel):
    query: str


@app.post("/query-v2")
async def post_datav2(data: QueryModel):
    return queryGraph(query=data.query)

if __name__ == "__main__":
    # Base.metadata.create_all(bind=engine)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
