"""
Carga el catálogo de productos turísticos y los asocia a los 10 paquetes.

Uso (desde la carpeta backend):
    venv\\Scripts\\python -m scripts.seed_productos            # aplica los cambios
    venv\\Scripts\\python -m scripts.seed_productos --dry-run  # solo muestra qué haría

Es idempotente: si un producto (mismo nombre y proveedor) o un vínculo
paquete-producto ya existe, no lo vuelve a crear. Los costos son por persona
(en hospedaje y alimentación, por noche o por día; "cantidad" indica cuántas
noches/días incluye el paquete).
"""
import sys
from decimal import Decimal

from app.core.constants import PRODUCT_STATUS_ACTIVE, PROVIDER_STATUS_APPROVED
from app.database.connection import SessionLocal, engine
from app.models.product_model import ProductModel
from app.models.provider_model import ProviderModel
from app.models.tourist_package_model import TouristPackageModel
from app.models.tourist_package_product_model import TouristPackageProductModel

# Quién presta cada tipo de servicio (empresa del proveedor aprobado)
PROVIDER_BY_TYPE = {
    "hospedaje": "Marito",
    "alimentacion": "Marito",
    "transporte": "Antonio",
    "tour": "Antonio",
    "actividad": "Antonio",
    "entrada": "Antonio",
}

# Unidad de cobro según el tipo (el resto se cobra por persona)
UNIT_BY_TYPE = {
    "hospedaje": "noche",
    "alimentacion": "dia",
}

# paquete → [(nombre, tipo, costo por persona, cantidad, descripción)]
CATALOG = {
    "Cartagena entre murallas y mar": [
        ("Hotel boutique en el Centro Histórico de Cartagena", "hospedaje", 180000, 3,
         "Habitación doble con aire acondicionado dentro de la Ciudad Amurallada, a pasos de las plazas principales. Precio por persona por noche."),
        ("Desayuno buffet en Cartagena", "alimentacion", 25000, 3,
         "Desayuno buffet con frutas tropicales, arepa de huevo, café y jugos naturales, servido en el hotel."),
        ("Recorrido guiado por la Ciudad Amurallada", "tour", 60000, 1,
         "Caminata de 3 horas con guía local por las murallas, el Castillo de San Felipe (exterior) y el barrio Getsemaní."),
        ("Excursión en lancha a las Islas del Rosario", "tour", 220000, 1,
         "Día completo en lancha desde el muelle de La Bodeguita, con parada en playa, snorkel básico y almuerzo típico."),
    ],
    "Eje Cafetero: aroma y naturaleza": [
        ("Finca hotel cafetera en Salento", "hospedaje", 150000, 2,
         "Alojamiento rural en finca tradicional con vista a las montañas del Quindío. Precio por persona por noche."),
        ("Desayuno campesino en Salento", "alimentacion", 20000, 2,
         "Calentado, arepa, huevos al gusto y café de origen de la finca."),
        ("Tour del café en finca cafetera", "tour", 70000, 1,
         "Recorrido por los cultivos, proceso del grano desde la cosecha hasta la taza y cata guiada."),
        ("Transporte en Willys al Valle del Cocora", "transporte", 30000, 1,
         "Traslado ida y regreso desde la plaza de Salento en el tradicional jeep Willys."),
        ("Caminata por el Valle del Cocora", "actividad", 50000, 1,
         "Caminata guiada de 4 a 5 horas entre las palmas de cera, árbol nacional de Colombia. Incluye entrada a la reserva."),
    ],
    "Santa Marta y Tayrona": [
        ("Hotel en el centro de Santa Marta", "hospedaje", 170000, 3,
         "Hotel con piscina a pocas cuadras de la bahía y el camellón. Precio por persona por noche."),
        ("Desayuno en Santa Marta", "alimentacion", 22000, 3,
         "Desayuno costeño con arepa, queso, huevos, frutas y café."),
        ("Recorrido por el centro histórico de Santa Marta", "tour", 45000, 1,
         "Visita guiada a la Catedral, el Parque de los Novios y la Quinta de San Pedro Alejandrino (exterior)."),
        ("Transporte Santa Marta - Parque Tayrona", "transporte", 60000, 1,
         "Traslado ida y regreso en van hasta la entrada El Zaino del Parque Nacional Natural Tayrona."),
        ("Entrada al Parque Nacional Natural Tayrona", "entrada", 75000, 1,
         "Ingreso al parque para un día. Sujeto a la apertura del parque por parte de Parques Nacionales."),
    ],
    "Medellín y Guatapé": [
        ("Hotel en El Poblado, Medellín", "hospedaje", 160000, 2,
         "Hotel en la zona de El Poblado, cerca de restaurantes y del metro. Precio por persona por noche."),
        ("Desayuno en Medellín", "alimentacion", 20000, 2,
         "Desayuno paisa con arepa, huevos pericos, chocolate o café."),
        ("City tour por Medellín y la Comuna 13", "tour", 60000, 1,
         "Recorrido en metro y metrocable por el centro, Plaza Botero y los grafitis de la Comuna 13 con guía local."),
        ("Transporte Medellín - Guatapé", "transporte", 70000, 1,
         "Traslado ida y regreso en bus turístico hasta Guatapé y El Peñol."),
        ("Recorrido por el pueblo de Guatapé", "tour", 45000, 1,
         "Caminata guiada por los zócalos de colores y el malecón del embalse. No incluye la subida a la Piedra del Peñol."),
    ],
    "San Andrés: colores del Caribe": [
        ("Hotel frente al mar en San Andrés", "hospedaje", 230000, 4,
         "Hotel sobre la playa de Spratt Bight con vista al mar de siete colores. Precio por persona por noche."),
        ("Desayuno isleño en San Andrés", "alimentacion", 25000, 4,
         "Desayuno con frutas, pan de coco, huevos y café."),
        ("Vuelta a la isla en chiva", "tour", 60000, 1,
         "Recorrido de medio día por San Luis, el Hoyo Soplador, la Piscinita y West View."),
        ("Paseo en lancha a Johnny Cay y el Acuario", "actividad", 120000, 1,
         "Lancha ida y regreso a los cayos con tiempo libre para nadar y hacer snorkel con mantarrayas."),
    ],
    "Jardín entre montañas": [
        ("Hostal colonial en Jardín", "hospedaje", 140000, 1,
         "Casa colonial de balcones de colores a una cuadra del parque principal. Precio por persona por noche."),
        ("Desayuno típico antioqueño", "alimentacion", 18000, 1,
         "Arepa, quesito, huevos, chocolate caliente y pan de bono."),
        ("Recorrido por el pueblo de Jardín", "tour", 35000, 1,
         "Caminata guiada por la Basílica, el parque principal y el teleférico (tiquete no incluido)."),
        ("Visita a finca cafetera en Jardín", "tour", 60000, 1,
         "Recorrido por una finca familiar con explicación del proceso del café y degustación."),
    ],
    "Bogotá histórica y cultural": [
        ("Hotel en La Candelaria, Bogotá", "hospedaje", 170000, 2,
         "Hotel en casa republicana restaurada en el centro histórico. Precio por persona por noche."),
        ("Desayuno santafereño", "alimentacion", 20000, 2,
         "Changua o huevos, almojábana, chocolate santafereño con queso."),
        ("Recorrido guiado por La Candelaria", "tour", 50000, 1,
         "Caminata por la Plaza de Bolívar, el Chorro de Quevedo y el exterior del Museo del Oro y el Museo Botero."),
        ("Tiquete de ascenso y descenso a Monserrate", "entrada", 35000, 1,
         "Ida y regreso en funicular o teleférico al santuario de Monserrate."),
    ],
    "Santander: aventura en San Gil": [
        ("Hotel en San Gil", "hospedaje", 140000, 2,
         "Hotel con piscina cerca del Parque El Gallineral. Precio por persona por noche."),
        ("Desayuno santandereano", "alimentacion", 18000, 2,
         "Arepa santandereana, huevos, fruta y café."),
        ("Rafting en el río Fonce", "actividad", 90000, 1,
         "Descenso de rápidos de nivel II-III con operador certificado, guía, chaleco, casco y transporte al punto de salida."),
        ("Transporte San Gil - Barichara", "transporte", 40000, 1,
         "Traslado ida y regreso hasta Barichara."),
        ("Recorrido por Barichara", "tour", 35000, 1,
         "Caminata guiada por el pueblo más bonito de Colombia y el inicio del Camino Real a Guane."),
    ],
    "Amazonas: naturaleza y cultura": [
        ("Ecohotel en Leticia", "hospedaje", 200000, 3,
         "Alojamiento en ecohotel rodeado de selva, con ventilador y mosquitero. Precio por persona por noche."),
        ("Alimentación completa en el Amazonas", "alimentacion", 90000, 3,
         "Desayuno, almuerzo y cena por día con pescado de río y frutas amazónicas."),
        ("Recorrido fluvial por el río Amazonas", "tour", 180000, 1,
         "Día en bote por el río, Isla de los Micos, avistamiento de delfines rosados y Puerto Nariño."),
        ("Visita cultural a comunidad indígena", "tour", 90000, 1,
         "Encuentro guiado con una comunidad ticuna: tradiciones, artesanías y medicina ancestral."),
    ],
    "Villa de Leyva y encanto colonial": [
        ("Hotel colonial en Villa de Leyva", "hospedaje", 150000, 2,
         "Hotel en casona colonial a dos cuadras de la Plaza Mayor. Precio por persona por noche."),
        ("Desayuno boyacense", "alimentacion", 20000, 2,
         "Huevos, arepa boyacense, queso campesino y agua de panela."),
        ("Recorrido histórico por Villa de Leyva", "tour", 40000, 1,
         "Caminata por la Plaza Mayor, la Casa de Nariño y el Museo del Carmen (exterior)."),
        ("Transporte Villa de Leyva - Ráquira", "transporte", 35000, 1,
         "Traslado ida y regreso hasta Ráquira, capital artesanal de Colombia."),
        ("Recorrido artesanal por Ráquira", "tour", 30000, 1,
         "Visita a talleres de cerámica y alfarería con demostración del oficio."),
    ],
}


def main(dry_run: bool):
    engine.echo = False
    db = SessionLocal()

    try:
        providers = {
            provider.nombre_empresa: provider
            for provider in db.query(ProviderModel)
            .filter(ProviderModel.estado_verificacion == PROVIDER_STATUS_APPROVED)
            .all()
        }

        missing = set(PROVIDER_BY_TYPE.values()) - set(providers)
        if missing:
            sys.exit(f"Faltan proveedores aprobados: {', '.join(sorted(missing))}")

        created_products = created_links = 0

        for package_name, items in CATALOG.items():
            package = db.query(TouristPackageModel).filter(TouristPackageModel.nombre == package_name).first()

            if package is None:
                print(f"! Paquete no encontrado, se omite: {package_name}")
                continue

            for nombre, tipo, costo, cantidad, descripcion in items:
                provider = providers[PROVIDER_BY_TYPE[tipo]]

                product = (
                    db.query(ProductModel)
                    .filter(ProductModel.nombre == nombre, ProductModel.proveedor_id == provider.id_proveedor)
                    .first()
                )

                if product is None:
                    product = ProductModel(
                        nombre=nombre,
                        descripcion=descripcion,
                        tipo_producto=tipo,
                        costo=Decimal(costo),
                        unidad_cobro=UNIT_BY_TYPE.get(tipo, "persona"),
                        ciudad_id=package.ciudades_id_ciudad,
                        proveedor_id=provider.id_proveedor,
                        estado=PRODUCT_STATUS_ACTIVE,
                    )
                    db.add(product)
                    db.flush()
                    created_products += 1

                link = (
                    db.query(TouristPackageProductModel)
                    .filter(
                        TouristPackageProductModel.paquetes_turisticos_id_paquete_turistico == package.id_paquete_turistico,
                        TouristPackageProductModel.productos_id_producto == product.id_producto,
                    )
                    .first()
                )

                if link is None:
                    db.add(TouristPackageProductModel(
                        paquetes_turisticos_id_paquete_turistico=package.id_paquete_turistico,
                        productos_id_producto=product.id_producto,
                        cantidad=cantidad,
                    ))
                    created_links += 1

        if dry_run:
            db.rollback()
            print(f"[simulación] Se crearían {created_products} productos y {created_links} vínculos con paquetes.")
        else:
            db.commit()
            print(f"Listo: {created_products} productos creados y {created_links} vínculos con paquetes.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
