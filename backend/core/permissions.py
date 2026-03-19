from rest_framework.permissions import BasePermission


class IsFamilyMember(BasePermission):
    """
    Permette l'accesso solo ai membri della famiglia specificata nell'URL.
    Richiede che la view esponga `get_family()` o che family_id sia in kwargs.
    """
    message = 'Non sei membro di questa famiglia.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        family_id = view.kwargs.get('family_id') or view.kwargs.get('id')
        if not family_id:
            return False
        return request.user.family_memberships.filter(
            family_id=family_id
        ).exists()


class IsFamilyAdmin(BasePermission):
    """
    Permette l'accesso solo agli admin della famiglia.
    """
    message = 'Non sei admin di questa famiglia.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        family_id = view.kwargs.get('family_id') or view.kwargs.get('id')
        if not family_id:
            return False
        return request.user.family_memberships.filter(
            family_id=family_id,
            role='admin'
        ).exists()
