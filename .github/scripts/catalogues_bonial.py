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


# Produits de chaque catalogue (nom, prix, zone sur la page), lus sur le
# service de la visionneuse Bonial / kaufDA (accord de l'utilisateur,
# 2026-11-26). Un navigateur ne peut pas le lire depuis une autre adresse :
# l'appli web lit les fichiers catalogues/pages/<id>.json écrits ici.
VISIONNEUSE = {
    'enseignes': ('https://content-viewer-be.bonial.fr', 'bonial_web',
                  48.8566, 2.3522),
    'kaufda': ('https://content-viewer-be.kaufda.de', 'kaufda_web',
               52.52, 13.405),
}


def telecharger_json(url):
    requete = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; PanierEco/1.0)',
                 'Accept': 'application/json'})
    with urllib.request.urlopen(requete, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def produit(contenu):
    """Offre de la visionneuse → {n, p, u, img} (p : prix ou None)."""
    produits = contenu.get('products') or [{}]
    nom = str(produits[0].get('name') or '').strip()
    prix = None
    unite = ''
    for deal in contenu.get('deals') or []:
        valeur = deal.get('min')
        if isinstance(valeur, (int, float)) and valeur > 0 and (
                prix is None or valeur < prix):
            prix = round(float(valeur), 2)
            conditions = [str(c.get('other') or '')
                          for c in deal.get('conditions') or []]
            unite = ', '.join(x for x in conditions + [
                str(deal.get('priceByBaseUnit') or '')] if x)
    if not nom:
        return None
    image = str(contenu.get('image') or '')
    return {'n': nom, 'p': prix, 'u': unite,
            'img': image + ('?impolicy=SEO-offer-thumbnails' if image else '')}


def pages_catalogue(source, brochure):
    """Pages (image + produits et leur zone) ou rayons d'un catalogue."""
    hote, partenaire, lat, lng = VISIONNEUSE[source]
    ident = brochure['contentId']
    requete = f'partner={partenaire}&lat={lat}&lng={lng}'
    if brochure.get('type') == 'DYNAMIC':
        infos = telecharger_json(
            f'{hote}/v1/brochures/{ident}?{requete}')['content']
        rayons = []
        bannieres = []
        for section in infos.get('sections') or []:
            time.sleep(0.5)
            donnees = telecharger_json(
                f'{hote}/v1/brochures/{ident}/section/'
                f'{section.get("number", 0)}?{requete}')['content']
            contenus = [c.get('content') or {}
                        for bloc in donnees.get('blocks') or []
                        for c in bloc.get('contents') or []]
            produits = [p for c in contenus if c.get('type') == 'offer'
                        for p in [produit(c)] if p]
            bannieres += [c['image'] for c in contenus
                          if c.get('type') == 'image_banner' and c.get('image')]
            if produits:
                rayons.append({'nom': str(section.get('name') or ''),
                               'produits': produits})
        if not rayons and bannieres:
            # Catalogue fait seulement d'images : affichées comme des pages.
            return {'id': ident, 'titre': brochure.get('title') or '',
                    'pages': [{'img': b, 'grande': b, 'produits': []}
                              for b in bannieres]}
        return {'id': ident, 'titre': brochure.get('title') or '',
                'rayons': rayons}
    donnees = telecharger_json(
        f'{hote}/v1/brochures/{ident}/pages?{requete}')
    pages = []
    for page in donnees.get('contents') or []:
        images = {i.get('size'): i.get('url') for i in page.get('images') or []}
        produits = []
        for offre in page.get('offers') or []:
            contenu = offre.get('content') or {}
            zone = (((contenu.get('parentContent') or {}).get('page') or {})
                    .get('area') or {})
            p = produit(contenu)
            if not p or not zone:
                continue
            haut, bas = zone.get('topLeft') or {}, zone.get('bottomRight') or {}
            p['z'] = [round(float(haut.get('x', 0)), 4),
                      round(float(haut.get('y', 0)), 4),
                      round(float(bas.get('x', 1)), 4),
                      round(float(bas.get('y', 1)), 4)]
            produits.append(p)
        pages.append({
            'img': images.get('768x1024') or images.get('1600x1600') or '',
            'grande': images.get('1600x1600') or images.get('768x1024') or '',
            'produits': produits,
        })
    return {'id': ident, 'titre': brochure.get('title') or '', 'pages': pages}


def ecrire_pages(sources):
    """Écrit catalogues/pages/<id>.json pour chaque catalogue Bonial et
    kaufDA, et supprime ceux qui ne sont plus en cours."""
    dossier = pathlib.Path('catalogues/pages')
    dossier.mkdir(parents=True, exist_ok=True)
    gardes = set()
    erreurs = 0
    for source, enseignes in sources.items():
        for donnees in enseignes.values():
            brochures = donnees.get('brochures') or {}
            for brochure in (brochures.get('viewer') or []) + (
                    brochures.get('publisher') or []):
                ident = str(brochure.get('contentId') or '')
                if not re.fullmatch(r'[0-9a-f-]{20,}', ident) or ident in gardes:
                    continue
                gardes.add(ident)
                fichier = dossier / f'{ident}.json'
                try:
                    contenu = pages_catalogue(source, brochure)
                except Exception as e:
                    erreurs += 1
                    print(f'Pages {ident} : {e}', file=sys.stderr)
                    continue  # l'ancien fichier, s'il existe, est gardé
                fichier.write_text(json.dumps(
                    contenu, ensure_ascii=False, separators=(',', ':')), 'utf-8')
                time.sleep(1)
    for fichier in dossier.glob('*.json'):
        if fichier.stem not in gardes:
            fichier.unlink()
    print(f'Pages de catalogues : {len(gardes)} ({erreurs} erreur(s))')


# Tiendeo : pages et zones des produits, lues sur le service public de la
# visionneuse (publication_pages ; accord de l'utilisateur, 2026-11-26).
# Le nom et le prix ne sont publics que pour 50 produits par catalogue
# (page du catalogue) ; les autres zones restent touchables, l'appli
# montre alors le produit agrandi pour le saisir. Les fiches produits
# (viewer_api) sont protégées contre les robots : on ne les lit pas.
# France et Allemagne seulement (magasins de l'utilisateur), pour ne pas
# surcharger le service.
PAYS_PAGES_TIENDEO = ('FR', 'DE')
PUBLICATIONS = 'https://shopfully-publication-api.global.ssl.fastly.net/publication_pages'


def image_page(descripteurs, niveau):
    """Adresse https de l'image de page au niveau voulu (webp de préférence)."""
    for d in descripteurs:
        chemin = str((d.get('pageRepresentation') or {}).get('resourcePath') or '')
        if f'_level_{niveau}_' in chemin and chemin.endswith('.webp'):
            return 'https://' + chemin, d.get('width'), d.get('height')
    return None, None, None


def pages_tiendeo(url):
    html = telecharger(url)
    donnees = json.loads(NEXT.search(html).group(1))
    ressources = donnees['props']['pageProps']['apiResources']
    flyer = ressources.get('flyer') or {}
    m = re.search(r'/publication/([a-z]{2}_[a-z]{2})_(\d+)',
                  str(flyer.get('publication_url') or ''))
    if not m:
        raise LookupError('pas de publication')
    langue, numero = m.groups()
    connus = {}
    for g in (ressources.get('flyerGibsData') or {}).get('flyerGibs') or []:
        reglages = g.get('settings') or {}
        chiffres = str((reglages.get('price_extended') or {}).get('digits') or '')
        try:
            prix = round(float(chiffres.replace(',', '.')), 2) if chiffres else None
        except ValueError:
            prix = None
        connus[g.get('id')] = {'n': str(g.get('title') or '').strip(),
                               'p': prix if prix and prix > 0 else None}
    pages = {}
    zones = {}
    tranche = 1
    total = None
    while tranche < 40:
        lot = telecharger_json(f'{PUBLICATIONS}/{langue}/{numero}/{tranche}?format=all')
        if not isinstance(lot, dict) or not lot:
            break
        descripteur = lot.get('publicationDescriptor') or {}
        total = descripteur.get('numberOfPages') or total
        recues = {int(c): v for c, v in lot.items() if str(c).isdigit()}
        if not recues:
            break
        pages.update(recues)
        try:
            for cle, liste in telecharger_json(
                    f'{PUBLICATIONS}/{langue}/{numero}/enr/{tranche}').items():
                if str(cle).isdigit() and isinstance(liste, list):
                    zones.setdefault(int(cle), []).extend(liste)
        except Exception:
            pass  # tranche sans produits repérés
        if (total and len(pages) >= total) or len(recues) < 10:
            break
        tranche += 1
        time.sleep(0.5)
    sortie = []
    for numero_page in sorted(pages):
        descripteurs = pages[numero_page].get('pageRepresentationDescriptors') or []
        petite, largeur, hauteur = image_page(descripteurs, 3)
        grande, l4, h4 = image_page(descripteurs, 4)
        largeur, hauteur = l4 or largeur, h4 or hauteur
        produits = []
        for z in zones.get(numero_page, []):
            forme = z.get('crop_shape') or {}
            if not z.get('flyerGibType') or not forme:
                continue
            x, y = float(forme.get('x', 0)), float(forme.get('y', 0))
            w, h = float(forme.get('width', 0)), float(forme.get('height', 0))
            if w <= 0 or h <= 0:
                continue
            infos = connus.get(z.get('id')) or {'n': '', 'p': None}
            produits.append({
                'n': infos['n'], 'p': infos['p'], 'u': '', 'img': '',
                'z': [round(max(0, x), 4), round(max(0, y), 4),
                      round(min(1, x + w), 4), round(min(1, y + h), 4)],
            })
        sortie.append({
            'img': petite or grande or '', 'grande': grande or petite or '',
            'r': round(largeur / hauteur, 4) if largeur and hauteur else None,
            'produits': produits,
        })
    titre = str(flyer.get('title') or '')
    return {'id': str(flyer.get('id') or ''), 'titre': titre, 'pages': sortie}


def ecrire_pages_tiendeo(tiendeo):
    dossier = pathlib.Path('catalogues/tiendeo')
    dossier.mkdir(parents=True, exist_ok=True)
    gardes = set()
    erreurs = 0
    for pays in PAYS_PAGES_TIENDEO:
        for enseigne in (tiendeo.get(pays) or {}).values():
            for b in (enseigne.get('brochures') or {}).get('publisher') or []:
                ident = str(b.get('id') or '')
                url = str(b.get('url') or '')
                if not ident.isdigit() or not url.startswith('https://') or ident in gardes:
                    continue
                gardes.add(ident)
                try:
                    contenu = pages_tiendeo(url)
                except Exception as e:
                    erreurs += 1
                    print(f'Tiendeo pages {ident} : {e}', file=sys.stderr)
                    continue
                if contenu['pages']:
                    (dossier / f'{ident}.json').write_text(json.dumps(
                        contenu, ensure_ascii=False, separators=(',', ':')), 'utf-8')
                time.sleep(1)
    for fichier in dossier.glob('*.json'):
        if fichier.stem not in gardes:
            fichier.unlink()
    print(f'Pages Tiendeo : {len(gardes)} ({erreurs} erreur(s))')


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
    ecrire_pages({'enseignes': enseignes, 'kaufda': kaufda})
    ecrire_pages_tiendeo(tiendeo)


if __name__ == '__main__':
    main()
