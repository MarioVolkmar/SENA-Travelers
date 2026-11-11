import './Skeleton.css';

/** Bloque gris animado que ocupa el lugar de un contenido mientras carga. */
export function Skeleton({ width = '100%', height = 16, radius, className = '' }) {
  return (
    <span
      className={`skeleton ${className}`}
      style={{ width, height, borderRadius: radius }}
      aria-hidden="true"
    />
  );
}

/** Silueta de una tarjeta de paquete (misma proporción que PackageCard). */
export function PackageCardSkeleton({ variant = 'card' }) {
  return (
    <div className={`skeleton-card skeleton-card-${variant}`} aria-hidden="true">
      <Skeleton className="skeleton-card-media" height="auto" />
      <div className="skeleton-card-body">
        <Skeleton width="45%" height={13} />
        <Skeleton width="80%" height={22} />
        <Skeleton width="35%" height={13} />
        <Skeleton width="50%" height={20} />
      </div>
    </div>
  );
}

/** Rejilla de tarjetas en carga, con un texto oculto para lectores de pantalla. */
export function PackageGridSkeleton({ count = 6, variant = 'card', className }) {
  return (
    <div className={className} role="status" aria-live="polite">
      <span className="visually-hidden">Cargando paquetes...</span>
      {Array.from({ length: count }, (_, index) => (
        <PackageCardSkeleton key={index} variant={variant} />
      ))}
    </div>
  );
}

/** Silueta genérica de página: título, párrafo y bloques (mientras llega el código de la pantalla). */
export function PageSkeleton() {
  return (
    <div className="page skeleton-page" role="status" aria-live="polite">
      <span className="visually-hidden">Cargando...</span>
      <Skeleton width="30%" height={14} />
      <Skeleton width="55%" height={40} radius={12} />
      <Skeleton width="70%" height={16} />
      <div className="skeleton-page-blocks">
        <Skeleton height={180} radius={24} />
        <Skeleton height={180} radius={24} />
        <Skeleton height={180} radius={24} />
      </div>
    </div>
  );
}
