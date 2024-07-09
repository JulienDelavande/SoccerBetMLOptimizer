from fastapi import FastAPI, HTTPException
from app.pipeline__RSF_PR_LR.infer__RSF_PR_LR import infer__RSF_PR_LR__pipeline
from app.pipeline__RSF_PS_LR.infer__RSF_PS_LR import infer__RSF_PS_LR__pipeline
app = FastAPI()

@app.get("/")
def read_root():
    return {"Info": "Microservice for ml pipelines"}

@app.get("/infer/RSF_PR_LR")
def infer__RSF_PR_LR__pipeline_route(date_stop=None):
    try:
        infer__RSF_PR_LR__pipeline(date_stop=date_stop)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/infer/RSF_PS_LR")
def infer__RSF_PS_LR__pipeline_route(date_stop=None):
    try:
        infer__RSF_PS_LR__pipeline(date_stop=date_stop)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))