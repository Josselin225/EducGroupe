from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from eleves.permissions import acces_requis
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import TypeFrais, Facture, Paiement, EcheancePaiement, STATUT_PAIEMENT
from .forms import TypeFraisForm, FactureForm, PaiementForm, EcheanceForm, GenererEcheancierForm
from eleves.models import AnneeScolaire
from django.http import HttpResponse


def _render_pdf(template_name, context):
    """Génère un HttpResponse PDF à partir d'un template HTML."""
    from io import BytesIO
    from xhtml2pdf import pisa
    from django.template.loader import render_to_string
    html = render_to_string(template_name, context)
    buf = BytesIO()
    pisa.pisaDocument(BytesIO(html.encode('utf-8')), buf)
    buf.seek(0)
    return buf.read()


@transaction.atomic
def _numero_facture():
    """Génère un numéro de facture unique. Le bloc atomic évite les doublons en cas d'accès concurrent."""
    today = timezone.localdate()
    prefix = f"FAC-{today.year}{today.month:02d}"
    last = Facture.objects.filter(numero__startswith=prefix).order_by('-numero').first()
    if last:
        try:
            seq = int(last.numero.split('-')[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}-{seq:04d}"


@acces_requis("paiements")
def index(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    factures = Facture.objects.filter(annee_scolaire=annee) if annee else Facture.objects.none()
    stats = factures.aggregate(
        total_attendu=Sum('montant_total'),
        total_encaisse=Sum('montant_paye'),
    )
    context = {
        'annee': annee,
        'total_factures': factures.count(),
        'total_attendu': stats['total_attendu'] or 0,
        'total_encaisse': stats['total_encaisse'] or 0,
        'total_restant': (stats['total_attendu'] or 0) - (stats['total_encaisse'] or 0),
        'nb_en_attente': factures.filter(statut='en_attente').count(),
        'nb_partiel': factures.filter(statut='partiel').count(),
        'nb_paye': factures.filter(statut='paye').count(),
        'factures_recentes': factures.select_related('eleve', 'type_frais').order_by('-date_creation')[:5],
        'page_title': 'Paiements',
        'active': 'paiements',
    }
    return render(request, 'paiements/index.html', context)


# ──────────────────────────────────────────────
# TYPES DE FRAIS
# ──────────────────────────────────────────────

@acces_requis("paiements")
def types_frais_liste(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    types = TypeFrais.objects.filter(annee_scolaire=annee).annotate(
        nb_factures=Count('factures')
    ) if annee else []
    context = {'types': types, 'annee': annee, 'page_title': 'Types de frais', 'active': 'paiements'}
    return render(request, 'paiements/types_frais/liste.html', context)


@acces_requis("paiements")
def type_frais_ajouter(request):
    form = TypeFraisForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Type de frais ajouté.')
        return redirect('paiements:types_frais_liste')
    return render(request, 'paiements/types_frais/form.html',
                  {'form': form, 'page_title': 'Nouveau type de frais', 'active': 'paiements'})


@acces_requis("paiements")
def type_frais_modifier(request, pk):
    tf = get_object_or_404(TypeFrais, pk=pk)
    form = TypeFraisForm(request.POST or None, instance=tf)
    if form.is_valid():
        form.save()
        messages.success(request, 'Type de frais modifié.')
        return redirect('paiements:types_frais_liste')
    return render(request, 'paiements/types_frais/form.html',
                  {'form': form, 'type_frais': tf, 'page_title': f'Modifier — {tf.nom}', 'active': 'paiements'})


# ──────────────────────────────────────────────
# FACTURES
# ──────────────────────────────────────────────

@acces_requis("paiements")
def factures_liste(request):
    annee = AnneeScolaire.objects.filter(en_cours=True).first()
    factures = Facture.objects.select_related('eleve', 'type_frais').filter(annee_scolaire=annee) if annee else []
    statut_filtre = request.GET.get('statut')
    search = request.GET.get('q', '').strip()
    if statut_filtre:
        factures = factures.filter(statut=statut_filtre)
    if search:
        factures = factures.filter(
            Q(eleve__nom__icontains=search) | Q(eleve__prenom__icontains=search) |
            Q(numero__icontains=search)
        )
    paginator = Paginator(factures, 10)
    page = request.GET.get('page', 1)
    factures_page = paginator.get_page(page)
    context = {
        'factures': factures_page,
        'paginator': paginator,
        'eleves': factures_page,
        'annee': annee,
        'statuts': STATUT_PAIEMENT,
        'search': search,
        'page_title': 'Factures',
        'active': 'paiements',
    }
    return render(request, 'paiements/factures/liste.html', context)


@acces_requis("paiements")
def facture_ajouter(request):
    initial = {'numero': _numero_facture()}
    form = FactureForm(request.POST or None, initial=initial)
    if form.is_valid():
        form.save()
        messages.success(request, 'Facture créée.')
        return redirect('paiements:factures_liste')
    return render(request, 'paiements/factures/form.html',
                  {'form': form, 'page_title': 'Nouvelle facture', 'active': 'paiements'})


@acces_requis("paiements")
def facture_detail(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    paiements = facture.paiements.all().order_by('-date_paiement')
    form = PaiementForm(request.POST or None, initial={
        'date_paiement': timezone.localdate(),
        'montant': facture.solde_restant(),
    })
    if request.method == 'POST' and form.is_valid():
        paiement = form.save(commit=False)
        paiement.facture = facture
        paiement.recu_par = request.user
        paiement.save()
        messages.success(request, f'Paiement de {paiement.montant} FCFA enregistré.')
        return redirect('paiements:facture_detail', pk=pk)
    context = {
        'facture': facture,
        'paiements': paiements,
        'form': form,
        'page_title': f'Facture {facture.numero}',
        'active': 'paiements',
    }
    return render(request, 'paiements/factures/detail.html', context)


@acces_requis("paiements")
def facture_pdf(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    paiements = facture.paiements.all().order_by('-date_paiement')

    from eleves.context_processors import groupe_scolaire
    groupe_ctx = groupe_scolaire(request)

    context = {
        'facture': facture,
        'paiements': paiements,
        **groupe_ctx,
    }
    pdf_bytes = _render_pdf('paiements/factures/facture_pdf.html', context)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="facture_{facture.numero}.pdf"'
    return response


@acces_requis("paiements")
def echeancier_pdf(request, pk):
    facture = get_object_or_404(Facture, pk=pk)

    from eleves.context_processors import groupe_scolaire
    groupe_ctx = groupe_scolaire(request)

    context = {
        'facture': facture,
        **groupe_ctx,
    }
    pdf_bytes = _render_pdf('paiements/factures/echeancier_pdf.html', context)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="echeancier_{facture.numero}.pdf"'
    return response


@acces_requis("paiements")
def paiement_supprimer(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    facture_pk = paiement.facture.pk
    if request.method == 'POST':
        paiement.delete()
        facture = Facture.objects.get(pk=facture_pk)
        total = facture.paiements.aggregate(t=Sum('montant'))['t'] or Decimal('0')
        facture.montant_paye = total
        if total >= facture.montant_total:
            facture.statut = 'paye'
        elif total > 0:
            facture.statut = 'partiel'
        else:
            facture.statut = 'en_attente'
        facture.save()
        messages.success(request, 'Paiement supprimé.')
    return redirect('paiements:facture_detail', pk=facture_pk)


# ──────────────────────────────────────────────
# REÇU DE PAIEMENT
# ──────────────────────────────────────────────

@acces_requis("paiements")
def recu_paiement(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    facture = paiement.facture
    context = {
        'paiement': paiement,
        'facture': facture,
        'page_title': f'Reçu — {paiement.facture.numero}',
        'active': 'paiements',
    }
    return render(request, 'paiements/recu.html', context)


# ──────────────────────────────────────────────
# ÉCHÉANCIER
# ──────────────────────────────────────────────

@acces_requis("paiements")
def echeancier_generer(request, facture_pk):
    facture = get_object_or_404(Facture, pk=facture_pk)
    form = GenererEcheancierForm(request.POST or None)
    if form.is_valid():
        nb = form.cleaned_data['nb_tranches']
        date_debut = form.cleaned_data['date_premiere_tranche']
        solde = facture.solde_restant()
        montant_tranche = (solde / nb).quantize(Decimal('1'))
        reste = solde - (montant_tranche * nb)

        import calendar

        def add_months(d, months):
            month = d.month - 1 + months
            year = d.year + month // 12
            month = month % 12 + 1
            day = min(d.day, calendar.monthrange(year, month)[1])
            return d.replace(year=year, month=month, day=day)

        facture.echeances.all().delete()
        for i in range(nb):
            d = add_months(date_debut, i)
            montant = montant_tranche + (reste if i == nb - 1 else Decimal('0'))
            EcheancePaiement.objects.create(
                facture=facture, numero=i + 1,
                montant=montant, date_echeance=d
            )
        messages.success(request, f'Échéancier de {nb} tranches créé.')
        return redirect('paiements:facture_detail', pk=facture_pk)
    return render(request, 'paiements/echeancier_form.html', {
        'form': form, 'facture': facture,
        'solde_restant': facture.solde_restant(),
        'page_title': f'Échéancier — {facture.numero}', 'active': 'paiements'
    })


@acces_requis("paiements")
def echeance_payer(request, pk):
    echeance = get_object_or_404(EcheancePaiement, pk=pk)
    facture = echeance.facture
    if echeance.est_paye:
        messages.warning(request, 'Cette tranche est déjà payée.')
        return redirect('paiements:facture_detail', pk=facture.pk)
    form = PaiementForm(request.POST or None, initial={
        'date_paiement': timezone.localdate(),
        'montant': echeance.montant,
        'recu_numero': f"{facture.numero}-T{echeance.numero}",
    })
    if form.is_valid():
        paiement = form.save(commit=False)
        paiement.facture = facture
        paiement.recu_par = request.user
        paiement.save()
        echeance.paiement = paiement
        echeance.save()
        messages.success(request, f'Tranche {echeance.numero} payée — Reçu généré.')
        return redirect('paiements:recu_paiement', pk=paiement.pk)
    return render(request, 'paiements/echeance_payer.html', {
        'form': form, 'echeance': echeance, 'facture': facture,
        'page_title': f'Payer tranche {echeance.numero} — {facture.numero}', 'active': 'paiements'
    })
