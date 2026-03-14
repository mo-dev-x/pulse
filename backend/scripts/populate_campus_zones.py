#!/usr/bin/env python3
"""Populate campus_zones with the Universite Laval dataset used by the backend."""

from pathlib import Path
import os
import sys

try:
    import pymysql
    from dotenv import load_dotenv
except ImportError as exc:  # pragma: no cover - script entrypoint
    print(
        "Missing dependency for populate_campus_zones.py. "
        "Run it with backend/venv/bin/python or install backend requirements.",
        file=sys.stderr,
    )
    raise


CAMPUS_ZONES = [
    ('Pavillon Alphonse-Desjardins', 'Administration, sciences sociales (ADJ)', 'academic'),
    ('Pavillon Charles-De Koninck', 'Philosophie (DKN)', 'academic'),
    ('Pavillon Félix-Antoine-Savard', 'Lettres et sciences humaines (FAS)', 'academic'),
    ('Pavillon Jean-Charles-Bonenfant', 'Bibliothèque des sciences humaines et sociales (BNF)', 'academic'),
    ('Pavillon Louis-Jacques-Casault', 'Sciences de l\'éducation (CSL)', 'academic'),
    ('Pavillon Jeanne-Lapointe', 'Littérature, langues (JLA)', 'academic'),
    ('Pavillon Adrien-Pouliot', 'Génie (PLT)', 'academic'),
    ('Pavillon Alexandre-Vachon', 'Sciences et génie, mathématiques (VCH)', 'academic'),
    ('Pavillon Abitibi-Price', 'Foresterie, géographie (ABP)', 'academic'),
    ('Pavillon Gene-H. Kruger', 'Sciences forestières (GHK)', 'academic'),
    ('Pavillon Paul-Comtois', 'Sciences de l\'agriculture et de l\'alimentation (CMT)', 'academic'),
    ('Pavillon de l\'Envirotron', 'Sciences de l\'environnement (EVT)', 'academic'),
    ('Pavillon Charles-Eugène-Marchand', 'Chimie (CHM)', 'academic'),
    ('Pavillon d\'Optique-photonique', 'Optique, photonique, physique (COP)', 'academic'),
    ('Pavillon Ferdinand-Vandry', 'Sciences de la santé, médecine (VND)', 'academic'),
    ('Pavillon de la Médecine dentaire', 'Dentisterie (MDE)', 'academic'),
    ('Pavillon Maurice-Pollack', 'Pharmacie (POL)', 'academic'),
    ('Pavillon Agathe-Lacerte', 'Nutrition, sciences infirmières (LCT)', 'academic'),
    ('Pavillon Palasis-Prince', 'Sciences de l\'administration (PAP)', 'academic'),
    ('Pavillon des Services', 'Services aux étudiants, registrariat (PSA)', 'social'),
    ('Place de l\'Université', 'Cœur du campus, espaces de rencontre', 'social'),
    ('Pavillon Alphonse-Marie-Parent', 'Services aux étudiants (PRN)', 'social'),
    ('PEPS - Zone sociale', 'Cafétéria, espaces communs PEPS', 'social'),
    ('PEPS - Pavillon principal', 'Centre sportif principal (PEPS)', 'sports'),
    ('PEPS - Arénas', 'Patinoires et sports sur glace', 'sports'),
    ('PEPS - Gymnases', 'Salles d\'entraînement et sports collectifs', 'sports'),
    ('PEPS - Piscine', 'Centre aquatique', 'sports'),
    ('Stade TELUS-Université Laval', 'Stade de football (SSI)', 'sports'),
    ('Terrain extérieur PEPS', 'Terrains sportifs extérieurs', 'sports'),
    ('Café de la Terrasse', 'Café étudiant, espace détente', 'dining'),
    ('Café Desjardins', 'Cafétéria Pavillon Alphonse-Desjardins', 'dining'),
    ('Café PEPS', 'Restauration au complexe sportif', 'dining'),
    ('Café Pollack', 'Cafétéria Pavillon Maurice-Pollack', 'dining'),
    ('Résidences universitaires - Zone Nord', 'Résidences étudiantes secteur nord', 'residence'),
    ('Résidences universitaires - Zone Sud', 'Résidences étudiantes secteur sud', 'residence'),
    ('Pavillon Ernest-Lemieux', 'Résidence (LEM)', 'residence'),
    ('Jardin Roger-Van den Hende', 'Jardin botanique, espaces verts', 'other'),
    ('Boulevard Hochelaga', 'Artère principale du campus', 'other'),
    ('Avenue de la Médecine', 'Secteur sciences de la santé', 'other'),
    ('Rue de l\'Université', 'Axe central du campus', 'other'),
    ('Stationnements campus', 'Aires de stationnement', 'other'),
    ('Pavillon de l\'Est', 'Installations diverses (PVE)', 'other'),
]


def main():
    backend_dir = Path(__file__).resolve().parents[1]
    load_dotenv(backend_dir / '.env')

    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'pulse_db'),
        charset='utf8mb4',
        autocommit=False,
    )

    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM campus_zones')
            cur.executemany(
                'INSERT INTO campus_zones (name, description, zone_type) VALUES (%s, %s, %s)',
                CAMPUS_ZONES,
            )
        conn.commit()
        print(f'Inserted {len(CAMPUS_ZONES)} campus zones.')
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
