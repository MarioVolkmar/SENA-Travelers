from test_reservations import (
    create_client_with_token,
    create_package_ready_for_reservation,
)


CLOUDFRONT_TEST_URL = "https://cdn.travelers.test"


def add_image(client, token, package_id, s3_key, es_portada=False, orden=0):
    return client.post(
        f"/packages/{package_id}/images",
        json={"s3_key": s3_key, "es_portada": es_portada, "orden": orden},
        headers={"Authorization": f"Bearer {token}"}
    )


def test_admin_can_register_image_and_get_cloudfront_url(client, db_session, monkeypatch):
    monkeypatch.setenv("CLOUDFRONT_URL", CLOUDFRONT_TEST_URL + "/")
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]

    response = add_image(client, admin_token, package_id, f"{package_id}/portada mar.jpg", es_portada=True)

    assert response.status_code == 201, response.json()
    data = response.json()
    assert data["es_portada"] is True
    assert data["imagen_url"] == f"{CLOUDFRONT_TEST_URL}/{package_id}/portada%20mar.jpg"


def test_cloudfront_url_without_scheme_gets_https(client, db_session, monkeypatch):
    monkeypatch.setenv("CLOUDFRONT_URL", "cdn.travelers.test")
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]

    response = add_image(client, admin_token, package_id, f"{package_id}/1.jpg")

    assert response.json()["imagen_url"] == f"https://cdn.travelers.test/{package_id}/1.jpg"


def test_image_url_is_null_without_cloudfront(client, db_session, monkeypatch):
    monkeypatch.delenv("CLOUDFRONT_URL", raising=False)
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]

    response = add_image(client, admin_token, package_id, f"{package_id}/1.jpg")

    assert response.status_code == 201, response.json()
    assert response.json()["imagen_url"] is None


def test_client_cannot_register_image(client, db_session):
    package, _ = create_package_ready_for_reservation(client, db_session)
    client_token, _ = create_client_with_token(
        client, db_session, email="cliente_img@example.com", identificacion="700700700"
    )
    package_id = package["id_paquete_turistico"]

    response = add_image(client, client_token, package_id, f"{package_id}/1.jpg")

    assert response.status_code == 403


def test_rejects_key_outside_package_folder_or_with_traversal(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]

    for bad_key in [f"{package_id + 1}/1.jpg", f"{package_id}/../x.jpg", f"{package_id}/", f"{package_id}/a.jpg?x=1"]:
        response = add_image(client, admin_token, package_id, bad_key)
        assert response.status_code == 400, bad_key


def test_rejects_duplicate_image_and_second_cover(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]

    assert add_image(client, admin_token, package_id, f"{package_id}/p.jpg", es_portada=True).status_code == 201
    assert add_image(client, admin_token, package_id, f"{package_id}/p.jpg").status_code == 400
    assert add_image(client, admin_token, package_id, f"{package_id}/q.jpg", es_portada=True).status_code == 400


def test_image_on_nonexistent_package_returns_404(client, db_session):
    _, admin_token = create_package_ready_for_reservation(client, db_session)

    assert add_image(client, admin_token, 9999, "9999/1.jpg").status_code == 404
    assert client.get("/packages/9999/images").status_code == 404


def test_list_images_puts_cover_first_then_order(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]

    add_image(client, admin_token, package_id, f"{package_id}/2.jpg", orden=2)
    add_image(client, admin_token, package_id, f"{package_id}/1.jpg", orden=1)
    add_image(client, admin_token, package_id, f"{package_id}/portada.jpg", es_portada=True, orden=5)

    response = client.get(f"/packages/{package_id}/images")

    assert response.status_code == 200
    keys = [image["s3_key"] for image in response.json()]
    assert keys == [f"{package_id}/portada.jpg", f"{package_id}/1.jpg", f"{package_id}/2.jpg"]


def test_admin_can_change_cover_and_list_covers(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    add_image(client, admin_token, package_id, f"{package_id}/a.jpg", es_portada=True)
    second = add_image(client, admin_token, package_id, f"{package_id}/b.jpg").json()

    response = client.patch(f"/packages/{package_id}/images/{second['id_imagen']}/cover", headers=headers)
    assert response.status_code == 200, response.json()

    cover = client.get(f"/packages/{package_id}/images/cover").json()
    assert cover["id_imagen"] == second["id_imagen"]

    covers = client.get("/packages/images/covers").json()
    assert [c["id_imagen"] for c in covers] == [second["id_imagen"]]


def test_admin_can_delete_image(client, db_session):
    package, admin_token = create_package_ready_for_reservation(client, db_session)
    package_id = package["id_paquete_turistico"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    image = add_image(client, admin_token, package_id, f"{package_id}/a.jpg").json()

    response = client.delete(f"/packages/{package_id}/images/{image['id_imagen']}", headers=headers)
    assert response.status_code == 204

    assert client.get(f"/packages/{package_id}/images").json() == []
    assert client.delete(f"/packages/{package_id}/images/{image['id_imagen']}", headers=headers).status_code == 404


def test_cover_is_null_when_package_has_none(client, db_session):
    package, _ = create_package_ready_for_reservation(client, db_session)

    response = client.get(f"/packages/{package['id_paquete_turistico']}/images/cover")

    assert response.status_code == 200
    assert response.json() is None
