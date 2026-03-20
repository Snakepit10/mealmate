import json
import logging
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Linux; Android 10; Mobile) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'
    ),
    'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
_TIMEOUT = 10


def import_from_url(url: str) -> dict:
    """
    Scarica la pagina, estrae il JSON-LD schema.org/Recipe e lo normalizza.
    Funziona con GialloZafferano, Cookpad, BBC Good Food e qualsiasi sito
    che usa lo standard schema.org/Recipe.
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.warning('recipe_importer: request failed for %s: %s', url, exc)
        raise

    soup = BeautifulSoup(resp.text, 'html.parser')
    recipe_ld = _extract_recipe_jsonld(soup)
    if not recipe_ld:
        logger.warning('recipe_importer: no schema.org/Recipe found at %s', url)
        raise ValueError('Nessun dato schema.org/Recipe trovato su {}'.format(url))

    result = _normalise(recipe_ld, source_url=url)
    logger.info(
        'recipe_importer: imported "%s" (%d ingredients, %d steps) from %s',
        result['title'], len(result['ingredients']), len(result['steps']), url,
    )
    return result


def _extract_recipe_jsonld(soup):
    for tag in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(tag.string or '')
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict):
            if _is_recipe_type(data.get('@type')):
                return data
            for node in data.get('@graph', []):
                if isinstance(node, dict) and _is_recipe_type(node.get('@type')):
                    return node
        if isinstance(data, list):
            for node in data:
                if isinstance(node, dict) and _is_recipe_type(node.get('@type')):
                    return node
    return None


def _is_recipe_type(t):
    if isinstance(t, str):
        return 'recipe' in t.lower()
    if isinstance(t, list):
        return any('recipe' in x.lower() for x in t if isinstance(x, str))
    return False


def _normalise(ld, source_url):
    return {
        'success':     True,
        'title':       _s(ld.get('name', '')),
        'description': _s(ld.get('description', '')),
        'servings':    _parse_servings(ld.get('recipeYield')),
        'prep_time':   _parse_duration(ld.get('prepTime')),
        'cook_time':   _parse_duration(ld.get('cookTime')),
        'ingredients': _parse_ingredients(ld.get('recipeIngredient', [])),
        'steps':       _parse_steps(ld.get('recipeInstructions', [])),
        'image_url':   _parse_image(ld.get('image')),
        'source_url':  source_url,
    }


def _s(v):
    """Stringa pulita da tag HTML e spazi multipli."""
    if v is None:
        return ''
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', str(v))).strip()


def _parse_duration(v):
    """ISO 8601 duration -> minuti interi."""
    if not v:
        return None
    m = re.match(r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', str(v).upper())
    if not m:
        return None
    d, h, mn, s = (int(x or 0) for x in m.groups())
    return (d * 1440 + h * 60 + mn + s // 60) or None


def _parse_servings(v):
    if v is None:
        return None
    if isinstance(v, list):
        v = v[0] if v else ''
    m = re.search(r'\d+', str(v))
    return int(m.group()) if m else None


def _parse_ingredients(v):
    if not isinstance(v, list):
        return []
    return [_s(i) for i in v if _s(i)]


def _parse_steps(v):
    if not v:
        return []
    if isinstance(v, str):
        return [v.strip()] if v.strip() else []
    steps = []
    for item in v:
        if isinstance(item, str):
            if item.strip():
                steps.append(item.strip())
        elif isinstance(item, dict):
            if 'HowToSection' in item.get('@type', ''):
                for sub in item.get('itemListElement', []):
                    t = _s(sub.get('text', '') if isinstance(sub, dict) else sub)
                    if t:
                        steps.append(t)
            else:
                t = _s(item.get('text', ''))
                if t:
                    steps.append(t)
    return steps


def _parse_image(v):
    if not v:
        return ''
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return _parse_image(v[0]) if v else ''
    if isinstance(v, dict):
        return _s(v.get('url', ''))
    return ''
