from fastapi import FastAPI, HTTPException
from app.pipeline__RSF_PR_LR.infer__RSF_PR_LR import infer__RSF_PR_LR__pipeline
from app.pipeline__OF.find__OF import find__of
from app.models.optimization_models import (
    OptimizationRequest,
    OptimizationResponse,
)
from app.models.prediction_models import (
    InferenceRequest,
    InferenceResponse,
)
import app._config
import logging

app = FastAPI(
    title="Predict Score Logistic Regression API",
    version="1.0.0",
    description="Microservice for football match outcome prediction and betting optimization"
)

logger = logging.getLogger('pipelines')

@app.get("/")
def read_root():
    return {"Info": "Microservice for ml pipelines"}

@app.post(
    "/predict",
    response_model=InferenceResponse,
    tags=["prediction"]
)
def predict(body: InferenceRequest):
    try:
        metrics, _, nb, first_name, last_name, dt_inf = infer__RSF_PR_LR__pipeline(
            datetime_stop=body.datetime_stop
        )
        return InferenceResponse(
            status="success",
            datetime_inference=dt_inf,
            train_test_metrics=metrics,
            nb_matches_inferred=nb,
            first_match_name=first_name,
            last_match_name=last_name,
        )
    except Exception as e:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.post(
    "/optimize",
    response_model=OptimizationResponse,
    tags=["optimization"]
)
def optimize(body: OptimizationRequest):
    try:
        dt_opt, df_results = find__of(
            datetime_first_match=body.datetime_first_match,
            model="RSF_PR_LR",
            n_matches=body.n_matches,
            same_day=body.same_day,
            bookmakers=body.bookmakers,
            bankroll=body.bankroll,
            method=body.method,
            utility_fn=body.utility_fn,
            optim_label=body.optim_label,
            l=body.l,
            divisor=body.divisor,
        )
        if hasattr(df_results, "to_dict"):
            # Transform DataFrame to list of MatchOptimization-compatible dictionaries
            df_results = df_results.to_dict(orient="records")

        return OptimizationResponse(
            status="success",
            datetime_optim=dt_opt,
            optim_label=body.optim_label,
            matches=df_results,
        )
    except Exception as e:
        logger.exception("Optimization failed")
        raise HTTPException(status_code=500, detail=str(e)) from e