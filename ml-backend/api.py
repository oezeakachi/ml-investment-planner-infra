from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from goal_planner import run_plan

app = FastAPI()

allowed_origin = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    goal: float
    years: int
    risk: str
    start_capital: float
    monthly_contrib: float

@app.post("/plan")
def plan(req: PlanRequest):
    return run_plan(req.goal, req.years, req.risk, req.start_capital, req.monthly_contrib)
