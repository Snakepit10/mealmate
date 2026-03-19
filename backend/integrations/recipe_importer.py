def import_from_url(url: str) -> dict:
    """
    Importa una ricetta da un URL esterno.
    L'API esterna verrà collegata in seguito.

    Returns:
        dict con i dati estratti della ricetta, oppure
        {"success": False, "url": url} in caso di fallimento totale.
    """
    # TODO: collegare API esterna quando disponibile
    raise NotImplementedError("L'API di importazione ricette non è ancora configurata.")
