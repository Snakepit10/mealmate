import logging

import openfoodfacts

logger = logging.getLogger(__name__)


def get_product_by_barcode(barcode: str) -> dict | None:
    """
    Cerca un prodotto su Open Food Facts per barcode.
    Restituisce un dict con i dati del prodotto o None se non trovato.
    """
    try:
        api = openfoodfacts.API(
            user_agent="MealMate/1.0 (mealmate@example.com)",
            environment=openfoodfacts.Environment.org,
        )
        result = api.product.get(barcode)
        logger.info("OFF barcode %s → type=%s", barcode, type(result).__name__)

        if result is None:
            logger.info("OFF: risultato None per %s", barcode)
            return None

        # Formato dict
        if isinstance(result, dict):
            if result.get('status') == 1:
                # Formato grezzo OFF API: {status: 1, product: {...}}
                product = result['product']
            elif result.get('status') == 0:
                logger.info("OFF: prodotto non trovato per %s", barcode)
                return None
            elif 'product_name' in result or 'code' in result:
                # SDK v1.1 restituisce il dict del prodotto direttamente (senza wrapper status)
                product = result
            else:
                logger.warning("OFF: formato dict sconosciuto per %s, keys=%s", barcode, list(result.keys())[:15])
                return None

        # Formato oggetto (SDK che restituisce Product direttamente)
        elif hasattr(result, 'product_name') or hasattr(result, '__dict__'):
            product = result
        else:
            logger.warning("OFF: formato risposta sconosciuto per %s: %s", barcode, result)
            return None

        # Estrai i campi in modo compatibile con dict e oggetti
        def _get(obj, *keys):
            for key in keys:
                val = obj.get(key, '') if isinstance(obj, dict) else getattr(obj, key, '')
                if val:
                    return val
            return ''

        name = _get(product, 'product_name', 'product_name_it', 'product_name_en')
        brand = _get(product, 'brands')
        image_url = _get(product, 'image_front_url', 'image_url')
        nutriscore = _get(product, 'nutriscore_grade')
        categories_raw = _get(product, 'categories')
        category_name = categories_raw.split(',')[0].strip() if categories_raw else ''

        if not name:
            logger.info("OFF: nome vuoto per %s, skip", barcode)
            return None

        return {
            'name': name,
            'brand': brand,
            'barcode': barcode,
            'off_id': barcode,
            'image_url': image_url,
            'nutriscore': nutriscore.upper() if nutriscore else None,
            'category_name': category_name,
            'source': 'open_food_facts',
        }

    except Exception as e:
        logger.error("OFF API errore per %s: %s", barcode, e, exc_info=True)
        return None
