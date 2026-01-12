from fastapi import FastAPI
from dotenv import load_dotenv
from api import router

# .env 파일에서 환경 변수 로드
load_dotenv()

app = FastAPI()

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}
