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
def infer__RSF_PR_LR__pipeline_route(date_stop : str = None, mlflow : bool = True):
    try:
        #to date time
        if date_stop:
            date_stop = datetime.datetime.strptime(date_stop, "%Y-%m-%d %H:%M:%S")
        train_test_metrics, df_infered, nb_matches_infered, first_match_name, last_match_name, datetime_inference = infer__RSF_PR_LR__pipeline(date_stop=date_stop, mlflow=mlflow)

        logging.info(f"RSF_PR_LR pipeline completed")
        return {"status": "success", "datetime_inference" : datetime_inference,
                "train_test_metrics": train_test_metrics, "nb_matches_infered": nb_matches_infered,
                "first_match_name": first_match_name, "last_match_name": last_match_name}
    except Exception as e:
        logging.error(f"RSF_PR_LR pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/optim")
def resolve_fik_route(datetime_first_match=None, model='RSF_PR_LR', n_matches = None, same_day = False, bookmakers = None, 
                      bankroll = 1, method = 'SLSQP', utility_fn = 'Kelly', optim_label = 'manual', alpha=1, l=10):
    """Resolve the OF problem for a given datetime_first_match and model
    
    Parameters
    ----------
        datetime_first_match (str): The datetime before the first match to consider
        model (str): The model to use for the predictions
        n_matches (int): The number of matches to consider
        same_day (bool): If True, only matches of the same day as the first match will be considered
        bookmakers (str): The bookmakers to consider
        bankroll (float): The bankroll to consider
        method (str): The optimization method to use
        utility_fn (str): The utility function to use
        optim_label (str): The label of the optimization
        alpha (float): the risk aversion factor if using Exponential Utility function
        l (int): the multiplication factor for the variance if using Linear Utility function
        
    Returns
    -------
        dict: The results of the optimization
    """
    try:
        if datetime_first_match:
            datetime_first_match = datetime.datetime.strptime(datetime_first_match, "%Y-%m-%d %H:%M:%S")
        if n_matches:
            n_matches = int(n_matches)
        if bookmakers:
            bookmakers = bookmakers.split(',')
        if bankroll:
            bankroll = float(bankroll)
        datetime_optim, df_results = find__of(datetime_first_match=datetime_first_match, model=model, n_matches=n_matches, same_day=same_day, bookmakers=bookmakers, 
                                  bankroll=bankroll, method=method, utility_fn=utility_fn, optim_label=optim_label, l=10)
        logging.info(f"Optimisation completed")
        return {"status": "success", "datetime_optim": datetime_optim, 'optim_label':optim_label,
                "df_results": df_results}
    except Exception as e:
        logging.error(f"Optimisation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))