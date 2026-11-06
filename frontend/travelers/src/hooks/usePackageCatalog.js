import { useEffect, useState } from 'react';

import api from '../api/axiosConfig';

/**
 * Carga los paquetes activos junto con su portada y su ciudad.
 * Con { withAvailability: true } también consulta los cupos disponibles de cada uno.
 */
export default function usePackageCatalog({ withAvailability = false } = {}) {
  const [state, setState] = useState({
    packages: [],
    cities: {},
    loading: true,
    error: '',
  });

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [packagesResponse, coversResponse, citiesResponse, ratingsResponse] = await Promise.all([
          api.get('/packages/'),
          api.get('/packages/images/covers').catch(() => ({ data: [] })),
          api.get('/cities/').catch(() => ({ data: [] })),
          api.get('/reviews/summary').catch(() => ({ data: [] })),
        ]);

        const ratings = Object.fromEntries(
          ratingsResponse.data.map((item) => [item.paquete_id, item])
        );

        const covers = Object.fromEntries(
          coversResponse.data.map((cover) => [cover.paquete_id, cover.imagen_url])
        );
        const cities = Object.fromEntries(
          citiesResponse.data.map((city) => [city.id_ciudad, city])
        );

        let availability = {};

        if (withAvailability) {
          const responses = await Promise.all(
            packagesResponse.data.map((item) =>
              api
                .get(`/reservations/availability/${item.id_paquete_turistico}`)
                .catch(() => null)
            )
          );

          availability = Object.fromEntries(
            responses
              .filter(Boolean)
              .map((response) => [response.data.id_paquete_turistico, response.data.cupos_disponibles])
          );
        }

        const packages = packagesResponse.data
          .map((item) => ({
            ...item,
            cover: covers[item.id_paquete_turistico] || null,
            city: cities[item.ciudad_id] || null,
            availableSlots: availability[item.id_paquete_turistico],
            rating: ratings[item.id_paquete_turistico] || null,
          }))
          .sort((a, b) => a.fecha_inicio.localeCompare(b.fecha_inicio));

        if (!cancelled) {
          setState({ packages, cities, loading: false, error: '' });
        }
      } catch {
        if (!cancelled) {
          setState({
            packages: [],
            cities: {},
            loading: false,
            error: 'No fue posible cargar los paquetes turísticos.',
          });
        }
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [withAvailability]);

  return state;
}
