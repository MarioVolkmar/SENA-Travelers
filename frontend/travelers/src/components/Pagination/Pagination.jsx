import { useEffect, useMemo, useState } from 'react';

import Icon from '../Icon/Icon';
import Select from '../Select/Select';
import './Pagination.css';
// Usa clases de la consola (admin-*); se importa aquí porque la consola se carga aparte
import '../../pages/Admin/AdminDashboard.css';

const SIZES = [10, 25, 50];

/**
 * Pagina una lista ya cargada. Vuelve a la primera página cuando cambian los filtros.
 *   const pager = usePagination(visible, [query, filter]);
 *   pager.items → filas de la página actual; <Pagination {...pager} />
 */
// eslint-disable-next-line react-refresh/only-export-components
export function usePagination(items, resetKeys = [], initialSize = 10) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialSize);
  const total = items.length;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const current = Math.min(page, pages);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => setPage(1), resetKeys);

  const pageItems = useMemo(
    () => items.slice((current - 1) * pageSize, current * pageSize),
    [items, current, pageSize]
  );

  return {
    items: pageItems,
    page: current,
    pages,
    total,
    pageSize,
    setPage,
    setPageSize: (size) => {
      setPageSize(size);
      setPage(1);
    },
  };
}

function pageList(current, pages) {
  if (pages <= 7) return Array.from({ length: pages }, (_, index) => index + 1);
  const list = new Set([1, pages, current, current - 1, current + 1]);
  if (current <= 3) [2, 3, 4].forEach((n) => list.add(n));
  if (current >= pages - 2) [pages - 1, pages - 2, pages - 3].forEach((n) => list.add(n));
  const sorted = [...list].filter((n) => n >= 1 && n <= pages).sort((a, b) => a - b);
  const result = [];
  sorted.forEach((n, index) => {
    if (index > 0 && n - sorted[index - 1] > 1) result.push(`gap-${n}`);
    result.push(n);
  });
  return result;
}

function Pagination({ page, pages, total, pageSize, setPage, setPageSize, label = 'registros' }) {
  if (total === 0) return null;
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <nav className="pagination" aria-label="Paginación">
      <p className="pagination-info">
        {from}–{to} de {total} {label}
      </p>

      {pages > 1 && (
        <div className="pagination-pages">
          <button
            type="button"
            className="pagination-button"
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
            aria-label="Página anterior"
          >
            <Icon name="chevronLeft" size={16} strokeWidth={2.4} />
          </button>
          {pageList(page, pages).map((item) => (
            typeof item === 'string'
              ? <span key={item} className="pagination-gap" aria-hidden="true">…</span>
              : (
                <button
                  key={item}
                  type="button"
                  className={`pagination-button ${item === page ? 'is-current' : ''}`}
                  aria-current={item === page ? 'page' : undefined}
                  onClick={() => setPage(item)}
                >
                  {item}
                </button>
              )
          ))}
          <button
            type="button"
            className="pagination-button"
            onClick={() => setPage(page + 1)}
            disabled={page === pages}
            aria-label="Página siguiente"
          >
            <Icon name="chevronRight" size={16} strokeWidth={2.4} />
          </button>
        </div>
      )}

      <label className="pagination-size">
        <span>Por página</span>
        <Select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))} className="admin-select">
          {SIZES.map((size) => <option key={size} value={size}>{size}</option>)}
        </Select>
      </label>
    </nav>
  );
}

export default Pagination;

/**
 * Envuelve una tabla y la pagina: <Paged items={visible}>{(rows) => <table>…rows.map…</table>}</Paged>
 * Vuelve a la página 1 cuando cambia la cantidad de filas (p. ej. al filtrar).
 */
export function Paged({ items, label, pageSize = 10, children }) {
  const pager = usePagination(items, [items.length], pageSize);
  return (
    <>
      {children(pager.items)}
      <Pagination {...pager} label={label} />
    </>
  );
}
