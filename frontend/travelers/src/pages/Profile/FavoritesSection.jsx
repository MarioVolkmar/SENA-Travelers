import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import api from '../../api/axiosConfig';
import Icon from '../../components/Icon/Icon';
import PackageCard from '../../components/PackageCard/PackageCard';
import { useFavorites } from '../../context/FavoritesContext';

/** Paquetes guardados con el corazón. */
function FavoritesSection() {
  const { ids } = useFavorites();
  const [packages, setPackages] = useState(null);
  const [extras, setExtras] = useState({ covers: {}, cities: {} });

  useEffect(() => {
    Promise.all([
      api.get('/favorites/'),
      api.get('/packages/images/covers').catch(() => ({ data: [] })),
      api.get('/cities/').catch(() => ({ data: [] })),
    ])
      .then(([favorites, covers, cities]) => {
        setExtras({
          covers: Object.fromEntries(covers.data.map((cover) => [cover.paquete_id, cover.imagen_url])),
          cities: Object.fromEntries(cities.data.map((city) => [city.id_ciudad, city])),
        });
        setPackages(favorites.data);
      })
      .catch(() => setPackages([]));
  }, []);

  if (!packages) return <p className="page-status">Cargando favoritos...</p>;

  // Al quitar un corazón desaparece de la lista sin recargar
  const visible = packages.filter((item) => ids.has(item.id_paquete_turistico));

  return (
    <div className="account-panel">
      <h2>Mis favoritos</h2>
      {visible.length === 0 ? (
        <div className="account-empty">
          <Icon name="heart" size={32} />
          <p>Aún no tienes paquetes guardados. Toca el corazón de un paquete para tenerlo a mano aquí.</p>
          <Link to="/packages" className="btn btn-primary">Explorar paquetes</Link>
        </div>
      ) : (
        <div className="account-favorites">
          {visible.map((item) => (
            <PackageCard
              key={item.id_paquete_turistico}
              touristPackage={{
                ...item,
                cover: extras.covers[item.id_paquete_turistico] || null,
                city: extras.cities[item.ciudad_id] || null,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default FavoritesSection;
