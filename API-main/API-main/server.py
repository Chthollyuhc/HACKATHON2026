import json
import pandas as pd
import xgboost as xgb
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from chatbot import chat, PROMPTS

app = FastAPI()

MODEL_PATH = "xgboost.json"
FEATURES = ["age", "job", "marital", "education", "balance", "housing", "loan", "contact", "day", "month", "campaign", "pdays", "previous", "poutcome"]
CAT_COLS = ["job", "marital", "education", "housing", "loan", "contact", "month", "poutcome"]

model = xgb.XGBClassifier(enable_categorical=True)
model.load_model(MODEL_PATH)


def _row_to_df(info: dict) -> pd.DataFrame:
    row = {k: info.get(k, "unknown" if k in CAT_COLS else 0) for k in FEATURES}
    df = pd.DataFrame([row])
    for col in CAT_COLS:
        df[col] = df[col].astype(str).astype("category")
    return df


class ChatRequest(BaseModel):
    message: str
    provider: str = "gemma"
    prompt_key: str


class CreateMailRequest(BaseModel):
    info: dict
    tier: int
    provider: str = "gemma"


class RemindRequest(BaseModel):
    info: dict | str
    provider: str = "gemma"


class SuggestNextActionRequest(BaseModel):
    summary: str
    info: dict
    tier: int
    provider: str = "gemma"


class ScoreRequest(BaseModel):
    info: dict


@app.post("/create_mail")
def api_create_mail(req: CreateMailRequest):
    if not 1 <= req.tier <= 5:
        return JSONResponse({"error": "Tier must be between 1 and 5"}, 400)

    prompt = (
        f"Thông tin khách hàng:\n{json.dumps(req.info, ensure_ascii=False, indent=2)}\n\n"
        f"Phân hạng: Tier {req.tier}/5\n\n"
        f"Hãy viết email marketing được cá nhân hóa cho khách hàng này."
    )
    raw = chat(req.provider, "email_marketing", prompt)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"title": "", "content": raw, "_warning": "Model did not return valid JSON, content is raw"}


@app.post("/remind")
def api_remind(req: RemindRequest):
    tasks_text = json.dumps(req.info, ensure_ascii=False) if isinstance(req.info, dict) else req.info

    prompt = (
        f"Danh sách công việc cần ưu tiên:\n{tasks_text}\n\n"
        f"Hãy sắp xếp theo thứ tự ưu tiên và trả về JSON."
    )
    raw = chat(req.provider, "task_prioritizer", prompt)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw, "_error": "Model did not return valid JSON"}


@app.post("/suggest_next_action")
def api_suggest_next_action(req: SuggestNextActionRequest):
    if not 1 <= req.tier <= 5:
        return JSONResponse({"error": "Tier must be between 1 and 5"}, 400)

    prompt = (
        f"Tóm tắt cuộc gọi:\n{req.summary}\n\n"
        f"Thông tin khách hàng:\n{json.dumps(req.info, ensure_ascii=False, indent=2)}\n\n"
        f"Phân hạng: Tier {req.tier}/5\n\n"
        f"Hãy phân tích và đưa ra lời khuyên về hành động tiếp theo."
    )
    advice = chat(req.provider, "next_action", prompt)
    return {"advice": advice}


@app.post("/score")
def api_score(req: ScoreRequest):
    missing = [k for k in FEATURES if k not in req.info]
    if missing:
        return JSONResponse({
            "error": "Missing required columns",
            "missing": missing,
            "required": FEATURES,
        }, 400)

    df = _row_to_df(req.info)
    proba = float(model.predict_proba(df)[:, 1][0])
    return {"score": proba}


