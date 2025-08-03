from fastapi import FastAPI, Request
from app.routes.user_routes import router as user_router
from app.routes.author_routes import router as author_router
from app.routes.book_routes import router as book_router
from fastapi.middleware.cors import CORSMiddleware
from app.routes.order_routes import router as order_router
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI() 



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 

app.include_router(user_router)
app.include_router(author_router)
app.include_router(book_router)
app.include_router(order_router)