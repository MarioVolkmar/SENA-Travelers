import { useState } from 'react';

import { mediaUrl } from '../../api/axiosConfig';

import './Avatar.css';

/**
 * Foto de perfil del usuario o, si no tiene (o no carga), su inicial.
 */
function Avatar({ user, size = 36, className = '' }) {
  const src = mediaUrl(user?.foto_url);
  const [failedSrc, setFailedSrc] = useState(null);

  const initial = (user?.nombre || '?').trim().charAt(0).toUpperCase();
  const showImage = src && failedSrc !== src;

  return (
    <span
      className={`avatar ${className}`}
      style={{ width: size, height: size, fontSize: Math.round(size * 0.42) }}
      aria-hidden="true"
    >
      {showImage ? (
        <img
          src={src}
          alt=""
          referrerPolicy="no-referrer"
          onError={() => setFailedSrc(src)}
        />
      ) : (
        initial
      )}
    </span>
  );
}

export default Avatar;
