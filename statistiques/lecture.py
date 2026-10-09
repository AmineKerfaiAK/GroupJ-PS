import os


class Instance:
    pass


def lire_instance(chemin):
    with open(chemin, "rb") as f:
        d = f.read().split()
    it = iter(map(int, d))
    i = Instance()
    i.nom = os.path.splitext(os.path.basename(chemin))[0]
    i.V, i.E, i.R, i.C, i.X = (next(it) for _ in range(5))
    i.taille = [next(it) for _ in range(i.V)]
    i.Ld = []
    i.liens = []
    for _ in range(i.E):
        ld, k = next(it), next(it)
        i.Ld.append(ld)
        i.liens.append({next(it): next(it) for _ in range(k)})
    i.req = [(next(it), next(it), next(it)) for _ in range(i.R)]
    return i


def lire_solution(chemin, inst):
    contenu = [set() for _ in range(inst.C)]
    with open(chemin) as f:
        lignes = [l.split() for l in f.read().strip().split("\n") if l.strip()]
    if not lignes:
        raise ValueError("empty solution")
    n = int(lignes[0][0])
    for l in lignes[1:n + 1]:
        c = int(l[0])
        contenu[c] = set(map(int, l[1:]))
    return contenu


def borne_superieure(inst):
    meilleur = [min(l.values()) if l else None for l in inst.liens]
    tot = nb = 0
    for v, e, n in inst.req:
        m = meilleur[e]
        if m is not None and inst.taille[v] <= inst.X and m < inst.Ld[e]:
            tot += n * (inst.Ld[e] - m)
        nb += n
    return tot * 1000 // nb if nb else 0


def dossier_sortie(nom, sous):
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sorties", nom, sous)
    os.makedirs(d, exist_ok=True)
    return d


def plt_ou_rien():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        print("matplotlib missing: pip install matplotlib (no charts)")
        return None
