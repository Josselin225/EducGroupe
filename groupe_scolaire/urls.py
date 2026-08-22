import os
import mimetypes
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from django.contrib import messages


@login_required
def media_protegee(request, chemin):
    """Sert les fichiers media uniquement aux utilisateurs authentifiés."""
    filepath = settings.MEDIA_ROOT / chemin
    if not filepath.exists() or not filepath.is_file():
        raise Http404("Fichier introuvable.")
    # Empêcher path traversal
    try:
        filepath.resolve().relative_to(settings.MEDIA_ROOT.resolve())
    except ValueError:
        raise Http404("Accès refusé.")
    content_type, _ = mimetypes.guess_type(str(filepath))
    return FileResponse(open(filepath, 'rb'), content_type=content_type or 'application/octet-stream')


@login_required
def profil(request):
    from eleves.models import UserProfile, GroupeScolaire
    from django.contrib.auth import get_user_model
    from django.contrib.auth.validators import UnicodeUsernameValidator
    from django.core.exceptions import ValidationError as DjValidationError
    from django.core.cache import cache
    User = get_user_model()

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    ctx = {
        'page_title': 'Mon profil', 'active': '',
        'pwd_success': False, 'pwd_error': None,
        'info_error': None, 'profile': profile,
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'photo':
            if 'photo' in request.FILES:
                if profile.photo:
                    profile.photo.delete(save=False)
                profile.photo = request.FILES['photo']
                profile.save()
                messages.success(request, 'Photo de profil mise à jour.')
            return redirect('/profil/')

        elif action == 'info':
            new_username = request.POST.get('username', '').strip()
            info_error = None

            if not new_username:
                info_error = "Le nom d'utilisateur ne peut pas être vide."
            elif User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
                info_error = "Ce nom d'utilisateur est déjà pris."
            else:
                try:
                    UnicodeUsernameValidator()(new_username)
                except DjValidationError as e:
                    info_error = e.messages[0]

            if info_error:
                ctx['info_error'] = info_error
            else:
                request.user.username = new_username
                request.user.first_name = request.POST.get('first_name', '').strip()
                request.user.last_name = request.POST.get('last_name', '').strip()
                request.user.email = request.POST.get('email', '').strip()
                request.user.save()
                profile.telephone = request.POST.get('telephone', '').strip()
                profile.poste = request.POST.get('poste', '').strip()
                profile.save()
                messages.success(request, 'Informations mises à jour.')
                return redirect('/profil/')

        elif action == 'support':
            if request.user.is_superuser or request.user.is_staff:
                groupe = GroupeScolaire.get()
                groupe.support_nom = request.POST.get('support_nom', '').strip()
                groupe.support_telephone = request.POST.get('support_telephone', '').strip()
                groupe.support_whatsapp = request.POST.get('support_whatsapp', '').strip()
                groupe.support_email = request.POST.get('support_email', '').strip()
                groupe.save()
                cache.delete('groupe_scolaire')
                messages.success(request, 'Coordonnées du support technique mises à jour.')
            return redirect('/profil/')

        elif action == 'password':
            actuel = request.POST.get('pwd_actuel', '')
            nouveau = request.POST.get('pwd_nouveau', '')
            confirm = request.POST.get('pwd_confirm', '')
            if not request.user.check_password(actuel):
                ctx['pwd_error'] = 'Mot de passe actuel incorrect.'
            elif nouveau != confirm:
                ctx['pwd_error'] = 'Les nouveaux mots de passe ne correspondent pas.'
            elif len(nouveau) < 8:
                ctx['pwd_error'] = 'Minimum 8 caractères requis.'
            else:
                request.user.set_password(nouveau)
                request.user.save()
                update_session_auth_hash(request, request.user)
                ctx['pwd_success'] = True

    return render(request, 'registration/profil.html', ctx)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dashboard/', RedirectView.as_view(url='/', permanent=False)),
    path('profil/', profil, name='profil'),
    path('', include('eleves.urls')),
    path('enseignants/', include('enseignants.urls')),
    path('emploi-du-temps/', include('emploi_du_temps.urls')),
    path('notes/', include('notes.urls')),
    path('presences/', include('presences.urls')),
    path('paiements/', include('paiements.urls')),
    path('rapports/', include('rapports.urls')),
] + [path('media/<path:chemin>', media_protegee, name='media_protegee')]
