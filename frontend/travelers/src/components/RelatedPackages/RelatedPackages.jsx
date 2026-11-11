import { useMemo } from 'react';

import PackageCard from '../PackageCard/PackageCard';
import { PackageCardSkeleton } from '../Skeleton/Skeleton';
import usePackageCatalog from '../../hooks/usePackageCatalog';
import { relatedPackages } from '../../utils/packageSearch';

import './RelatedPackages.css';

/**
 * "También te puede gustar": paquetes parecidos al que se está viendo
 * (mismo tipo de experiencia, misma región o precio parecido).
 */
function RelatedPackages({ current }) {
  const { packages, loading } = usePackageCatalog();

  const related = useMemo(() => {
    const self = packages.find((item) => item.id_paquete_turistico === current.id_paquete_turistico);
    return relatedPackages(self || current, packages);
  }, [packages, current]);

  if (!loading && related.length === 0) return null;

  return (
    <section className="related" aria-labelledby="related-title">
      <p className="eyebrow">Sigue explorando</p>
      <h2 id="related-title">También te puede gustar</h2>
      <div className="related-grid">
        {loading
          ? Array.from({ length: 3 }, (_, index) => <PackageCardSkeleton key={index} />)
          : related.map((item) => <PackageCard key={item.id_paquete_turistico} touristPackage={item} />)}
      </div>
    </section>
  );
}

export default RelatedPackages;
