import logging
import time
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.cache import patch_vary_headers

audit_log = logging.getLogger('edugroupe.audit')
security_log = logging.getLogger('edugroupe.security')

# Stockage en mémoire des tentatives de login (simple, sans dépendances)
_login_attempts = {}  # {ip: [timestamp, ...]}


class LoginRateLimitMiddleware:
    """Bloque les IPs après trop de tentatives de login échouées."""

    MAX_ATTEMPTS = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)
    BLOCK_DURATION = getattr(settings, 'LOGIN_BLOCK_DURATION', 300)
    LOGIN_PATH = '/accounts/login/'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self._get_ip(request)
        if request.path == self.LOGIN_PATH and self._est_bloque(ip):
            attente = self._temps_restant(ip)
            security_log.warning(f"LOGIN BLOQUÉ ip={ip} — trop de tentatives, {attente}s restantes")
            return redirect(f'{self.LOGIN_PATH}?bloque=1&attente={attente}')

        response = self.get_response(request)

        # Détecter un login échoué (page login rechargée avec erreur)
        if (request.method == 'POST'
                and request.path == self.LOGIN_PATH
                and response.status_code == 200
                and not request.user.is_authenticated):
            ip = self._get_ip(request)
            self._enregistrer_tentative(ip)
            attempts = self._compter_tentatives(ip)
            if attempts >= self.MAX_ATTEMPTS:
                security_log.warning(
                    f"BRUTE FORCE DÉTECTÉ ip={ip} — {attempts} tentatives, bloqué {self.BLOCK_DURATION}s"
                )

        return response

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '0.0.0.0')

    def _enregistrer_tentative(self, ip):
        now = time.time()
        if ip not in _login_attempts:
            _login_attempts[ip] = []
        _login_attempts[ip].append(now)
        # Nettoyer les anciennes tentatives
        _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < self.BLOCK_DURATION]

    def _compter_tentatives(self, ip):
        now = time.time()
        attempts = _login_attempts.get(ip, [])
        return len([t for t in attempts if now - t < self.BLOCK_DURATION])

    def _est_bloque(self, ip):
        return self._compter_tentatives(ip) >= self.MAX_ATTEMPTS

    def _temps_restant(self, ip):
        """Secondes avant la fin du blocage (basé sur la tentative la plus ancienne)."""
        now = time.time()
        attempts = _login_attempts.get(ip, [])
        recentes = [t for t in attempts if now - t < self.BLOCK_DURATION]
        if not recentes:
            return 0
        return max(0, int(min(recentes) + self.BLOCK_DURATION - now))


class AuditMiddleware:
    """Journalise toutes les actions (consultation, création, modification, suppression)
    de l'utilisateur connecté sur les pages de l'application dans le Journal d'activité."""

    PREFIXES_EXCLUS = ['/static/', '/media/', '/accounts/', '/admin/', '/favicon.ico']
    MOTS_SUPPRESSION = ['supprimer', 'desactiver', 'annuler']
    MOTS_CREATION = ['ajouter', 'creer', 'generer']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (request.user.is_authenticated
                and response.status_code in (200, 302)
                and not any(request.path.startswith(p) for p in self.PREFIXES_EXCLUS)):
            type_event = None
            if request.method == 'GET':
                type_event = 'consultation'
            elif request.method == 'POST':
                type_event = self._type_action(request.path)

            if type_event:
                audit_log.info(
                    f"user={request.user.username} type={type_event} "
                    f"method={request.method} path={request.path} status={response.status_code}"
                )
                from .models import ConnexionLog
                ConnexionLog.objects.create(
                    user=request.user,
                    username_tente=request.user.username,
                    type_event=type_event,
                    path=request.path,
                    ip=self._get_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
                )

        return response

    def _type_action(self, path):
        if any(mot in path for mot in self.MOTS_SUPPRESSION):
            return 'suppression'
        if any(mot in path for mot in self.MOTS_CREATION):
            return 'creation'
        return 'modification'

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '0.0.0.0')
