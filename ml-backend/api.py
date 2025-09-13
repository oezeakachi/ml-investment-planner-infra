from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .goal_planner import run_plan

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
