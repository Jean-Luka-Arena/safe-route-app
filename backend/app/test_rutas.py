from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ---------- CASOS EXITOSOS ----------


def test_ruta_mas_corta():
    respuesta = client.get(
        "/route", params={"origin": "A", "destination": "D", "criteria": "corta"}
    )
    assert respuesta.status_code == 200
    data = respuesta.json()
    assert data["ruta"][0] == "A"
    assert data["ruta"][-1] == "D"
    assert data["distancia_total"] is not None


def test_ruta_mas_segura():
    respuesta = client.get(
        "/route", params={"origin": "A", "destination": "D", "criteria": "segura"}
    )
    assert respuesta.status_code == 200
    data = respuesta.json()
    assert data["ruta"][0] == "A"
    assert data["ruta"][-1] == "D"


def test_ruta_balanceada():
    respuesta = client.get(
        "/route",
        params={
            "origin": "A",
            "destination": "D",
            "criteria": "balanceada",
            "alpha": 0.5,
            "beta": 0.5,
        },
    )
    assert respuesta.status_code == 200
    data = respuesta.json()
    assert data["ruta"][0] == "A"
    assert data["ruta"][-1] == "D"


def test_respuesta_incluye_los_campos_esperados():
    respuesta = client.get(
        "/route", params={"origin": "A", "destination": "B", "criteria": "corta"}
    )
    data = respuesta.json()
    assert set(data.keys()) == {
        "ruta",
        "distancia_total",
        "seguridad_promedio",
        "costo_total",
    }


# ---------- ERRORES DEL CLIENTE (400) ----------


def test_criterio_invalido_devuelve_400():
    respuesta = client.get(
        "/route",
        params={"origin": "A", "destination": "B", "criteria": "mas_linda"},
    )
    assert respuesta.status_code == 400


def test_balanceada_sin_alpha_beta_devuelve_400():
    respuesta = client.get(
        "/route",
        params={"origin": "A", "destination": "B", "criteria": "balanceada"},
    )
    assert respuesta.status_code == 400


def test_falta_parametro_obligatorio_devuelve_422():
    # FastAPI valida automaticamente los Query(...) requeridos
    respuesta = client.get("/route", params={"origin": "A", "criteria": "corta"})
    assert respuesta.status_code == 422


# ---------- ERRORES DE RECURSO (404) ----------


def test_origen_inexistente_devuelve_404():
    respuesta = client.get(
        "/route", params={"origin": "Z", "destination": "A", "criteria": "corta"}
    )
    assert respuesta.status_code == 404


def test_destino_inexistente_devuelve_404():
    respuesta = client.get(
        "/route", params={"origin": "A", "destination": "Z", "criteria": "corta"}
    )
    assert respuesta.status_code == 404
