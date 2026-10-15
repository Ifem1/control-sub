"""Deterministic, simulated security configurations for offline + Direct Mode."""
import hashlib
import json

OWNER = "0x" + "11" * 20
BOB = "0x" + "22" * 20
ROUTE = "https://raw.githubusercontent.com/example-org/controls/" + "a" * 40 + "/"
SOURCES = [
    b"service_gateway:\n  auth: hardware-bound key\n  authorization: separate admin approval\n  deny_unsigned: true\n  audit: append-only\n",
    b"review_pipeline:\n  approvals: two independent reviewers\n  require_review_before_activation: true\n  bypass_paths: none\n",
]

DIMENSIONS = [
    {"id":"STRONG_AUTH", "objective":"Every administrator authenticates using a hardware-bound credential and no password-only bypass exists.",
     "failure_mode":"Password-only login or unattended administrative credential is possible."},
    {"id":"INDEPENDENT_APPROVAL", "objective":"A distinct authorized reviewer must approve each privileged deployment before activation.",
     "failure_mode":"One actor can deploy an unreviewed change or waive review alone."},
]


def charter():
    return {
        "title": "Privileged access alternatives",
        "context": "Administrative deployment access to production configuration, not ordinary read-only support access.",
        "baseline": "The existing mechanism requires hardware-rooted operator authentication and independent pre-activation approval. No unilateral bypass is allowed.",
        "dimensions_json": json.dumps(DIMENSIONS),
        "allowed_repos_json": json.dumps(["example-org/controls"]),
        "certificate_lifetime_days": 14,
    }


def controls():
    return json.dumps([
        {"id": "GATEWAY", "mechanism": "Gateway code enforces hardware-rooted authentication with no fallback.",
         "source_url": ROUTE+"gateway.yml", "source_sha256": hashlib.sha256(SOURCES[0]).hexdigest()},
        {"id": "REVIEW", "mechanism": "Pipeline rejects activation without two independent signoffs.",
         "source_url": ROUTE+"review.yml", "source_sha256": hashlib.sha256(SOURCES[1]).hexdigest()},
    ])


def passing():
    return {"dimensions":[
        {"id":"STRONG_AUTH","state":"COVERED","supports":[0]},
        {"id":"INDEPENDENT_APPROVAL","state":"COVERED","supports":[1]},
    ], "no_new_material_weakening":"YES", "reason_code":"ALL_COVERED"}


def missing():
    return {"dimensions":[
        {"id":"STRONG_AUTH","state":"COVERED","supports":[0]},
        {"id":"INDEPENDENT_APPROVAL","state":"GAP","supports":[]},
    ], "no_new_material_weakening":"NO", "reason_code":"MISSING_CONTROL"}


def ambiguous():
    return {"dimensions":[
        {"id":"STRONG_AUTH","state":"COVERED","supports":[0]},
        {"id":"INDEPENDENT_APPROVAL","state":"UNKNOWN","supports":[]},
    ], "no_new_material_weakening":"UNKNOWN", "reason_code":"INSUFFICIENT_INFORMATION"}
