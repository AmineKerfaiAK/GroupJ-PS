import os
import statistics as st
import sys
from collections import Counter, defaultdict

from lecture import borne_superieure, dossier_sortie, lire_instance, lire_solution, plt_ou_rien


def analyser(i, contenu):
    erreurs = []
    plein = [sum(i.taille[v] for v in contenu[c]) for c in range(i.C)]
    for c in range(i.C):
        if plein[c] > i.X:
            erreurs.append(f"cache {c}: {plein[c]} MB > X = {i.X}")
    gain_paire = defaultdict(int)
    lat_avant = Counter()
    lat_apres = Counter()
    tot = nb = servies = 0
    ou = defaultdict(list)
    for c in range(i.C):
        for v in contenu[c]:
            ou[v].append(c)
    for v, e, n in i.req:
        best, cache = i.Ld[e], None
        liens = i.liens[e]
        for c in ou.get(v, ()):
            lc = liens.get(c)
            if lc is not None and lc < best:
                best, cache = lc, c
        if cache is not None:
            gain_paire[(cache, v)] += n * (i.Ld[e] - best)
            servies += n
        lat_avant[i.Ld[e]] += n
        lat_apres[best] += n
        tot += n * (i.Ld[e] - best)
        nb += n
    copies = sum(len(s) for s in contenu)
    inutiles = sum(1 for c in range(i.C) for v in contenu[c] if gain_paire.get((c, v), 0) == 0)
    gain_cache = Counter()
    gain_video = Counter()
    for (c, v), g in gain_paire.items():
        gain_cache[c] += g
        gain_video[v] += g
    moy = lambda cpt: sum(k * n for k, n in cpt.items()) / max(1, nb)
    r = dict(
        erreurs=erreurs, score=tot * 1000 // max(1, nb), borne=borne_superieure(i),
        plein=plein, copies=copies, inutiles=inutiles,
        distinctes=len(set().union(*contenu)) if contenu else 0,
        servies=servies, nb=nb, lat_avant=lat_avant, lat_apres=lat_apres,
        moy_avant=moy(lat_avant), moy_apres=moy(lat_apres),
        gain_paire=gain_paire, gain_cache=gain_cache, gain_video=gain_video,
    )
    return r


def rapport(i, r):
    taux = [100 * p / i.X for p in r["plein"]]
    utilises = sum(1 for p in r["plein"] if p > 0)
    t = [f"=== Solution statistics: {i.nom} ==="]
    t.append("  VALID" if not r["erreurs"] else "  INVALID: " + " ; ".join(r["erreurs"][:5]))
    t.append(f"  {'score':<45} {r['score']}")
    t.append(f"  {'upper bound':<45} {r['borne']}")
    t.append(f"  {'score / upper bound':<45} {100 * r['score'] / max(1, r['borne']):.1f} %")
    t.append("\n[Cache usage]")
    t.append(f"  {'caches used':<45} {utilises} / {i.C}")
    t.append(f"  {'average fill':<45} {st.mean(taux):.1f} %")
    t.append(f"  {'caches more than 95 % full':<45} {sum(1 for x in taux if x >= 95)}")
    t.append(f"  {'copies placed':<45} {r['copies']}")
    t.append(f"  {'distinct videos in caches':<45} {r['distinctes']}")
    t.append(f"  {'useless copies (serve no request)':<45} {r['inutiles']}")
    t.append("\n[Latency per video and cache]")
    t.append(f"  {'requests served by a cache':<45} {100 * r['servies'] / max(1, r['nb']):.1f} %")
    t.append(f"  {'average latency without caches':<45} {r['moy_avant']:.1f} ms")
    t.append(f"  {'average latency with the solution':<45} {r['moy_apres']:.1f} ms")
    t.append("  top 10 (cache, video) by time saved:")
    for (c, v), g in sorted(r["gain_paire"].items(), key=lambda x: -x[1])[:10]:
        t.append(f"    cache {c:<5} video {v:<6} size {i.taille[v]:<5} {g} ms saved")
    return "\n".join(t)


def graphiques(plt, i, r, d):
    taux = sorted((100 * p / i.X for p in r["plein"]), reverse=True)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    ax[0].bar(range(len(taux)), taux, color="tab:red", width=1.0)
    ax[0].axhline(100, color="black", ls="--")
    ax[0].set_title("Fill of each cache (%), sorted")
    gc = [r["gain_cache"].get(c, 0) for c in range(i.C)]
    ax[1].bar(range(i.C), gc, color="tab:orange", width=1.0)
    ax[1].set_title("Time saved per cache (ms)")
    fig.savefig(os.path.join(d, "utilisation_caches.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    for cpt, nom, coul in ((r["lat_avant"], "without caches", "tab:blue"), (r["lat_apres"], "solution", "tab:green")):
        ks = sorted(cpt)
        ax[0].hist(ks, weights=[cpt[k] for k in ks], bins=40, alpha=0.6, label=nom, color=coul)
    ax[0].set_title("Request latency (ms), weighted by Rn")
    ax[0].legend()
    top = r["gain_video"].most_common(20)
    ax[1].barh([f"v{v}" for v, _ in top][::-1], [g for _, g in top][::-1], color="tab:purple")
    ax[1].set_title("20 videos that save the most time (ms)")
    fig.savefig(os.path.join(d, "latence.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(["score", "upper bound"], [r["score"], r["borne"]], color=["tab:green", "tab:gray"])
    ax.set_title("Score vs upper bound")
    fig.savefig(os.path.join(d, "score.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: python stats_solution.py instance.in solution.out")
    i = lire_instance(sys.argv[1])
    r = analyser(i, lire_solution(sys.argv[2], i))
    d = dossier_sortie(i.nom, "solution")
    texte = rapport(i, r)
    print(texte)
    with open(os.path.join(d, "rapport.txt"), "w") as f:
        f.write(texte + "\n")
    plt = plt_ou_rien()
    if plt:
        graphiques(plt, i, r, d)
        print(f"\n  charts -> {d}")


if __name__ == "__main__":
    main()
