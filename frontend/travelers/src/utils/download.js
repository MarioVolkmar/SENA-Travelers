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
