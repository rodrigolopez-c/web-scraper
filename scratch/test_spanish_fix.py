import pandas as pd
import re

df = pd.read_csv('informes_rector_universal.csv')
sample_texts = df['text-original'].dropna().tolist()

def fix_spanish_ocr_artifacts(text: str) -> str:
    if not text:
        return ""
    
    # Lista de reemplazos directos de palabras comunes con acentos garabateados por OCR en DSpace
    word_replacements = {
        'Mxico': 'México', 'mxico': 'méxico',
        'Perifrico': 'Periférico', 'perifrico': 'periférico',
        'Tecnolgico': 'Tecnológico', 'tecnolgico': 'tecnológico',
        'Gmez': 'Gómez', 'gmez': 'gómez',
        'Acua': 'Acuña', 'acua': 'acuña',
        'Velzquez': 'Velázquez', 'velzquez': 'velázquez',
        'Captulo': 'Capítulo', 'captulo': 'capítulo',
        'Poltica': 'Política', 'poltica': 'política',
        'Polticas': 'Políticas', 'polticas': 'políticas',
        'Acadmico': 'Académico', 'acadmico': 'académico',
        'Acadmica': 'Académica', 'acadmica': 'académica',
        'Pblica': 'Pública', 'pblica': 'pública',
        'Sesin': 'Sesión', 'sesin': 'sesión',
        'nmero': 'número', 'Nmero': 'Número',
        'artculo': 'artículo', 'Artculo': 'Artículo',
        'pgina': 'página', 'Pgina': 'Página',
        'tambin': 'también', 'Tambin': 'También',
        'ms': 'más', 'Ms': 'Más',
        'as': 'así', 'As': 'Así',
        'año': 'año', 'Ao': 'Año', 'ao': 'año', 'aos': 'años', 'Aos': 'Años',
        'diseo': 'diseño', 'Diseo': 'Diseño',
        'formacin': 'formación', 'Formacin': 'Formación',
        'impresin': 'impresión', 'Impresin': 'Impresión',
        'gestin': 'gestión', 'Gestin': 'Gestión',
        'investigacin': 'investigación', 'Investigacin': 'Investigación',
        'educacin': 'educación', 'Educacin': 'Educación',
        'evaluacin': 'evaluación', 'Evaluacin': 'Evaluación',
        'planeacin': 'planeación', 'Planeacin': 'Planeación',
        'direccin': 'dirección', 'Direccin': 'Dirección',
        'coordinacin': 'coordinación', 'Coordinacin': 'Coordinación',
        'participacin': 'participación', 'Participacin': 'Participación',
        'vinculacin': 'vinculación', 'Vinculacin': 'Vinculación',
        'construccin': 'construcción', 'Construccin': 'Construcción',
        'poblacin': 'población', 'Poblacin': 'Población',
        'revisin': 'revisión', 'Revisin': 'Revisión',
        'relacin': 'relación', 'Relacin': 'Relación',
        'institucin': 'institución', 'Institucin': 'Institución',
        'atencin': 'atención', 'Atencin': 'Atención',
        'posicin': 'posición', 'Posicin': 'Posición',
        'acredizacin': 'acreditación', 'Acreditacin': 'Acreditación'
    }
    
    for old, new in word_replacements.items():
        text = text.replace(old, new)
        
    # Patrones regex sufijos comunes en español con ''
    # Sufijo -ción / -sión / -gión / -ñón / -zón
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})[iI]n\b', r'\1ión', text)
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})[iI]nes\b', r'\1iones', text)
    
    # Sufijo -ría / -rías / -gía / -gías / -tía / -día / -cía
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})a\b', r'\1ía', text)
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})as\b', r'\1ías', text)
    
    # Sufijo -tico / -tica / -ticos / -ticas / -gico / -gica / -gicos / -gicas
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})tico\b', r'\1tico', text)
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})tica\b', r'\1tica', text)
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})ticos\b', r'\1ticos', text)
    text = re.sub(r'([a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,})ticas\b', r'\1ticas', text)

    return text

# Probar recuento de '' antes y después
raw_combined = ' '.join(sample_texts)
cleaned_combined = fix_spanish_ocr_artifacts(raw_combined)

print(f"Total '' antes: {raw_combined.count('')}")
print(f"Total '' después: {cleaned_combined.count('')}")
