from fastapi import FastAPI
from app.routes.user_routes import router as user_router
from app.routes.author_routes import router as author_router



app = FastAPI() 


app.include_router(user_router)
app.include_router(author_router)
