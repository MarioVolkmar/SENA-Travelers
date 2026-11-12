"""
Vista previa al compartir un paquete (etiquetas Open Graph para WhatsApp, Facebook, etc.).
"""
from app.models.tourist_package_model import TouristPackageModel

from test_reservations import create_package_ready_for_reservation


def test_share_page_has_package_preview(client, db_session, monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://travelers.test")
    package, _ = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]

    response = client.get(f"/share/packages/{package_id}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert f'<meta property="og:title" content="{package["nombre"]} · Travelers" />' in html
    assert "por persona, IVA incluido" in html
    assert f'<meta property="og:url" content="https://travelers.test/packages/{package_id}" />' in html
    # Sin portada se usa la imagen general del sitio
    assert '<meta property="og:image" content="https://travelers.test/og-image.jpg" />' in html
    # Una persona que llegue aquí sigue a la página normal del paquete
    assert f'url=https://travelers.test/packages/{package_id}' in html


def test_share_page_escapes_html_and_hides_inactive_packages(client, db_session, monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://travelers.test")
    package, _ = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]

    db_session.rollback()
    row = db_session.query(TouristPackageModel).filter(TouristPackageModel.id_paquete_turistico == package_id).one()
    row.nombre = 'Playa "<script>"'
    db_session.commit()

    html = client.get(f"/share/packages/{package_id}").text
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

    row.estado = "inactivo"
    db_session.commit()
    html = client.get(f"/share/packages/{package_id}").text
    assert "Travelers · Paquetes turísticos por Colombia" in html
    assert "Playa" not in html


def test_share_page_for_missing_package_uses_site_preview(client):
    response = client.get("/share/packages/999999")

    assert response.status_code == 200
    assert "Travelers · Paquetes turísticos por Colombia" in response.text
