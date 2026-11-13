"""
scrapper.py
===========
Scraper universal para sitios de discursos, diarios de debates y repositorios DSpace 7.
Detecta automáticamente la fuente (infolej.congresojal.gob.mx o DSpace 7 REI ITESO)
y genera un conjunto de datos estandarizado siguiendo el esquema de `dataset_base.xlsx`:
['id', 'language', 'speaker', 'role', 'date', 'context', 'text-original', 'text_clean']

Uso por línea de comandos:
    python scrapper.py --url "https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php" --output "diario_debates"
"""

from scrapper_universal import UniversalScraper, argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper Universal para Diario de Debates y Repositorios")
    parser.add_argument("--url", type=str, default="https://infolej.congresojal.gob.mx/consulta/DiarioDeDebates.php", help="URL objetivo")
    parser.add_argument("--output", type=str, default="diario_debates", help="Prefijo de archivo de salida")
    args = parser.parse_args()

    scraper = UniversalScraper(target_url=args.url, output_prefix=args.output)
    scraper.run()
