from fastapi import FastAPI

app = FastAPI(title="geeknews-summary")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
