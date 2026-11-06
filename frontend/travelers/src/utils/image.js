export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();

    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('No se pudo leer la imagen'));
    };

    image.src = url;
  });
}

/**
 * Reduce una foto para que su lado más largo mida como máximo `maxSide` px
 * (sin recortar). Sirve para que las fotos de los paquetes carguen rápido.
 */
export async function resizeToJpeg(file, maxSide = 1600, quality = 0.82) {
  if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    throw new Error(`"${file.name}" no es una imagen JPG, PNG o WEBP.`);
  }

  const image = await loadImage(file);
  const scale = Math.min(1, maxSide / Math.max(image.naturalWidth, image.naturalHeight));
  const width = Math.round(image.naturalWidth * scale);
  const height = Math.round(image.naturalHeight * scale);

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;

  const context = canvas.getContext('2d');
  context.fillStyle = '#ffffff';
  context.fillRect(0, 0, width, height);
  context.imageSmoothingQuality = 'high';
  context.drawImage(image, 0, 0, width, height);

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error('No se pudo procesar la imagen'))),
      'image/jpeg',
      quality
    );
  });
}

/**
 * Recorta la imagen al centro en un cuadrado y la reduce a `size` px.
 * Devuelve un JPEG liviano (normalmente < 100 KB) listo para subir.
 */
export async function cropToSquareJpeg(file, size = 512, quality = 0.86) {
  if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    throw new Error('Usa una imagen JPG, PNG o WEBP.');
  }

  const image = await loadImage(file);
  const side = Math.min(image.naturalWidth, image.naturalHeight);
  const sx = (image.naturalWidth - side) / 2;
  const sy = (image.naturalHeight - side) / 2;
  const target = Math.min(size, side);

  const canvas = document.createElement('canvas');
  canvas.width = target;
  canvas.height = target;

  const context = canvas.getContext('2d');
  context.fillStyle = '#ffffff'; // fondo blanco para PNG con transparencia
  context.fillRect(0, 0, target, target);
  context.imageSmoothingQuality = 'high';
  context.drawImage(image, sx, sy, side, side, 0, 0, target, target);

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error('No se pudo procesar la imagen'))),
      'image/jpeg',
      quality
    );
  });
}
