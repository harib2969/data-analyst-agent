from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import importlib.util
import os
import sys

app = FastAPI()

def dynamic_import(module_path: str, func_name: str = "analyze"):
    """Dynamically import `analyze` function from a Python file"""
    spec = importlib.util.spec_from_file_location("dynamic_module", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["dynamic_module"] = module
    spec.loader.exec_module(module)
    return getattr(module, func_name)

@app.post("/api/")
async def pipeline(request: Request):
    """
    Generic pipeline:
    - Accepts any request
    - Loads dataset and question info
    - Delegates actual analysis to run.py (or whichever script you configure)
    - Returns exactly what that script outputs
    """
    payload = await request.json()

    # choose the script dynamically (default: run.py in current dir)
    script_path = os.getenv("ANALYZER_PATH", "run.py")
    analyze = dynamic_import(script_path, "analyze")

    # call the analyzer with full payload
    result = analyze(payload)

    # must be JSON serializable
    return JSONResponse(content=result)
