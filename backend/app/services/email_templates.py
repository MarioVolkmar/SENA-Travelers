"""
Plantilla HTML de los correos de Travelers.

Los correos se arman con tablas y estilos en línea porque Gmail, Outlook y los
clientes de celular ignoran casi todo el CSS moderno (flexbox, clases, <style>).
Cada correo se envía en dos versiones: esta en HTML y una en texto plano.
"""
from html import escape

NIGHT = "#0b1520"
SURFACE = "#121e2b"
ACCENT = "#f5a524"
TEXT = "#1d2733"
MUTED = "#5f6b78"
LINE = "#e3e7ec"
SOFT = "#f4f6f8"

TONES = {
    "info": ACCENT,       # avisos generales
    "success": "#2fa36b", # pago aprobado
    "danger": "#d9534f",  # cancelación
    "warning": "#e8961c", # plazo por vencer
}


def _detail_rows(details):
    rows = []
    for index, (label, value) in enumerate(details):
        border = f"border-top:1px solid {LINE};" if index else ""
        rows.append(
            f'<tr>'
            f'<td style="{border}padding:12px 0;font-size:14px;color:{MUTED};">{escape(str(label))}</td>'
            f'<td style="{border}padding:12px 0;font-size:14px;color:{TEXT};font-weight:700;text-align:right;">{escape(str(value))}</td>'
            f'</tr>'
        )
    return "".join(rows)


def render_email(
    *,
    title: str,
    greeting: str,
    paragraphs: list[str],
    preheader: str = "",
    eyebrow: str = "",
    details: list[tuple[str, str]] | None = None,
    button: tuple[str, str] | None = None,
    note: str = "",
    tone: str = "info",
) -> str:
    """
    Devuelve el HTML del correo.

    - title: titular grande de la cabecera.
    - paragraphs: párrafos del cuerpo (texto plano; se escapan).
    - details: filas "etiqueta → valor" en un recuadro (código, fecha, total...).
    - button: (texto, enlace) del botón principal.
    - note: texto pequeño al final (avisos de seguridad, por ejemplo).
    """
    color = TONES.get(tone, ACCENT)
    body = "".join(
        f'<p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:{TEXT};">{escape(text)}</p>'
        for text in paragraphs
    )

    details_html = ""
    if details:
        details_html = (
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="margin:8px 0 24px;padding:4px 20px;background:{SOFT};border-radius:12px;">'
            f'{_detail_rows(details)}</table>'
        )

    button_html = ""
    if button:
        text, url = button
        button_html = (
            f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 24px;">'
            f'<tr><td style="border-radius:999px;background:{ACCENT};">'
            f'<a href="{escape(url, quote=True)}" target="_blank" '
            f'style="display:inline-block;padding:14px 28px;font-size:15px;font-weight:700;'
            f'color:{NIGHT};text-decoration:none;border-radius:999px;">{escape(text)}</a>'
            f'</td></tr></table>'
            f'<p style="margin:0 0 20px;font-size:12px;line-height:1.5;color:{MUTED};">'
            f'Si el botón no funciona, copia este enlace en tu navegador:<br>'
            f'<a href="{escape(url, quote=True)}" style="color:{MUTED};word-break:break-all;">{escape(url)}</a></p>'
        )

    note_html = (
        f'<p style="margin:8px 0 0;padding-top:16px;border-top:1px solid {LINE};font-size:13px;line-height:1.5;color:{MUTED};">'
        f'{escape(note)}</p>'
        if note else ""
    )

    eyebrow_html = (
        f'<p style="margin:0 0 8px;font-size:12px;font-weight:700;letter-spacing:2px;color:{color};text-transform:uppercase;">'
        f'{escape(eyebrow)}</p>'
        if eyebrow else ""
    )

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light only">
<title>{escape(title)}</title>
</head>
<body style="margin:0;padding:0;background:{SOFT};font-family:Segoe UI,Helvetica,Arial,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{SOFT};">
<tr><td align="center" style="padding:32px 16px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">
    <tr><td style="padding:28px 32px;background:{NIGHT};border-radius:20px 20px 0 0;">
      <p style="margin:0 0 22px;font-size:24px;font-weight:800;letter-spacing:1px;color:#ffffff;">TRAVELERS<span style="color:{ACCENT};">.</span></p>
      <table role="presentation" cellpadding="0" cellspacing="0"><tr><td style="width:44px;height:3px;background:{color};font-size:0;line-height:0;">&nbsp;</td></tr></table>
      <p style="margin:14px 0 0;font-size:26px;line-height:1.25;font-weight:800;color:#ffffff;">{escape(title)}</p>
    </td></tr>
    <tr><td style="padding:32px;background:#ffffff;border-radius:0 0 20px 20px;">
      {eyebrow_html}
      <p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:{TEXT};font-weight:700;">{escape(greeting)}</p>
      {body}
      {details_html}
      {button_html}
      {note_html}
    </td></tr>
    <tr><td style="padding:24px 16px;text-align:center;font-size:12px;line-height:1.6;color:{MUTED};">
      Travelers · Paquetes turísticos por Colombia<br>
      Recibes este correo por tu cuenta o tus reservas en Travelers.
    </td></tr>
  </table>
</td></tr>
</table>
</body>
</html>"""
