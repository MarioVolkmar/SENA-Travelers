import api from '../api/axiosConfig';

function filenameFrom(disposition, fallback) {
  const match = /filename="?([^";]+)"?/i.exec(disposition || '');
  return match ? match[1] : fallback;
}

async function readBlobError(error) {
  // Con responseType "blob" el mensaje de error del backend llega como Blob
  const data = error.response?.data;
  if (data instanceof Blob) {
    try {
      const parsed = JSON.parse(await data.text());
      if (parsed?.detail) return new Error(parsed.detail);
    } catch {
      // no era JSON
    }
  }
  return error;
}

/** Descarga un archivo del backend (con el token de la sesión) y lo guarda en el equipo. */
export async function downloadFile(path, fallbackName, params) {
  let response;
  try {
    response = await api.get(path, { params, responseType: 'blob' });
  } catch (error) {
    throw await readBlobError(error);
  }

  const url = URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = filenameFrom(response.headers['content-disposition'], fallbackName);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/**
 * Abre un archivo del backend (por ejemplo un PDF) en una pestaña nueva para verlo.
 * La pestaña se abre antes de pedir el archivo para que el navegador no la bloquee.
 */
export async function openFile(path, params) {
  const tab = window.open('', '_blank');
  if (tab) {
    tab.document.title = 'Cargando...';
    tab.document.body.style.cssText = 'margin:0;display:grid;place-items:center;height:100vh;background:#0b1520;color:#c9d1db;font-family:system-ui,sans-serif';
    tab.document.body.textContent = 'Generando el PDF...';
  }

  let response;
  try {
    response = await api.get(path, { params, responseType: 'blob' });
  } catch (error) {
    tab?.close();
    throw await readBlobError(error);
  }

  const url = URL.createObjectURL(response.data);
  if (tab) {
    tab.location.href = url;
  } else {
    window.location.href = url; // si el navegador bloqueó la pestaña
  }
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
