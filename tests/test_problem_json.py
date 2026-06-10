# tests del builder de errores RFC 7807 (problem+json)
import json

from app.core.exceptions import MEDIA_TYPE, _problem


def test_problem_tiene_campos_rfc7807():
    resp = _problem(status_code=404, detail="Pedido 42 no encontrado", instance="/x")
    assert resp.media_type == MEDIA_TYPE
    body = json.loads(resp.body)
    assert body["status"] == 404
    assert body["title"] == "Not Found"
    assert body["detail"] == "Pedido 42 no encontrado"
    assert body["instance"] == "/x"
    assert body["type"].endswith("not-found")


def test_problem_conserva_detail_para_compat():
    resp = _problem(status_code=409, detail="conflicto", instance="/y")
    body = json.loads(resp.body)
    # el front viejo lee .detail: debe seguir presente
    assert "detail" in body


def test_problem_extra_se_mergea():
    resp = _problem(
        status_code=422,
        detail="invalido",
        instance="/z",
        extra={"errors": [{"campo": "email", "mensaje": "requerido"}]},
    )
    body = json.loads(resp.body)
    assert body["errors"][0]["campo"] == "email"
