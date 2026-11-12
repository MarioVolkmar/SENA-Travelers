"""Desglose del IVA (19 %, incluido en los precios)."""
from decimal import Decimal

from app.core.taxes import split_iva

from test_reservations import (
    create_client_with_token,
    create_package_ready_for_reservation,
    create_reservation,
)


def test_split_iva_always_adds_up_to_the_total():
    assert split_iva("1190000") == (Decimal("1000000.00"), Decimal("190000.00"))
    for total in ["460000", "650000", "1300000", "1", "99999999.99"]:
        base, iva = split_iva(total)
        assert base + iva == Decimal(total)
        assert iva >= 0


def test_reservation_and_payment_show_the_iva_breakdown(client, db_session):
    package, _ = create_package_ready_for_reservation(client, db_session)
    token, _ = create_client_with_token(client, db_session, email="iva@example.com", identificacion="990990990")
    headers = {"Authorization": f"Bearer {token}"}

    reservation = create_reservation(client, token, package_id=package["id_paquete_turistico"]).json()

    total = Decimal(reservation["total_reserva"])
    assert reservation["iva_porcentaje"] == 19
    assert Decimal(reservation["subtotal_sin_iva"]) + Decimal(reservation["iva"]) == total
    assert Decimal(reservation["iva"]) == split_iva(total)[1]

    payment = client.post(
        "/payments/",
        json={"reserva_id": reservation["id_reserva"], "metodo_pago": "Nequi", "valor": reservation["total_reserva"]},
        headers=headers,
    ).json()
    assert Decimal(payment["valor_sin_iva"]) + Decimal(payment["iva"]) == Decimal(payment["valor"])

    voucher = client.get(f"/vouchers/{reservation['id_reserva']}", headers=headers)
    assert voucher.status_code == 200 and voucher.content.startswith(b"%PDF")
