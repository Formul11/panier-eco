"""Récupère les catalogues et offres nationaux des enseignes : Bonial
(France), kaufDA (Allemagne) et Tiendeo (Espagne).

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
# Pages nationales kaufDA (même liste que enseignesKaufda dans l'appli,
# champ « nationale »).
SLUGS_KAUFDA = [
    'Lidl', 'Aldi-Nord', 'Aldi-Sued', 'Edeka', 'Marktkauf', 'Kaufland',
    'REWE', 'Penny-Markt', 'Netto-Supermarkt', 'Netto-Marken-Discount',
    'Norma', 'Rossmann', 'Globus', 'Mueller',
]
# Tiendeo par pays (sitesTiendeo dans l'appli) : site, chemin des pages
# d'enseigne et du catalogue, et principales enseignes. En France et en
# Allemagne, seulement celles que Bonial et kaufDA n'ont pas.
TIENDEO = {
    'FR': ('www.tiendeo.fr', 'promotions-catalogues', 'Catalogues', [
        'aldi', 'auchan', 'picard', 'monoprix', 'netto', 'grand-frais',
        'franprix', 'biocoop', 'carrefour-market', 'e-leclerc', 'super-u',
        'intermarche', 'lidl', 'norma', 'match', 'carrefour']),
    'DE': ('www.tiendeo.de', 'angebote-prospekte', 'Kataloge', [
        'tegut', 'globus', 'famila', 'v-markt', 'real', 'mueller']),
    'ES': ('www.tiendeo.com', 'Folletos-Catalogos', 'Catalogos', [
        'lidl', 'aldi', 'carrefour', 'dia', 'alcampo', 'mercadona',
        'eroski', 'consum', 'hipercor', 'supercor', 'el-corte-ingles',
        'ahorramas', 'bm-supermercados', 'caprabo', 'condis', 'spar',
        'masymas', 'froiz', 'gadis', 'alimerka', 'hiperdino', 'family-cash',
        'coviran']),
    'IT': ('www.tiendeo.it', 'offerte-volantino', 'Cataloghi', [
        'lidl', 'conad', 'coop', 'esselunga', 'carrefour', 'eurospin',
        'penny', 'md', 'aldi', 'despar', 'pam', 'iper', 'famila', 'bennet',
        'unes', 'todis', 'tigre', 'crai', 'sigma', 'interspar']),
    'PT': ('www.tiendeo.pt', 'ofertas-catalogos', 'Catalogos', [
        'continente', 'pingo-doce', 'lidl', 'intermarche', 'aldi',
        'mercadona', 'minipreco', 'auchan', 'e-leclerc', 'spar']),
    'GB': ('www.tiendeo.co.uk', 'offers-catalogues', 'Catalogues', [
        'tesco', 'aldi', 'lidl', 'asda', 'sainsburys', 'morrisons',
        'iceland', 'co-op', 'marks-and-spencer', 'waitrose', 'farmfoods',
        'b-m', 'home-bargains']),
    'BE': ('www.tiendeo.be', 'depliant-catalogue', 'catalogues', [
        'delhaize', 'colruyt', 'carrefour', 'lidl', 'aldi', 'intermarche',
        'spar', 'okay', 'cora', 'match', 'albert-heijn']),
    'CH': ('www.tiendeo.ch', 'aktionen-angebote', 'kataloge', [
        'migros', 'coop', 'denner', 'aldi', 'lidl', 'spar', 'volg',
        'manor']),
    'AT': ('www.tiendeo.at', 'angebote-flugblatt', 'Kataloge', [
        'billa', 'spar', 'hofer', 'lidl', 'penny', 'merkur', 'interspar',
        'eurospar', 'mpreis', 'unimarkt']),
    'NL': ('www.tiendeo.nl', 'aanbiedingen-folders', 'Catalogi', [
        'albert-heijn', 'jumbo', 'lidl', 'aldi', 'plus', 'dirk', 'coop',
        'vomar', 'spar', 'hoogvliet', 'dekamarkt', 'poiesz']),
    'US': ('www.tiendeo.us', 'deals-catalogs', 'Catalogs', [
        'aldi', 'walmart', 'target', 'kroger', 'costco', 'publix',
        'safeway', 'lidl', 'food-lion', 'meijer', 'h-e-b', 'albertsons']),
    'BR': ('www.tiendeo.com.br', 'ofertas-catalogos', 'Catalogos', [
        'carrefour', 'atacadao', 'assai', 'pao-de-acucar', 'extra',
        'dia', 'big', 'tenda', 'tatico']),
}
LD = re.compile(
    r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.S)
NEXT = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.S)


def telecharger(url):
    requete = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; PanierEco/1.0)',
                 'Accept': 'text/html'})
    with urllib.request.urlopen(requete, timeout=30) as r:
        return r.read().decode('utf-8')


def lire(slug, site='https://www.bonial.fr/Enseignes/'):
    html = telecharger(site + slug)
    donnees = json.loads(NEXT.search(html).group(1))
    info = donnees['props']['pageProps']['pageInformation']
    brochures = info.get('brochures') or {}
    offres = (info.get('offers') or {}).get('main') or {}
    return {
        'brochures': {k: brochures.get(k) or [] for k in ('viewer', 'publisher')},
        'offers': {'main': {'items': offres.get('items') or []}},
    }


def lire_tiendeo(pays, slug):
    """Catalogues d'une page Tiendeo, au format des pages Bonial (comme
    donneesTiendeo dans l'appli)."""
    hote, enseignes, catalogue, _ = TIENDEO[pays]
    html = telecharger(f'https://{hote}/{enseignes}/{slug}')
    brochures = []
    for bloc in LD.findall(html):
        try:
            d = json.loads(bloc)
        except ValueError:
            continue
        if not isinstance(d, dict) or d.get('@type') != 'OfferCatalog':
            continue
        for e in d.get('itemListElement') or []:
            image = str(e.get('image') or '')
            m = re.search(r'(?:small|big)_(\d+)', image)
            if not m:
                continue
            brochures.append({
                'id': int(m.group(1)),
                'title': str(e.get('name') or '').strip(),
                'validFrom': e.get('startDate'),
                'validUntil': e.get('endDate'),
                'pageCount': 0,
                'pages': [{'url': {'normal': image}}],
                'publisher': {
                    'name': (e.get('organizer') or {}).get('name') or ''},
                'url': f'https://{hote}/{catalogue}/{m.group(1)}',
            })
    if not brochures:
        # Enseigne sans catalogue : pas gardée (fichier plus léger).
        raise LookupError('aucun catalogue')
    return {'brochures': {'publisher': brochures}}


def collecter(slugs, lecteur, ancien, nom):
    """Lit chaque page ; en cas d'échec, garde l'ancienne version."""
    pages = {}
    erreurs = 0
    for slug in slugs:
        try:
            pages[slug] = lecteur(slug)
        except Exception as e:
            erreurs += 1
            print(f'{nom} {slug} : {e}', file=sys.stderr)
            if slug in ancien:
                pages[slug] = ancien[slug]
        time.sleep(2)
    return pages, erreurs


def main():
    sortie = pathlib.Path('catalogues/bonial.json')
    ancien = {}
    if sortie.exists():
        try:
            ancien = json.loads(sortie.read_text('utf-8'))
        except ValueError:
            ancien = {}
    enseignes, e1 = collecter(
        SLUGS, lire, ancien.get('enseignes') or {}, 'Bonial')
    kaufda, e2 = collecter(
        SLUGS_KAUFDA,
        lambda slug: lire(slug, 'https://www.kaufda.de/Geschaefte/'),
        ancien.get('kaufda') or {}, 'kaufDA')
    tiendeo = {}
    e3 = 0
    ancien_tiendeo = ancien.get('tiendeo') or {}
    for pays, (_, _, _, slugs) in TIENDEO.items():
        pages, erreurs = collecter(
            slugs, lambda slug, pays=pays: lire_tiendeo(pays, slug),
            {} if not isinstance(ancien_tiendeo.get(pays), dict)
            else ancien_tiendeo[pays], f'Tiendeo {pays}')
        tiendeo[pays] = pages
        e3 += erreurs
    if e1 == len(SLUGS):
        sys.exit('Bonial ne répond pas.')
    sortie.parent.mkdir(exist_ok=True)
    sortie.write_text(json.dumps({
        'maj': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'enseignes': enseignes,
        'kaufda': kaufda,
        'tiendeo': tiendeo,
    }, ensure_ascii=False, separators=(',', ':')), 'utf-8')
    print(f'Bonial {len(enseignes)} ({e1} erreur(s)), '
          f'kaufDA {len(kaufda)} ({e2}), '
          f'Tiendeo {sum(len(v) for v in tiendeo.values())} ({e3})')


main()
