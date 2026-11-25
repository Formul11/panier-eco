"""Récupère les catalogues et offres nationaux des enseignes sur Bonial.

Lancé par .github/workflows/catalogues.yml. Écrit catalogues/bonial.json,
lu par la version web de Panier Économique (un navigateur ne peut pas lire
bonial.fr directement depuis une autre adresse).
"""
import datetime
import json
import pathlib
import re
import sys
import time
import urllib.request

# Pages nationales (même liste que pagesBonial dans l'appli).
SLUGS = [
    'E-Leclerc', 'Carrefour', 'Super-U', 'Intermarche', 'Lidl', 'Aldi',
    'Auchan', 'Supermarches-Match', 'Norma', 'Netto', 'Monoprix',
    'Grand-Frais', 'Picard',
]
NEXT = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.S)


def lire(slug):
    requete = urllib.request.Request(
        f'https://www.bonial.fr/Enseignes/{slug}',
        headers={'User-Agent': 'Mozilla/5.0 (compatible; PanierEco/1.0)',
                 'Accept': 'text/html'})
    with urllib.request.urlopen(requete, timeout=30) as r:
        html = r.read().decode('utf-8')
    donnees = json.loads(NEXT.search(html).group(1))
    info = donnees['props']['pageProps']['pageInformation']
    brochures = info.get('brochures') or {}
    offres = (info.get('offers') or {}).get('main') or {}
    return {
        'brochures': {k: brochures.get(k) or [] for k in ('viewer', 'publisher')},
        'offers': {'main': {'items': offres.get('items') or []}},
    }


def main():
    sortie = pathlib.Path('catalogues/bonial.json')
    ancien = {}
    if sortie.exists():
        try:
            ancien = json.loads(sortie.read_text('utf-8')).get('enseignes', {})
        except ValueError:
            ancien = {}
    enseignes = {}
    erreurs = 0
    for slug in SLUGS:
        try:
            enseignes[slug] = lire(slug)
        except Exception as e:  # garde l'ancienne version de l'enseigne
            erreurs += 1
            print(f'{slug} : {e}', file=sys.stderr)
            if slug in ancien:
                enseignes[slug] = ancien[slug]
        time.sleep(2)
    if erreurs == len(SLUGS):
        sys.exit('Bonial ne répond pas.')
    sortie.parent.mkdir(exist_ok=True)
    sortie.write_text(json.dumps({
        'maj': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'enseignes': enseignes,
    }, ensure_ascii=False, separators=(',', ':')), 'utf-8')
    print(f'{len(enseignes)} enseignes, {erreurs} erreur(s)')


main()
