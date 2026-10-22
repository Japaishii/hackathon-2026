from pathlib import Path
from contextlib import asynccontextmanager
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import database
from app.schemas import Animal, AnimalCreate, Assessment, AssessmentCreate, FollowUpUpdate
from app.specialist.engine import infer, load_knowledge_base


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
RULES = load_knowledge_base(KNOWLEDGE / "rules.json")
QUESTIONS = json.loads((KNOWLEDGE / "questions.json").read_text(encoding="utf-8"))
question_by_id = {q["id"]: q for q in QUESTIONS["questions"]}

@asynccontextmanager
async def lifespan(app: FastAPI):
    database.initialize()
    yield


app = FastAPI(title="BoviHealth", version="1.1.1", description="Anamnese e triagem explicável com regras determinísticas locais.", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return (ROOT / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/api/questions")
def get_questions() -> dict:
    return QUESTIONS


@app.get("/api/rules")
def get_rules() -> dict:
    return {"version": RULES["version"], "priority_order": RULES["priority_order"], "rules": RULES["rules"], "sources": RULES["sources"]}


@app.get("/api/animals", response_model=list[Animal])
def get_animals():
    return database.list_animals()


@app.post("/api/animals", response_model=Animal, status_code=201)
def post_animal(payload: AnimalCreate):
    if payload.productive_state == "dry" and payload.days_in_milk is not None:
        raise HTTPException(422, "Animal no período seco não deve ter dias em lactação ativos.")
    if payload.transition_stage == "prepartum" and payload.productive_state == "lactating":
        raise HTTPException(422, "Informe período seco para pré-parto neste cadastro simplificado.")
    try:
        return database.create_animal(payload.model_dump())
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="Já existe um animal com esse identificador.") from exc
        raise


@app.get("/api/assessments", response_model=list[Assessment])
def get_assessments(animal_id: int | None = None):
    return database.list_assessments(animal_id)


@app.get("/api/assessments/page")
def get_assessments_page(page: int = 1, page_size: int = 5, animal_id: int | None = None):
    if page < 1 or not 1 <= page_size <= 50:
        raise HTTPException(422, "Página ou tamanho de página inválido.")
    return database.list_assessments_page(page, page_size, animal_id)


@app.delete("/api/assessments/{assessment_id}", status_code=204)
def delete_assessment(assessment_id: int):
    if not database.delete_assessment(assessment_id):
        raise HTTPException(404, "Avaliação não encontrada.")


@app.get("/api/assessments/{assessment_id}", response_model=Assessment)
def get_assessment(assessment_id: int):
    record = database.get_assessment(assessment_id)
    if not record:
        raise HTTPException(404, "Avaliação não encontrada.")
    return record


@app.post("/api/assessments", response_model=Assessment, status_code=201)
def post_assessment(payload: AssessmentCreate):
    if payload.animal_id is not None and not database.animal_exists(payload.animal_id):
        raise HTTPException(404, "Animal não encontrado.")
    unknown = set(payload.answers) - set(question_by_id)
    if unknown:
        raise HTTPException(422, f"Perguntas desconhecidas: {', '.join(sorted(unknown))}")
    for key, value in payload.answers.items():
        question = question_by_id[key]
        if value is not None and question["type"] == "boolean" and not isinstance(value, bool):
            raise HTTPException(422, f"A resposta para {key} deve ser sim, não ou desconhecido.")
        if value is not None and question["type"] == "enum" and value not in question.get("options", []):
            raise HTTPException(422, f"A resposta para {key} não corresponde a uma opção válida.")
        if value is not None and question["type"] == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise HTTPException(422, f"A resposta para {key} deve ser numérica ou desconhecida.")
            if value < 0:
                raise HTTPException(422, f"A resposta para {key} não pode ser negativa.")
            if key == "onset_hours" and value > 8760:
                raise HTTPException(422, "O tempo desde o início dos sinais deve ser de até 8760 horas.")
    result = infer(payload.answers, RULES).to_dict()
    return database.save_assessment(payload.animal_id, payload.answers, result)


@app.patch("/api/assessments/{assessment_id}/follow-up", response_model=Assessment)
def patch_follow_up(assessment_id: int, payload: FollowUpUpdate):
    record = database.update_follow_up(assessment_id, payload.follow_up)
    if not record:
        raise HTTPException(404, "Avaliação não encontrada.")
    return record


@app.get("/api/assessments/{assessment_id}/report")
def report(assessment_id: int):
    record = database.get_assessment(assessment_id)
    if not record:
        raise HTTPException(404, "Avaliação não encontrada.")
    return {"assessment": record, "questions": question_by_id, "report_note": "Registro de apoio à anamnese; não é laudo nem diagnóstico."}
