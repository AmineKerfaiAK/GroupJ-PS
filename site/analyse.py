import math
import os
import sys
import random
from collections import Counter, defaultdict

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "statistiques"))
sys.path.insert(0, os.path.join(RACINE, "generateur"))

from lecture import lire_instance, borne_superieure
from stats_instance import calculer
from stats_solution import analyser

_cache = {}


def memo(cle, mtime, fn):
    if cle in _cache and _cache[cle][0] == mtime:
        return _cache[cle][1]
    val = fn()
    if len(_cache) > 12:
        _cache.pop(next(iter(_cache)))
    _cache[cle] = (mtime, val)
    return val


def instance(chemin):
    return memo(("inst", chemin), os.path.getmtime(chemin), lambda: lire_instance(chemin))


def nombre(x):
    return f"{int(x):,}" if float(x).is_integer() else f"{x:,.1f}"


def hist(valeurs, bins=20, poids=None):
    if not valeurs:
        return {"labels": [], "counts": []}
    lo, hi = min(valeurs), max(valeurs)
    entiers = all(isinstance(x, int) for x in valeurs)
    if entiers and hi - lo + 1 <= 25:
        counts = [0] * (hi - lo + 1)
        for k, x in enumerate(valeurs):
            counts[x - lo] += poids[k] if poids else 1
        return {"labels": [nombre(lo + b) for b in range(hi - lo + 1)], "counts": counts}
    brut = max((hi - lo) / bins, 1e-9)
    ordre = 10 ** math.floor(math.log10(brut))
    pas = ordre * 10
    for m in ((1, 2, 5, 10) if entiers else (1, 2, 2.5, 5, 10)):
        if m * ordre >= brut:
            pas = m * ordre
            break
    if entiers:
        pas = max(1, int(round(pas)))
    debut = math.floor(lo / pas) * pas
    n = int((hi - debut) // pas) + 1
    counts = [0] * n
    for k, x in enumerate(valeurs):
        counts[min(n - 1, int((x - debut) // pas))] += poids[k] if poids else 1
    labels = [f"{nombre(debut + b * pas)}\u2013{nombre(debut + (b + 1) * pas)}" for b in range(n)]
    return {"labels": labels, "counts": counts}


def echantillon_graphe(i, maxi=25):
    rng = random.Random(0)
    endpoints = list(range(i.E)) if i.E <= maxi else sorted(rng.sample(range(i.E), maxi))
    caches = sorted({c for e in endpoints for c in i.liens[e]})
    return {
        "endpoints": [{"id": e, "ld": i.Ld[e]} for e in endpoints],
        "caches": caches,
        "liens": [{"e": e, "c": c, "lc": lc} for e in endpoints for c, lc in i.liens[e].items()],
        "echantillon": len(endpoints) < i.E,
    }


def stats_instance(chemin):
    def calc():
        i = instance(chemin)
        s, demandes, par_endpoint, gains, deg_cache = calculer(i)
        tri = sorted(demandes.values(), reverse=True)
        pas = max(1, len(tri) // 300)
        return {
            "nom": i.nom, "V": i.V, "E": i.E, "R": i.R, "C": i.C, "X": i.X,
            "sections": [{"titre": t, "lignes": [[k, str(v)] for k, v in l]} for t, l in s.items()],
            "tailles": hist(i.taille),
            "capacite": {"demandee": sum(i.taille[v] for v in demandes), "totale": i.C * i.X},
            "caches_par_endpoint": hist([len(l) for l in i.liens], bins=max(1, min(30, max(len(l) for l in i.liens) + 1))),
            "endpoints_par_cache": hist([deg_cache[c] for c in range(i.C)]),
            "ld": hist(i.Ld),
            "gains": hist(gains),
            "popularite": [[k + 1, tri[k]] for k in range(0, len(tri), pas)],
            "par_endpoint": hist(list(par_endpoint.values())),
            "graphe": echantillon_graphe(i),
            "borne": borne_superieure(i),
        }
    return memo(("stats", chemin), os.path.getmtime(chemin), calc)


def lire_sortie(chemin, i):
    with open(chemin) as f:
        lignes = [l.split() for l in f.read().strip().split("\n") if l.strip()]
    if not lignes:
        raise ValueError("empty output: the program wrote nothing")
    n = int(lignes[0][0])
    if not 0 <= n <= i.C:
        raise ValueError(f"N={n} outside [0,C]")
    contenu = [set() for _ in range(i.C)]
    ordre = []
    vus = set()
    for l in lignes[1:n + 1]:
        c = int(l[0])
        if not 0 <= c < i.C:
            raise ValueError(f"cache {c} does not exist")
        if c in vus:
            raise ValueError(f"cache {c} described twice")
        vus.add(c)
        for v in map(int, l[1:]):
            if not 0 <= v < i.V:
                raise ValueError(f"video {v} does not exist")
            if v in contenu[c]:
                raise ValueError(f"video {v} twice in cache {c}")
            contenu[c].add(v)
            ordre.append((c, v))
    return contenu, ordre


def score_rapide(chemin_inst, chemin_sortie):
    i = instance(chemin_inst)
    contenu, _ = lire_sortie(chemin_sortie, i)
    r = analyser(i, contenu)
    return {"score": r["score"], "borne": r["borne"], "valide": not r["erreurs"], "erreurs": r["erreurs"][:5]}


def stats_solution(chemin_inst, chemin_sortie):
    def calc():
        i = instance(chemin_inst)
        try:
            contenu, ordre = lire_sortie(chemin_sortie, i)
        except Exception as ex:
            return {"erreur": str(ex)}
        r = analyser(i, contenu)
        taux = [round(100 * p / i.X, 1) for p in r["plein"]]
        av = sorted(r["lat_avant"])
        ap = sorted(r["lat_apres"])
        tous = av + ap
        lo, hi = min(tous), max(tous)
        def h(cpt):
            vals = sorted(cpt)
            return hist(vals + [lo, hi], poids=[cpt[k] for k in vals] + [0, 0])
        top_paires = sorted(r["gain_paire"].items(), key=lambda x: -x[1])[:15]
        return {
            "nom": i.nom, "C": i.C, "X": i.X,
            "valide": not r["erreurs"], "erreurs": r["erreurs"][:5],
            "score": r["score"], "borne": r["borne"],
            "utilises": sum(1 for p in r["plein"] if p > 0),
            "remplissage_moyen": round(sum(taux) / len(taux), 1),
            "copies": r["copies"], "distinctes": r["distinctes"], "inutiles": r["inutiles"],
            "servies": round(100 * r["servies"] / max(1, r["nb"]), 1),
            "lat_avant": round(r["moy_avant"], 1), "lat_apres": round(r["moy_apres"], 1),
            "taux_tries": sorted(taux, reverse=True),
            "gain_cache": [r["gain_cache"].get(c, 0) for c in range(i.C)],
            "hist_avant": h(r["lat_avant"]), "hist_apres": h(r["lat_apres"]),
            "top_videos": [[v, g] for v, g in r["gain_video"].most_common(20)],
            "top_paires": [{"cache": c, "video": v, "taille": i.taille[v], "gain": g} for (c, v), g in top_paires],
            "replay": rejouer(i, ordre),
            "bilan": bilan(i, contenu, r),
        }
    cle = ("sol", chemin_inst, chemin_sortie)
    return memo(cle, (os.path.getmtime(chemin_inst), os.path.getmtime(chemin_sortie)), calc)


def rejouer(i, ordre, max_images=400):
    lat_cache = [dict() for _ in range(i.C)]
    for e in range(i.E):
        for c, lc in i.liens[e].items():
            lat_cache[c][e] = lc
    par_video = defaultdict(list)
    attente = []
    nb = 0
    somme_ld = 0
    for k, (v, e, n) in enumerate(i.req):
        par_video[v].append(k)
        attente.append(i.Ld[e])
        nb += n
        somme_ld += n * i.Ld[e]

    def gain_initial(c, v):
        return sum(i.req[k][2] * (i.Ld[i.req[k][1]] - lat_cache[c][i.req[k][1]])
                   for k in par_video[v] if i.req[k][1] in lat_cache[c])

    ordre = sorted(ordre, key=lambda p: -gain_initial(*p) / i.taille[p[1]])
    total = len(ordre)
    pas = max(1, -(-total // max_images))
    plein = [0] * i.C
    gagne = 0
    images = [{"etape": 0, "score": 0, "plein": plein[:], "evt": None}]
    complet = pas == 1
    for k, (c, v) in enumerate(ordre):
        g = 0
        for idx in par_video[v]:
            e = i.req[idx][1]
            lc = lat_cache[c].get(e)
            if lc is not None and attente[idx] > lc:
                g += i.req[idx][2] * (attente[idx] - lc)
                attente[idx] = lc
        gagne += g
        plein[c] += i.taille[v]
        if (k + 1) % pas == 0 or k + 1 == total:
            images.append({"etape": k + 1, "score": gagne * 1000 // max(1, nb), "plein": plein[:],
                           "evt": {"cache": c, "video": v, "taille": i.taille[v], "gain": g}})
    res = {"images": images, "total": total, "complet": complet, "X": i.X, "C": i.C,
           "lat_moyenne_dc": somme_ld / max(1, nb)}
    if complet and i.E <= 30 and i.C <= 30 and i.R <= 300:
        res["petit"] = {
            "ordre": ordre,
            "taille": i.taille,
            "ld": i.Ld,
            "liens": [{"e": e, "c": c, "lc": lc} for e in range(i.E) for c, lc in i.liens[e].items()],
            "requetes": i.req,
        }
    return res


def bilan(i, contenu, r):
    nb = max(1, r["nb"])
    depuis_cache = dc_possible = dc_impossible = 0
    perdu_absent = perdu_lent = 0
    pertes = {}
    plus_rapide = [min(l.items(), key=lambda x: x[1]) if l else (None, None) for l in i.liens]
    ou = defaultdict(list)
    for c in range(i.C):
        for v in contenu[c]:
            ou[v].append(c)
    for v, e, n in i.req:
        ld = i.Ld[e]
        possible, meilleur_c = ld, None
        fc, fl = plus_rapide[e]
        if fc is not None and i.taille[v] <= i.X and fl < ld:
            possible, meilleur_c = fl, fc
        obtenu = ld
        liens = i.liens[e]
        for c in ou.get(v, ()):
            lc = liens.get(c)
            if lc is not None and lc < obtenu:
                obtenu = lc
        if obtenu < ld:
            depuis_cache += n
        elif possible < ld:
            dc_possible += n
        else:
            dc_impossible += n
        perte = n * (obtenu - possible)
        if perte > 0:
            if obtenu == ld:
                perdu_absent += perte
            else:
                perdu_lent += perte
            cle = (e, v)
            p = pertes.get(cle)
            if p is None:
                pertes[cle] = [perte, n, obtenu, possible, meilleur_c]
            else:
                p[0] += perte
                p[1] += n
    utile = [0] * i.C
    inutile = [0] * i.C
    for c in range(i.C):
        for v in contenu[c]:
            if r["gain_paire"].get((c, v), 0) > 0:
                utile[c] += i.taille[v]
            else:
                inutile[c] += i.taille[v]
    total_gain = sum(r["gain_paire"].values())
    top = sorted(r["gain_paire"].items(), key=lambda x: -x[1])[:10]
    pires = sorted(pertes.items(), key=lambda x: -x[1][0])[:6]
    return {
        "espace": {"utile": sum(utile), "inutile": sum(inutile), "vide": i.C * i.X - sum(utile) - sum(inutile),
                   "par_cache": [[utile[c], inutile[c]] for c in range(i.C)]},
        "requetes": {"cache": depuis_cache, "dc_possible": dc_possible, "dc_impossible": dc_impossible},
        "perdu": {"absent": perdu_absent * 1000 // nb, "lent": perdu_lent * 1000 // nb},
        "pires": [{"e": e, "v": v, "perte": p[0] * 1000 // nb, "n": p[1], "obtenu": p[2], "possible": p[3],
                   "cache": p[4], "taille": i.taille[v], "ld": i.Ld[e]} for (e, v), p in pires],
        "top": [{"c": c, "v": v, "gain": g * 1000 // nb, "taille": i.taille[v]} for (c, v), g in top],
        "part_top": round(100 * sum(g for _, g in top) / total_gain, 1) if total_gain else 0,
    }
