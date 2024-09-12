from fastapi import FastAPI, HTTPException
from app.pipeline__RSF_PR_LR.infer__RSF_PR_LR import infer__RSF_PR_LR__pipeline
from app.pipeline__RSF_PS_LR.infer__RSF_PS_LR import infer__RSF_PS_LR__pipeline
from app.pipeline__OF.find__OF import find__of
import app._config
import logging
import datetime

app = FastAPI()

logger = logging.getLogger('pipelines')

@app.get("/")
def read_root():
    return {"Info": "Microservice for ml pipelines"}

@app.get("/infer/RSF_PR_LR")
def infer__RSF_PR_LR__pipeline_route(date_stop=None):
    try:
        #to date time
        if date_stop:
            date_stop = datetime.datetime.strptime(date_stop, "%Y-%m-%d %H:%M:%S")
        infer__RSF_PR_LR__pipeline(date_stop=date_stop)
        logging.info(f"RSF_PR_LR pipeline completed")
        return {"status": "success"}
    except Exception as e:
        logging.error(f"RSF_PR_LR pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/infer/RSF_PS_LR")
def infer__RSF_PS_LR__pipeline_route(date_stop=None):
    try:
        #to date time
        if date_stop:
            date_stop = datetime.datetime.strptime(date_stop, "%Y-%m-%d %H:%M:%S")
        infer__RSF_PS_LR__pipeline(date_stop=date_stop)
        logging.info(f"RSF_PS_LR pipeline completed")
        return {"status": "success"}
    except Exception as e:
        logging.error(f"RSF_PS_LR pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/optim")
def resolve_fik_route(datetime_first_match=None, model='RSF_PR_LR', n_matches = None, bookmakers = None, bankroll = 1, method = 'SLSQP'):
    try:
        if datetime_first_match:
            datetime_first_match = datetime.datetime.strptime(datetime_first_match, "%Y-%m-%d %H:%M:%S")
        if n_matches:
            n_matches = int(n_matches)
        if bookmakers:
            bookmakers = bookmakers.split(',')
        if bankroll:
            bankroll = float(bankroll)
        datetime_optim = find__of(datetime_first_match=datetime_first_match, model=model, n_matches=n_matches, bookmakers=bookmakers, 
                                  bankroll=bankroll, method=method)
        logging.info(f"Optimisation completed")
        return {"status": "success", "datetime_optim": datetime_optim}
    except Exception as e:
        logging.error(f"Optimisation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))