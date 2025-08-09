from .routes.teams import router as teams_router
app.include_router(teams_router)
from .routes.views import router as views_router
app.include_router(views_router)
from .routes.tags import router as tags_router
app.include_router(tags_router)
from .routes.packs import router as packs_router
from .routes.tenants import router as tenants_router
from fastapi import FastAPI
from .routes.determinism import router as det_router
from .routes.audit import router as audit_router
from .routes.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pathlib import Path
import hashlib
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .routes.runs import router as runs_router
from .routes.reports import router as reports_router
from .routes.harden import router as harden_router

app = FastAPI(title="AAH API", version="0.4.0")
app.include_router(det_router)
app.include_router(audit_router)
app.include_router(auth_router)
configure_logging()  # JSON logs from now on

from .routes.badge import router as badge_router
from .routes.broadcast import router as broadcast_router
from .routes.compare import router as compare_router
from .utils.logging import configure_logging
from .routes.incidents import router as incidents_router
from .routes.tenant import router as tenant_router
from .routes.embed import router as embed_router
from .routes.release_notes import router as relnotes_router


# Import verify and evidence routers
from .routes.verify import router as verify_router
from .routes.evidence import router as evidence_router

app = FastAPI(title="AAH API", version="0.4.0")
configure_logging()  # JSON logs from now on

app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:3000"],
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TRUTH_POLICY_PATH = REPO_ROOT / "Truth_policy.md"
SPEC_SCHEMA_PATH = REPO_ROOT / "specs/schemas/test_spec.schema.json"

def sha256_of(p: Path) -> str:
	h = hashlib.sha256()
	with p.open("rb") as f:
		for chunk in iter(lambda: f.read(8192), b""):
			h.update(chunk)
	return h.hexdigest()

POLICY_HASH = sha256_of(TRUTH_POLICY_PATH)
SPEC_SCHEMA_HASH = sha256_of(SPEC_SCHEMA_PATH)


@app.get("/health")
def health():
	return {
		"status": "ok",
		"truth_policy_hash": POLICY_HASH,
		"spec_schema_hash": SPEC_SCHEMA_HASH,
		"service": "aah-api"
	}

@app.get("/")
def root():
	return {"message": "AAH API up. See /health."}


@app.get("/metrics")
def metrics():
	data = generate_latest()
	return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# Register routers
app.include_router(packs_router)
app.include_router(tenants_router)
app.include_router(runs_router)
app.include_router(reports_router)
app.include_router(harden_router)
app.include_router(badge_router)
app.include_router(broadcast_router)
app.include_router(compare_router)
app.include_router(verify_router)
app.include_router(evidence_router)
app.include_router(tenant_router)
app.include_router(embed_router)
app.include_router(relnotes_router)
app.include_router(incidents_router)
