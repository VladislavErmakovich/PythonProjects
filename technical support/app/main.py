from fastapi import FastAPI


app = FastAPI(title="CRM support",
              description="API для тех поддержки",
              version="1.0.0")


@app.get("/")
async def root():
    return ({"message": "CRM работает", "status": "ok"})

