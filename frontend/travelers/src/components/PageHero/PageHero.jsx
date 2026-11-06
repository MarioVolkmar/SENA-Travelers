import './PageHero.css';

/**
 * Encabezado de página con foto, en el mismo estilo del slider del inicio:
 * etiqueta con línea de acento, título condensado y texto corto.
 */
function PageHero({ image, eyebrow, title, children }) {
  return (
    <header className="page-hero">
      {image && <img src={image} alt="" className="page-hero-image" />}
      <div className="page-hero-shade" />

      <div className="page-hero-content">
        {eyebrow && <p className="page-hero-eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {children && <div className="page-hero-text">{children}</div>}
      </div>
    </header>
  );
}

export default PageHero;
