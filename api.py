from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from elastic import Elastic
app = FastAPI()
elastic = Elastic('localhost', 9200, '<api_key>','soft98')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def search(q: str, offset: int = 0, limit: int = 20):
    time, total,res, suggest = elastic.search(q, offset, limit)
    return {"time": time, 'total':total, 'res':res,'suggest':suggest}

@app.get("/suggest")
async def suggest(q: str, limit: int = 10):
    time,res = elastic.suggest(q, limit)
    return {"time": time, 'res':res}
