"""
scrapper_trafilatura.py
======================
Scraper de discursos, diarios de debates e informes utilizando Trafilatura para la
extracción limpia del cuerpo principal y eliminación de boilerplate.

Soporta:
1. Diario de los Debates del Congreso de Jalisco (infolej.congresojal.gob.mx)
2. Diario de los Debates del Senado de la República:
   - https://www.senado.gob.mx/66/diario_de_los_debates/LIV/ (Legislaturas LXIV, LXV, LXVI)
   - https://www.senado.gob.mx/informacion/diario/LXIV

Esquema de salida (dataset_base):
['id', 'language', 'speaker', 'role', 'date', 'context', 'text-original', 'text_clean']

Uso:
    python scrappers/scrapper_trafilatura.py --url "https://www.senado.gob.mx/66/diario_de_los_debates/LIV/" --output "../datasets/diario_debates_senado_trafilatura"
"""

import os
import re
import csv
import json
import html
import time
import logging
import argparse
import unicodedata
import threading
from urllib.parse import urlparse, urljoin, quote, urlunparse
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

import trafilatura
import pypdfium2 as pdfium
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "scratch", "cache_senado"))
PDF_LOCK = threading.Lock()

MONTHS_ES = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'setiembre': '09', 'octubre': '10',
    'noviembre': '11', 'diciembre': '12'
}


class TrafilaturaSpeechScraper:
    def __init__(self, target_url: str, output_prefix: str = "../datasets/diario_debates_senado_trafilatura", max_workers: int = 10):
        self.target_url = target_url.strip()
        self.output_prefix = output_prefix if os.path.isabs(output_prefix) else os.path.normpath(os.path.join(BASE_DIR, output_prefix))
        self.max_workers = max_workers
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    @staticmethod
    def fix_mojibake(text: str) -> str:
        if not text:
            return ""
        try:
            if 'Ã' in text or 'Â' in text:
                return text.encode('latin-1').decode('utf-8')
        except Exception:
            pass
        return text

    @staticmethod
    def sanitize_url(url: str) -> str:
        parsed = urlparse(url)
        encoded_path = quote(parsed.path)
        return urlunparse((parsed.scheme, parsed.netloc, encoded_path, parsed.params, parsed.query, parsed.fragment))

    @staticmethod
    def sanitize_excel_text(text: str) -> str:
        if not isinstance(text, str):
            return text
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', '', text)

    @staticmethod
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

    @staticmethod
    def clean_main_text(raw_text: str) -> str:
        if not raw_text:
            return ""

        text = TrafilaturaSpeechScraper.fix_mojibake(raw_text)
        text = unicodedata.normalize('NFC', text)
        text = text.replace('\xad', '').replace('\xa0', ' ').replace('\ufeff', '').replace('\u200b', '')

        colophon_patterns = [
            r'Tiraje:\s*[\d,]+\s*ejemplares.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
            r'Diseño y formación:.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
            r'Impresión:.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
            r'D\.R\.\s*©\s*\d{4}.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
            r'A[ñn]o\s+[I|V|X]+\s*[\u2022\u00b7\-•]?\s*Tomo\s+[I|V|X]+.*?\n',
            r'Guadalajara,\s*Jalisco,\s*\d{1,2}\s+de\s+[a-z]+\s+de\s+\d{4}',
            r'\|?\s*Directorio\s+DIARIO DE LOS DEBATES\s+de la Cámara de Senadores.*$',
            r'Directorio\s*\n+\s*DIARIO DE LOS DEBATES\s*\n+\s*de la Cámara de Senadores.*$'
        ]
        for pattern in colophon_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

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

    def extract_speaker(self, raw_text: str, context: str):
        header = raw_text[:3000]
        patterns = [
            r'Presidencia:\s*(?:C\.\s*)?(?:Diputad[oa]\s*)?([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.\-–]+?)(?=\.|\n|Secretar|\n\n)',
            r'(?:C\.\s*)?Diputad[oa]\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)\s*\n\s*Presidente',
            r'Presidente:\s*(?:C\.\s*)?(?:Diputad[oa]\s*)?([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)(?=\.|\n|\n\n)',
            r'Presidida por el diputad[oa]\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)(?=\.|\n|,\s*presidente)',
            r'Dip\.\s*([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)\s*\n\s*Presidente'
        ]
        for pat in patterns:
            m = re.search(pat, header, re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                val = re.sub(r'\s+', ' ', val).strip(' .')
                if 4 <= len(val) <= 50 and not any(k in val.lower() for k in ['general', 'proceso', 'coordinador', 'tabla', 'pagina', 'secretaria']):
                    if not val.lower().startswith('dip'):
                        val = f"Dip. {val}"
                    return val
        return "Mesa Directiva del H. Congreso del Estado de Jalisco"

    def _extract_pdf_bytes_text(self, pdf_bytes: bytes) -> str:
        if not pdf_bytes or not pdf_bytes.startswith(b'%PDF'):
            return ""
        try:
            with PDF_LOCK:
                pdf = pdfium.PdfDocument(pdf_bytes)
                pages = []
                for p in pdf:
                    t = p.get_textpage().get_text_range()
                    try:
                        t_lat = t.encode('latin-1', errors='ignore').decode('latin-1')
                        t = t_lat if '\ufffd' not in t_lat else t.encode('latin-1', errors='ignore').decode('utf-8', errors='replace')
                    except Exception:
                        pass
                    pages.append(t)
                return "\n\n".join(pages)
        except Exception as e:
            logging.warning(f"Error parseando PDF: {e}")
            return ""

    def process_senado(self):
        """
        Extrae el Diario de los Debates del Senado de la República para las
        Legislaturas LXIV (2018-2021), LXV (2021-2024) y LXVI (2024-hoy)
        usando el portal /66/diario_de_los_debates/{LXIV,LXV,LXVI}/ y /informacion/diario/.
        """
        logging.info("Iniciando extracción Trafilatura para Diario de los Debates del Senado (Legislaturas LXIV, LXV y LXVI)...")
        os.makedirs(CACHE_DIR, exist_ok=True)

        target_legs = ["LXIV", "LXV", "LXVI"]
        discovered = {}

        # 1. Catalogar todas las sesiones de LXIV, LXV y LXVI desde /66/diario_de_los_debates/{leg}/ (o caché local)
        for leg in target_legs:
            idx_url = f"https://www.senado.gob.mx/66/diario_de_los_debates/{leg}/"
            local_idx = os.path.normpath(os.path.join(BASE_DIR, "..", "scratch", f"senado_66_{leg}.html"))
            html_idx = ""
            try:
                r = requests.get(idx_url, headers=self.headers, verify=False, timeout=15)
                if r.status_code == 200 and len(r.text) > 10000:
                    html_idx = r.text
                    with open(local_idx, "w", encoding="utf-8") as lf:
                        lf.write(html_idx)
            except Exception as e:
                if os.path.exists(local_idx):
                    with open(local_idx, "r", encoding="utf-8") as lf:
                        html_idx = lf.read()
                else:
                    logging.error(f"Error consultando índice {idx_url}: {e}")

            if html_idx:
                soup = BeautifulSoup(html_idx, "lxml")
                count = 0
                for a in soup.find_all("a", href=True):
                    m = re.search(r'/66/diario_de_los_debates/documento/(\d+)', a["href"])
                    if m:
                        txt = a.get_text(" ", strip=True)
                        # Omitir el banner superior que apunta siempre a la última sesión de la LXVI
                        if "Legislatura" in txt or "Año de ejercicio" in txt:
                            continue
                        sid = int(m.group(1))
                        if sid not in discovered:
                            discovered[sid] = {
                                'sid': sid,
                                'leg_code': leg,
                                'link_text': txt,
                                'url': f"https://www.senado.gob.mx/informacion/diario/sesion/{sid}",
                                'doc_url': f"https://www.senado.gob.mx/66/diario_de_los_debates/documento/{sid}"
                            }
                            count += 1
                logging.info(f"Legislatura {leg} ({idx_url}): {count} sesiones catalogadas.")

        # Fallback a /informacion/diario/ si fuera necesario
        if not discovered:
            for leg in ["LXIV", "LXV"]:
                for anio in ["I", "II", "III"]:
                    idx_url = f"https://www.senado.gob.mx/informacion/diario/{leg}/{anio}"
                    try:
                        r = requests.get(idx_url, headers=self.headers, verify=False, timeout=20)
                        soup = BeautifulSoup(r.text, "lxml")
                        for a in soup.find_all("a", href=True):
                            m = re.search(r'/informacion/diario/sesion/(\d+)', a["href"])
                            if m:
                                sid = int(m.group(1))
                                if sid not in discovered:
                                    discovered[sid] = {
                                        'sid': sid,
                                        'leg_code': leg,
                                        'link_text': a.get_text(" ", strip=True),
                                        'url': f"https://www.senado.gob.mx/informacion/diario/sesion/{sid}",
                                        'doc_url': f"https://www.senado.gob.mx/66/diario_de_los_debates/documento/{sid}"
                                    }
                    except Exception:
                        pass

        sorted_items = [discovered[k] for k in sorted(discovered.keys())]
        total_items = len(sorted_items)
        logging.info(f"Total sesiones a extraer: {total_items} (LXIV, LXV, LXVI) con {self.max_workers} trabajadores...")

        progress_lock = threading.Lock()
        completed_count = [0]
        valid_count = [0]
        partial_records = []
        csv_path = f"{self.output_prefix}.csv"
        os.makedirs(os.path.dirname(os.path.abspath(self.output_prefix)), exist_ok=True)

        def fetch_and_parse_senado(item):
            sid = item['sid']
            leg_code = item['leg_code']
            url = item['url']
            cache_file = os.path.join(CACHE_DIR, f"sesion_{sid}.html")

            html_str = None
            if os.path.exists(cache_file) and os.path.getsize(cache_file) > 13000:
                try:
                    with open(cache_file, "r", encoding="utf-8") as cf:
                        html_str = cf.read()
                except Exception:
                    html_str = None

            if not html_str:
                for attempt in range(5):
                    try:
                        r = requests.get(url, headers=self.headers, verify=False, timeout=30)
                        if r.status_code == 200 and len(r.text) > 13000 and "DIARIO DE LOS DEBATES" in r.text:
                            html_str = r.text
                            try:
                                with open(cache_file, "w", encoding="utf-8") as cf:
                                    cf.write(html_str)
                            except Exception:
                                pass
                            break
                        elif r.status_code == 200 and 'id="gaceta"' in r.text and len(r.text) <= 13000:
                            break
                    except Exception:
                        pass
                    time.sleep(1.0 * (attempt + 1))

            with progress_lock:
                completed_count[0] += 1
                curr = completed_count[0]

            if not html_str:
                if curr % 50 == 0 or curr == total_items:
                    logging.info(f"Progreso: {curr}/{total_items} procesadas ({valid_count[0]} válidas)...")
                return None

            soup = BeautifulSoup(html_str, "lxml")
            gaceta = soup.find("div", id="gaceta")
            if not gaceta:
                return None
            panel_body = gaceta.find("div", class_="panel-body")
            if not panel_body:
                return None
            body_rows = panel_body.find_all("div", class_="row", recursive=False)
            if len(body_rows) < 5:
                return None

            row2 = body_rows[2]
            row3 = body_rows[3]
            row4 = body_rows[4]

            tds = row2.find_all("td")
            anio_str = tds[1].get_text(" ", strip=True) if len(tds) > 1 else ""
            periodo_str = tds[2].get_text(" ", strip=True) if len(tds) > 2 else ""
            sesion_num_str = tds[3].get_text(" ", strip=True) if len(tds) > 3 else ""

            # Respetar la legislatura real (LXIV, LXV, LXVI) obtenida del índice /66/
            if sid >= 3539:
                leg_code = "LXVI"
            elif sid >= 3277:
                leg_code = "LXV"
            else:
                leg_code = "LXIV"

            # Fecha e información descriptiva de la sesión (Row 3)
            p_desc = row3.find("p")
            desc_str = " ".join(p_desc.stripped_strings) if p_desc else row3.get_text(" ", strip=True)
            desc_str = re.sub(r'Versi[óo]n para descarga.*', '', desc_str, flags=re.IGNORECASE)
            desc_str = re.sub(r'\s+', ' ', desc_str).strip()

            date_iso = self.parse_spanish_date(desc_str)
            if not date_iso and item['link_text']:
                date_iso = self.parse_spanish_date(item['link_text'])

            # Extraer speaker y role de la caja de metadatos (Row 2) o cuerpo (Row 4)
            role_title = "Presidente de la Mesa Directiva"
            speaker = "Mesa Directiva del Senado de la República"

            strong_tag = row2.find("strong")
            if strong_tag:
                parts = [re.sub(r'\s+', ' ', p).strip() for p in strong_tag.stripped_strings if p.strip()]
                if len(parts) >= 2:
                    role_title = parts[0]
                    speaker = parts[1]
                elif len(parts) == 1:
                    if parts[0].lower().startswith("sen"):
                        speaker = parts[0]
                    else:
                        role_title = parts[0]

            row4_raw_preview = row4.get_text("\n")[:4000]
            if speaker == "Mesa Directiva del Senado de la República":
                m_pres = re.search(
                    r'(?:El|La)\s+(Presidente|Presidenta)(?:\s+de\s+la\s+Mesa\s+Directiva|\s+de\s+la\s+Mesa\s+de\s+Decanos)?,?\s+Senador(?:a)?\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?):',
                    row4_raw_preview
                )
                if m_pres:
                    role_title = f"{m_pres.group(1)} de la Mesa Directiva"
                    name_val = re.sub(r'\s+', ' ', m_pres.group(2)).strip(' .')
                    speaker = f"Sen. {name_val}"
                else:
                    m_header = re.search(
                        r'PRESIDE(?:NCIA)?\s+(?:DE(?:L| LA)\s+)?(?:MESA\s+DE\s+DECANOS\s+)?(?:EL\s+|LA\s+)?SENADOR(A)?\s*\n+\s*([A-ZÁÉÍÓÚÑ\s\.]{5,60}?)(?=\n|APERTURA)',
                        row4_raw_preview
                    )
                    if m_header:
                        is_fem = bool(m_header.group(1)) or ('LA SENADORA' in m_header.group(0))
                        role_title = "Presidenta de la Mesa Directiva" if is_fem else "Presidente de la Mesa Directiva"
                        name_val = " ".join(m_header.group(2).split()).title()
                        speaker = f"Sen. {name_val}"

            if not speaker.lower().startswith("sen") and speaker != "Mesa Directiva del Senado de la República":
                speaker = f"Sen. {speaker}"

            role = f"{role_title} / {leg_code} Legislatura del Senado de la República"

            periodo_clean = re.sub(r'\s+', ' ', periodo_str).strip()
            anio_clean = re.sub(r'\s+', ' ', anio_str).strip()
            sesion_clean = re.sub(r'\s+', ' ', sesion_num_str).strip()
            context_parts = [p for p in [sesion_clean, periodo_clean, anio_clean, desc_str] if p]
            context = f"{', '.join(context_parts)} - {leg_code} Legislatura del Senado de la República"

            # Eliminar únicamente la tabla de Directorio final (<table class="forma_tabla"> pequeña)
            for tbl in row4.find_all("table", class_="forma_tabla"):
                tbl_txt = tbl.get_text(" ", strip=True)
                if "Directorio" in tbl_txt and len(tbl_txt) < 1000:
                    tbl.decompose()

            # Texto original completo (Rows 1 a 4, sin el menú superior Row 0)
            text_original = "\n\n".join(
                body_rows[i].get_text("\n", strip=True) for i in range(1, len(body_rows))
            ).strip()

            # Construir HTML limpio de párrafos del debate para extracción rápida y precisa con Trafilatura
            row4_lines = [line.strip() for line in row4.get_text("\n").splitlines() if line.strip()]
            debate_html = "<html><body><article><p>" + "</p>\n<p>".join(row4_lines) + "</p></article></body></html>"
            try:
                traf_extracted = trafilatura.extract(debate_html, fast=True, deduplicate=False)
            except Exception:
                traf_extracted = ""

            # Si la página solo tenía enlace a PDF y no cuerpo HTML, intentar descarga de PDF
            if (not traf_extracted or len(traf_extracted) < 100) and len(text_original) < 600:
                pdf_a = row3.find("a", href=re.compile(r'\.pdf$', re.I))
                if pdf_a:
                    pdf_url = self.sanitize_url(urljoin(url, pdf_a["href"]))
                    try:
                        pr = requests.get(pdf_url, headers=self.headers, verify=False, timeout=25)
                        if pr.status_code == 200 and pr.content.startswith(b'%PDF'):
                            pdf_text = self._extract_pdf_bytes_text(pr.content)
                            if pdf_text:
                                text_original = pdf_text
                                traf_pdf = trafilatura.extract(pdf_text, fast=True)
                                traf_extracted = traf_pdf if traf_pdf else pdf_text
                    except Exception:
                        pass

            clean_text = self.clean_main_text(traf_extracted if traf_extracted else text_original)
            if not clean_text or len(clean_text) < 50:
                return None

            rec_obj = {
                'sid': sid,
                'leg_code': leg_code,
                'language': 'es',
                'speaker': speaker,
                'role': role,
                'date': date_iso,
                'context': context,
                'text-original': text_original,
                'text_clean': clean_text
            }

            with progress_lock:
                valid_count[0] += 1
                v_curr = valid_count[0]

            if curr % 50 == 0 or curr == total_items:
                logging.info(f"Progreso: {curr}/{total_items} procesadas ({v_curr} válidas)...")

            return rec_obj

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            raw_records = [r for r in executor.map(fetch_and_parse_senado, sorted_items) if r]

        # Ordenar cronológicamente / por sid y asignar ID secuencial por legislatura (DD-LXIV-001, DD-LXV-001, DD-LXVI-001)
        leg_order = {'LXIV': 1, 'LXV': 2, 'LXVI': 3}
        raw_records.sort(key=lambda x: (leg_order.get(x['leg_code'], 9), x['date'] or '9999-99-99', x['sid']))
        leg_counters = {}
        final_records = []
        for rec in raw_records:
            leg = rec['leg_code']
            leg_counters[leg] = leg_counters.get(leg, 0) + 1
            rec_id = f"DD-{leg}-{leg_counters[leg]:03d}"
            final_records.append({
                'id': rec_id,
                'language': rec['language'],
                'speaker': rec['speaker'],
                'role': rec['role'],
                'date': rec['date'],
                'context': rec['context'],
                'text-original': rec['text-original'],
                'text_clean': rec['text_clean']
            })

        logging.info(f"Extracción del Senado completada: {len(final_records)} sesiones válidas ({leg_counters}).")
        return final_records

    def process_infolej(self):
        logging.info("Iniciando extracción Trafilatura para Diario de Debates (infolej)...")
        session = requests.Session()
        items = []

        for leg in ['LX', 'LXI', 'LXII', 'LXIII', 'LXIV']:
            data = {
                'C_Legis': leg, 'C_NS': '0', 'C_tipo': '0', 'C_Fecha': '',
                'C_Fecha1': '', 'C_Acuerdo': '0', 'C_buscar': '1', 'Submit': 'Buscar'
            }
            try:
                r = session.post(self.target_url, headers=self.headers, data=data, verify=False, timeout=20)
                text = html.unescape(r.content.decode('iso-8859-1', errors='replace'))
                soup = BeautifulSoup(text, 'html.parser')
                tables = soup.find_all('table')
                count = 0
                for t in tables:
                    a = t.find('a', href=True)
                    if a and '.pdf' in a['href'].lower():
                        row_text = t.get_text(' ', strip=True).replace('Acceder', '').strip()
                        date_match = re.search(r'd[íi]a\s*(\d{2}-\d{2}-\d{4})', row_text, re.IGNORECASE)
                        date_str = date_match.group(1) if date_match else ""

                        clean_pdf_url = self.sanitize_url(urljoin(self.target_url, a['href']))
                        count += 1
                        items.append({
                            'id': f"DD-{leg}-{count:03d}",
                            'legislatura': leg,
                            'title_raw': row_text,
                            'date': date_str,
                            'pdf_url': clean_pdf_url
                        })
                logging.info(f"Legislatura {leg}: {count} sesiones parseadas.")
            except Exception as e:
                logging.error(f"Error parseando Legislatura {leg}: {e}")

        def process_one(item):
            try:
                r = requests.get(item['pdf_url'], headers=self.headers, verify=False, timeout=30)
                if r.status_code != 200 or not r.content.startswith(b'%PDF'):
                    return None
                pdf_bytes = r.content
            except Exception as e:
                logging.error(f"Error descargando {item['id']}: {e}")
                return None

            raw_text = self._extract_pdf_bytes_text(pdf_bytes)
            if not raw_text:
                return None

            context = f"{item['title_raw']} - {item['legislatura']} Legislatura del H. Congreso del Estado de Jalisco"
            speaker = self.extract_speaker(raw_text, context)
            role = f"Presidente de la Mesa Directiva / {item['legislatura']} Legislatura del H. Congreso del Estado de Jalisco"

            try:
                traf_extracted = trafilatura.extract(raw_text) if raw_text else ""
                clean_text = self.clean_main_text(traf_extracted if traf_extracted else raw_text)
            except Exception:
                clean_text = self.clean_main_text(raw_text)

            date_formatted = item['date']
            if date_formatted and len(date_formatted) == 10 and '-' in date_formatted:
                parts = date_formatted.split('-')
                if len(parts[0]) == 2 and len(parts[2]) == 4:
                    date_formatted = f"{parts[2]}-{parts[1]}-{parts[0]}"

            return {
                'id': item['id'],
                'language': 'es',
                'speaker': speaker,
                'role': role,
                'date': date_formatted,
                'context': context,
                'text-original': raw_text,
                'text_clean': clean_text
            }

        logging.info(f"Descargando y procesando {len(items)} sesiones con {self.max_workers} trabajadores...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            records = [r for r in executor.map(process_one, items) if r]

        return records

    def run(self):
        if "senado.gob.mx" in self.target_url.lower():
            records = self.process_senado()
        else:
            records = self.process_infolej()

        columns = ['id', 'language', 'speaker', 'role', 'date', 'context', 'text-original', 'text_clean']
        df = pd.DataFrame(records)[columns]

        os.makedirs(os.path.dirname(os.path.abspath(self.output_prefix)), exist_ok=True)
        excel_path = f"{self.output_prefix}.xlsx"
        csv_path = f"{self.output_prefix}.csv"

        if hasattr(df, 'map'):
            df_clean = df.map(lambda x: self.sanitize_excel_text(x) if isinstance(x, str) else x)
        else:
            df_clean = df.applymap(lambda x: self.sanitize_excel_text(x) if isinstance(x, str) else x)

        # Guardar Excel primero y luego CSV con reintentos ante bloqueos temporales de OneDrive/Excel
        for attempt in range(5):
            try:
                df_clean.to_excel(excel_path, index=False)
                break
            except PermissionError:
                time.sleep(1.5)

        csv_saved = False
        for attempt in range(5):
            try:
                df_clean.to_csv(csv_path, index=False, encoding='utf-8-sig')
                csv_saved = True
                break
            except PermissionError:
                time.sleep(1.5)

        if not csv_saved:
            alt_csv = f"{self.output_prefix}_completo.csv"
            df_clean.to_csv(alt_csv, index=False, encoding='utf-8-sig')
            logging.warning(f"El archivo '{csv_path}' está abierto en otro programa; se guardó copia completa en '{alt_csv}'.")

        logging.info(f"Proceso finalizado. {len(df)} registros guardados en '{excel_path}' y '{csv_path}'.")
        return df_clean


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper Trafilatura para Diario de Debates y Colecciones")
    parser.add_argument("--url", type=str, default="https://www.senado.gob.mx/66/diario_de_los_debates/LIV/", help="URL objetivo")
    parser.add_argument("--output", type=str, default="../datasets/diario_debates_senado_trafilatura", help="Prefijo de archivo de salida")
    args = parser.parse_args()

    scraper = TrafilaturaSpeechScraper(target_url=args.url, output_prefix=args.output)
    scraper.run()
