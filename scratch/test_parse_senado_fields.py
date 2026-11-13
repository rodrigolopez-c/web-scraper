import re
import unicodedata
from bs4 import BeautifulSoup
import trafilatura

MONTHS_ES = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'setiembre': '09', 'octubre': '10',
    'noviembre': '11', 'diciembre': '12'
}

def parse_spanish_date(text: str) -> str:
    if not text:
        return ""
    m = re.search(r'(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})', text.lower())
    if m:
        day = int(m.group(1))
        month_name = m.group(2)
        year = m.group(3)
        month = MONTHS_ES.get(month_name, '01')
        return f"{year}-{month}-{day:02d}"
    return ""

def clean_main_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = unicodedata.normalize('NFC', raw_text)
    text = text.replace('\xad', '').replace('\xa0', ' ').replace('\ufeff', '').replace('\u200b', '')
    
    # Remove footer/colophon table ("Directorio DIARIO DE LOS DEBATES...")
    colophon_patterns = [
        r'\|?\s*Directorio\s+DIARIO DE LOS DEBATES\s+de la Cámara de Senadores.*$',
        r'Directorio\s*\n+\s*DIARIO DE LOS DEBATES\s*\n+\s*de la Cámara de Senadores.*$',
    ]
    for pat in colophon_patterns:
        text = re.sub(pat, '', text, flags=re.IGNORECASE | re.DOTALL)
        
    text = re.sub(r'[\r\t\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ufffd]', '', text)
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})-\s*\n\s*([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})', r'\1\2', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    lines = [line.strip() for line in text.split('\n')]
    cleaned_lines = []
    blank_count = 0
    for l in lines:
        if not l:
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append('')
        else:
            blank_count = 0
            cleaned_lines.append(l)
    return '\n'.join(cleaned_lines).strip()

def parse_session_html(html_str: str, sid: str):
    soup = BeautifulSoup(html_str, "html.parser")
    gaceta = soup.find("div", id="gaceta")
    if not gaceta:
        return None
    panel_body = gaceta.find("div", class_="panel-body")
    if not panel_body:
        return None
    body_rows = panel_body.find_all("div", class_="row", recursive=False)
    if len(body_rows) < 5:
        return None

    # Remove Directorio table from row 4 before extracting text
    row4 = body_rows[4]
    for tbl in row4.find_all("table", class_="forma_tabla"):
        tbl.decompose()

    # Metadata from row 2
    row2 = body_rows[2]
    tds = row2.find_all("td")
    leg_str = tds[0].get_text(" ", strip=True) if len(tds) > 0 else "LXIV Legislatura"
    anio_str = tds[1].get_text(" ", strip=True) if len(tds) > 1 else ""
    periodo_str = tds[2].get_text(" ", strip=True) if len(tds) > 2 else ""
    sesion_num_str = tds[3].get_text(" ", strip=True) if len(tds) > 3 else ""

    leg_code_m = re.search(r'(LX[IVX]+)', leg_str)
    leg_code = leg_code_m.group(1) if leg_code_m else "LXIV"

    strong_tag = row2.find("strong")
    role_title = "Presidente de la Mesa Directiva"
    speaker = "Mesa Directiva del Senado de la República"
    if strong_tag:
        parts = [p.strip() for p in strong_tag.stripped_strings if p.strip()]
        if len(parts) >= 2:
            role_title = parts[0]
            speaker = parts[1]
        elif len(parts) == 1:
            if parts[0].lower().startswith("sen"):
                speaker = parts[0]
            else:
                role_title = parts[0]

    # Row 3: Session description and date
    row3 = body_rows[3]
    p_desc = row3.find("p")
    desc_str = " ".join(p_desc.stripped_strings) if p_desc else row3.get_text(" ", strip=True)
    desc_str = re.sub(r'\s+', ' ', desc_str).strip()
    date_iso = parse_spanish_date(desc_str)

    # Fallback speaker extraction from row 4 if header didn't have it
    row4_text_raw = row4.get_text("\n")
    if speaker == "Mesa Directiva del Senado de la República":
        m_sp = re.search(r'PRESIDE(?:NCIA)?\s+(?:DE(?:L| LA)\s+)?(?:SENADOR[A]?\s+)?([A-ZÁÉÍÓÚÑ\s]{5,60})', row4_text_raw)
        if m_sp:
            name_clean = " ".join(m_sp.group(1).split()).title()
            speaker = f"Sen. {name_clean}"

    role = f"{role_title} / {leg_code} Legislatura del Senado de la República"
    context_parts = [p for p in [sesion_num_str, periodo_str, anio_str, desc_str] if p]
    context = f"{', '.join(context_parts)} - {leg_code} Legislatura del Senado de la República"

    # Build clean HTML containing ONLY the debate header + content (rows 1, 2, 3, 4)
    debate_html = "<html><body>\n" + "\n".join(str(body_rows[i]) for i in range(1, len(body_rows))) + "\n</body></html>"
    
    # text-original: raw text of rows 1..4
    raw_soup = BeautifulSoup(debate_html, "html.parser")
    text_original = raw_soup.get_text("\n", strip=True)

    # text_clean: extracted with Trafilatura + cleaned
    traf_text = trafilatura.extract(debate_html, include_tables=True, deduplicate=False)
    text_clean = clean_main_text(traf_text if traf_text else text_original)

    return {
        'sid': sid,
        'leg_code': leg_code,
        'language': 'es',
        'speaker': speaker,
        'role': role,
        'date': date_iso,
        'context': context,
        'len_orig': len(text_original),
        'len_clean': len(text_clean),
        'preview_clean': text_clean[:300]
    }

for sid in ["3011", "3015", "3100", "3278", "3400"]:
    with open(f"scratch/senado_{sid}.html", "r", encoding="utf-8") as f:
        res = parse_session_html(f.read(), sid)
    print(res)

