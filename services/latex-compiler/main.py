"""Sandboxed Tectonic LaTeX Compilation Microservice Internal REST API"""
import logging
from typing import Optional
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from compiler import compile_latex_source

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (latex-compiler) %(message)s"
)
logger = logging.getLogger("latex.microservice")

app = FastAPI(
    title="LaTeX Compiler Sandbox Microservice",
    description="Internal microservice for compiling LaTeX documents using Tectonic in an isolated sandbox.",
    version="1.0.0"
)


class CompileRequest(BaseModel):
    latex_source: str = Field(..., min_length=1, description="Raw LaTeX document content to compile")
    timeout_sec: Optional[int] = Field(20, ge=1, le=60, description="Subprocess timeout in seconds")


@app.get("/health", tags=["Health"])
async def health_check():
    """Internal service health check."""
    return {"status": "healthy", "service": "latex-compiler", "engine": "tectonic"}


@app.post("/compile", tags=["Compilation"])
async def compile_endpoint(request: Request):
    """
    Compile raw LaTeX into PDF bytes.
    
    Accepts:
    - application/json: { "latex_source": "...", "timeout_sec": 20 }
    - text/plain or application/x-tex: raw LaTeX body text
    
    Returns:
    - 200 OK: binary PDF bytes (application/pdf)
    - 422 Unprocessable Entity: structured compilation error with truncated log
    """
    content_type = request.headers.get("content-type", "")
    timeout_sec = 20

    if "application/json" in content_type:
        try:
            body = await request.json()
            latex_source = body.get("latex_source", "")
            timeout_sec = body.get("timeout_sec", 20)
        except Exception as exc:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "error": f"Invalid JSON payload: {str(exc)}", "log": ""}
            )
    else:
        raw_bytes = await request.body()
        latex_source = raw_bytes.decode("utf-8", errors="replace")

    if not latex_source or not latex_source.strip():
        return JSONResponse(
            status_code=422,
            content={"status": "error", "error": "LaTeX source is empty", "log": ""}
        )

    success, pdf_bytes, log_output = compile_latex_source(
        latex_source=latex_source,
        timeout_sec=timeout_sec
    )

    if not success or pdf_bytes is None:
        logger.warning("Compilation failed for submitted document")
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "error": "LaTeX compilation failed",
                "log": log_output
            }
        )


    logger.info(f"Compilation succeeded — generated PDF size: {len(pdf_bytes)} bytes")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=resume.pdf",
            "Content-Length": str(len(pdf_bytes))
        }
    )
