"""
scrapper_universal.py
=====================
Scraper universal para sitios de discursos, diarios de debates y repositorios DSpace 7.
Detecta automáticamente la fuente (infolej.congresojal.gob.mx o DSpace 7 REI ITESO)
y genera un conjunto de datos estandarizado siguiendo el esquema de `dataset_base.xlsx`:
['id', 'language', 'speaker', 'role', 'date', 'context', 'text-original', 'text_clean']

Uso por línea de comandos:
    python scrapper_universal.py --url "https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php" --output "diario_debates"
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

import pypdfium2 as pdfium
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_LOCK = threading.Lock()

class UniversalScraper:
    def __init__(self, target_url: str, output_prefix: str = "diario_debates", max_workers: int = 16):
        self.target_url = target_url.strip()
        self.output_prefix = output_prefix if os.path.isabs(output_prefix) else os.path.join(BASE_DIR, output_prefix)
        self.max_workers = max_workers
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

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
    def clean_text_content(raw_text: str) -> str:
        if not raw_text:
            return ""

        text = UniversalScraper.fix_mojibake(raw_text)
        text = unicodedata.normalize('NFC', text)
        text = text.replace('\xad', '').replace('\xa0', ' ').replace('\ufeff', '').replace('\u200b', '')

        colophon_patterns = [
            r'Tiraje:\s*[\d,]+\s*ejemplares.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
            r'Diseño y formación:.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
            r'Impresión:.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
            r'D\.R\.\s*©\s*\d{4}.*?(?=\n\n|\n[A-ZÁÉÍÓÚÑ])',
            r'A[ñn]o\s+[I|V|X]+\s*[\u2022\u00b7\-•]?\s*Tomo\s+[I|V|X]+.*?\n',
            r'Guadalajara,\s*Jalisco,\s*\d{1,2}\s+de\s+[a-z]+\s+de\s+\d{4}'
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

    def extract_speaker(self, raw_text: str):
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

    def scrape_infolej(self):
        logging.info("Extrayendo sesiones de Infolej Diario de Debates...")
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

        def process_item(item):
            try:
                r = requests.get(item['pdf_url'], headers=self.headers, verify=False, timeout=30)
                if r.status_code != 200 or not r.content.startswith(b'%PDF'):
                    return None
                pdf_bytes = r.content
            except Exception as e:
                logging.error(f"Error descargando {item['id']}: {e}")
                return None

            raw_text = ""
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
                    raw_text = "\n\n".join(pages)
            except Exception as pdf_err:
                logging.warning(f"Error parseando PDF {item['id']}: {pdf_err}")

            if not raw_text:
                return None

            context = f"{item['title_raw']} - {item['legislatura']} Legislatura del H. Congreso del Estado de Jalisco"
            speaker = self.extract_speaker(raw_text)
            role = f"Presidente de la Mesa Directiva / {item['legislatura']} Legislatura del H. Congreso del Estado de Jalisco"
            clean_text = self.clean_text_content(raw_text)

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

        logging.info(f"Procesando {len(items)} ítems con {self.max_workers} trabajadores...")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            records = [r for r in executor.map(process_item, items) if r]

        return records

    def run(self):
        records = self.scrape_infolej()
        columns = ['id', 'language', 'speaker', 'role', 'date', 'context', 'text-original', 'text_clean']
        df = pd.DataFrame(records)[columns]

        excel_path = f"{self.output_prefix}.xlsx"
        csv_path = f"{self.output_prefix}.csv"

        df_clean = df.applymap(lambda x: self.sanitize_excel_text(x) if isinstance(x, str) else x)
        df_clean.to_excel(excel_path, index=False)
        df_clean.to_csv(csv_path, index=False, encoding='utf-8-sig')

        logging.info(f"Proceso finalizado. {len(df)} registros guardados en '{excel_path}' y '{csv_path}'.")
        return df_clean

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper Universal para Diario de Debates y Repositorios")
    parser.add_argument("--url", type=str, default="https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php", help="URL objetivo")
    parser.add_argument("--output", type=str, default="diario_debates", help="Prefijo de archivo de salida")
    args = parser.parse_args()

    scraper = UniversalScraper(target_url=args.url, output_prefix=args.output)
    scraper.run()
