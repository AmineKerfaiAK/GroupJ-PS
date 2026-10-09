import argparse
import os
import random

LIM = dict(V=10000, E=1000, R=1000000, C=1000, X=500000, S=1000,
           LD_MIN=2, LD_MAX=4000, LC_MAX=500, RN=10000)


class Instance:
    def __init__(self, C, X, tailles):
        self.C = C
        self.X = X
        self.tailles = tailles
        self.endpoints = []
        self.requetes = []

    def ajouter_endpoint(self, ld, liens):
        self.endpoints.append((ld, liens))

    def ajouter_requete(self, v, e, n):
        self.requetes.append((v, e, min(LIM["RN"], max(1, n))))

    def texte(self):
        if not self.requetes:
            self.ajouter_requete(0, 0, 1)
        lignes = [f"{len(self.tailles)} {len(self.endpoints)} {len(self.requetes)} {self.C} {self.X}",
                  " ".join(map(str, self.tailles))]
        for ld, liens in self.endpoints:
            lignes.append(f"{ld} {len(liens)}")
            lignes += [f"{c} {l}" for c, l in liens]
        lignes += [f"{v} {e} {n}" for v, e, n in self.requetes]
        return "\n".join(lignes) + "\n"


def liens_aleatoires(rng, caches, k, ld, lc_min=1, lc_max=LIM["LC_MAX"]):
    choisis = rng.sample(caches, min(k, len(caches)))
    haut = max(1, min(lc_max, ld - 1))
    bas = min(lc_min, haut)
    return [(c, rng.randint(bas, haut)) for c in choisis]


def tirage_zipf(rng, ordre, a, k):
    poids = [1.0 / (r + 1) ** a for r in range(len(ordre))]
    return rng.choices(ordre, weights=poids, k=k)


def aleatoire(rng, V, E, R, C, X, smin, smax, kmax, **_):
    inst = Instance(C, X, [rng.randint(smin, smax) for _ in range(V)])
    for _ in range(E):
        ld = rng.randint(LIM["LD_MIN"], LIM["LD_MAX"])
        inst.ajouter_endpoint(ld, liens_aleatoires(rng, list(range(C)), rng.randint(0, kmax), ld))
    for _ in range(R):
        inst.ajouter_requete(rng.randrange(V), rng.randrange(E), rng.randint(1, LIM["RN"]))
    return inst


def zipf(rng, V, E, R, C, X, smin, smax, kmax, a, **_):
    inst = Instance(C, X, [rng.randint(smin, smax) for _ in range(V)])
    for _ in range(E):
        ld = rng.randint(500, LIM["LD_MAX"])
        inst.ajouter_endpoint(ld, liens_aleatoires(rng, list(range(C)), rng.randint(1, kmax), ld))
    ordre = list(range(V))
    rng.shuffle(ordre)
    videos = tirage_zipf(rng, ordre, a, R)
    for v in videos:
        inst.ajouter_requete(v, rng.randrange(E), rng.randint(1, 1000))
    return inst


def regional(rng, V, E, R, C, X, smin, smax, kmax, a, G, **_):
    inst = Instance(C, X, [rng.randint(smin, smax) for _ in range(V)])
    caches_region = [list(range(g, C, G)) for g in range(G)]
    region = [rng.randrange(G) for _ in range(E)]
    for e in range(E):
        ld = rng.randint(1000, LIM["LD_MAX"])
        liens = liens_aleatoires(rng, caches_region[region[e]], rng.randint(1, kmax), ld, 1, 100)
        autres = [c for c in range(C) if c not in dict(liens)]
        if autres and rng.random() < 0.3:
            liens += liens_aleatoires(rng, autres, 1, ld, 300, LIM["LC_MAX"])
        inst.ajouter_endpoint(ld, liens)
    gouts = []
    for _ in range(G):
        ordre = list(range(V))
        rng.shuffle(ordre)
        gouts.append(ordre)
    par_region = [[e for e in range(E) if region[e] == g] for g in range(G)]
    for _ in range(R):
        g = rng.randrange(G)
        if not par_region[g]:
            continue
        v = tirage_zipf(rng, gouts[g], a, 1)[0]
        inst.ajouter_requete(v, rng.choice(par_region[g]), rng.randint(1, 1000))
    return inst


def dejavu(rng, V, E, R, C, X, smin, smax, **_):
    inst = Instance(C, X, [rng.randint(smin, smax) for _ in range(V)])
    connexions = min(4, C)
    par_endpoint = max(1, R // E)
    for e in range(E):
        ld = rng.randint(LIM["LD_MIN"] + 1, 1000)
        inst.ajouter_endpoint(ld, liens_aleatoires(rng, list(range(C)), connexions, ld))
        noyau = [rng.randrange(V) for _ in range(max(1, int(0.075 * par_endpoint)))]
        for _ in range(int(par_endpoint * rng.uniform(0.9, 1.1))):
            inst.ajouter_requete(rng.choice(noyau), e, rng.randint(2, LIM["RN"]))
    return inst


def geant(rng, V, E, R, C, X, kmax, **_):
    tailles = [rng.randint(max(1, X // 2), min(LIM["S"], X + X // 4)) for _ in range(V)]
    inst = Instance(C, X, tailles)
    for _ in range(E):
        ld = rng.randint(LIM["LD_MIN"], LIM["LD_MAX"])
        inst.ajouter_endpoint(ld, liens_aleatoires(rng, list(range(C)), rng.randint(1, kmax), ld))
    for _ in range(R):
        inst.ajouter_requete(rng.randrange(V), rng.randrange(E), rng.randint(1, LIM["RN"]))
    return inst


def piege_sac(rng, C, X, **_):
    petit = X // 2 + 1
    inst = Instance(C, X, [])
    for c in range(C):
        inst.tailles += [petit, X]
        inst.ajouter_endpoint(1000, [(c, 1)])
        inst.ajouter_requete(2 * c, c, 6000)
        inst.ajouter_requete(2 * c + 1, c, 10000)
    return inst


def limite(rng, variante, **_):
    if variante == "single":
        inst = Instance(1, 1, [1])
        inst.ajouter_endpoint(2, [(0, 1)])
        inst.ajouter_requete(0, 0, 1)
    elif variante == "no_cache":
        inst = Instance(5, 100, [rng.randint(1, 100) for _ in range(50)])
        for _ in range(20):
            inst.ajouter_endpoint(rng.randint(2, 4000), [])
        for _ in range(200):
            inst.ajouter_requete(rng.randrange(50), rng.randrange(20), rng.randint(1, 10000))
    elif variante == "too_big":
        inst = Instance(10, 100, [rng.randint(101, 1000) for _ in range(100)])
        for _ in range(30):
            ld = rng.randint(100, 4000)
            inst.ajouter_endpoint(ld, liens_aleatoires(rng, list(range(10)), 3, ld))
        for _ in range(300):
            inst.ajouter_requete(rng.randrange(100), rng.randrange(30), rng.randint(1, 10000))
    elif variante == "exact_fit":
        inst = Instance(1, 100, [25, 25, 25, 25])
        inst.ajouter_endpoint(1000, [(0, 10)])
        for v in range(4):
            inst.ajouter_requete(v, 0, 10000)
    elif variante == "maximum":
        inst = Instance(LIM["C"], LIM["X"], [LIM["S"]] * 100)
        inst.ajouter_endpoint(LIM["LD_MAX"], [(c, LIM["LC_MAX"]) for c in range(LIM["C"])])
        for v in range(100):
            inst.ajouter_requete(v, 0, LIM["RN"])
    else:
        raise SystemExit("unknown variant: " + variante)
    return inst


UTILISES = dict(
    random=["V", "E", "R", "C", "X", "smin", "smax", "kmax"],
    zipf=["V", "E", "R", "C", "X", "smin", "smax", "kmax"],
    regional=["V", "E", "R", "C", "X", "smin", "smax", "kmax", "G"],
    dejavu=["V", "E", "R", "C", "X", "smin", "smax"],
    giant=["V", "E", "R", "C", "X", "kmax"],
    knapsack_trap=["C", "X"],
    edge=[],
)

BORNES = dict(V=(1, LIM["V"], "Videos"), E=(1, LIM["E"], "Endpoints"), R=(1, LIM["R"], "Requests"),
              C=(1, LIM["C"], "Caches"), X=(1, LIM["X"], "Cache size"), smin=(1, LIM["S"], "Min video size"),
              smax=(1, LIM["S"], "Max video size"), kmax=(1, LIM["C"], "Caches per endpoint"), G=(1, LIM["C"], "Regions"))


def verifier(type_, p):
    for k in UTILISES[type_]:
        lo, hi, nom = BORNES[k]
        v = p.get(k)
        if v is None or not lo <= v <= hi:
            raise ValueError(f"{nom} must be between {lo:,} and {hi:,} (you gave {v:,}).")
    if type_ in ("random", "zipf", "regional", "dejavu") and p["smin"] > p["smax"]:
        raise ValueError("Min video size must not be bigger than Max video size.")
    if type_ == "knapsack_trap" and p["X"] > LIM["S"]:
        raise ValueError(f"For knapsack_trap, Cache size must be at most {LIM['S']:,}, because one video is as big as a cache.")
    if type_ == "regional" and p["G"] > p["C"]:
        raise ValueError("Regions must not be more than Caches.")


TYPES = dict(random=aleatoire, zipf=zipf, regional=regional, dejavu=dejavu,
             giant=geant, knapsack_trap=piege_sac, edge=limite)

SUITE = [
    ("small_random", "random", dict(V=20, E=6, R=40, C=4, X=100, smin=5, smax=60, kmax=3)),
    ("random", "random", dict(V=2000, E=200, R=20000, C=50, X=5000, smin=1, smax=1000, kmax=10)),
    ("zipf", "zipf", dict(V=5000, E=300, R=50000, C=80, X=10000, smin=1, smax=800, kmax=8, a=1.1)),
    ("regional", "regional", dict(V=3000, E=400, R=40000, C=60, X=8000, smin=1, smax=800, kmax=5, a=1.0, G=6)),
    ("dejavu", "dejavu", dict(V=10000, E=115, R=100000, C=20, X=2000, smin=4, smax=110)),
    ("giant", "giant", dict(V=500, E=100, R=5000, C=30, X=600, kmax=6)),
    ("knapsack_trap", "knapsack_trap", dict(C=10, X=100)),
    ("edge_single", "edge", dict(variante="single")),
    ("edge_no_cache", "edge", dict(variante="no_cache")),
    ("edge_too_big", "edge", dict(variante="too_big")),
    ("edge_exact_fit", "edge", dict(variante="exact_fit")),
    ("edge_maximum", "edge", dict(variante="maximum")),
]


def ecrire(chemin, inst):
    dossier = os.path.dirname(chemin)
    if dossier:
        os.makedirs(dossier, exist_ok=True)
    with open(chemin, "w", newline="\n") as f:
        f.write(inst.texte())
    print(f"{chemin}  V={len(inst.tailles)} E={len(inst.endpoints)} R={len(inst.requetes)} C={inst.C} X={inst.X}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--type", choices=TYPES, default="random")
    p.add_argument("--suite", action="store_true")
    p.add_argument("-o", "--sortie", default="instances/generated")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--V", type=int, default=1000)
    p.add_argument("--E", type=int, default=100)
    p.add_argument("--R", type=int, default=10000)
    p.add_argument("--C", type=int, default=20)
    p.add_argument("--X", type=int, default=2000)
    p.add_argument("--smin", type=int, default=1)
    p.add_argument("--smax", type=int, default=1000)
    p.add_argument("--kmax", type=int, default=5)
    p.add_argument("--a", type=float, default=1.0)
    p.add_argument("--G", type=int, default=4)
    p.add_argument("--variante", default="single")
    args = vars(p.parse_args())
    suite = args.pop("suite")
    if not suite:
        try:
            verifier(args["type"], args)
        except ValueError as ex:
            raise SystemExit(str(ex))
    if suite:
        for nom, type_, params in SUITE:
            ecrire(os.path.join(args["sortie"], nom + ".in"), TYPES[type_](random.Random(args["seed"]), **params))
        return
    sortie = args.pop("sortie")
    if not sortie.endswith(".in"):
        sortie = os.path.join(sortie, f"{args['type']}_{args['seed']}.in")
    ecrire(sortie, TYPES[args["type"]](random.Random(args["seed"]), **args))


if __name__ == "__main__":
    main()
