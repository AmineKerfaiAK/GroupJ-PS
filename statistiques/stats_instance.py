import os
import random
import statistics as st
import sys
from collections import Counter

from lecture import borne_superieure, dossier_sortie, lire_instance, plt_ou_rien


def resume(valeurs):
    if not valeurs:
        return "none"
    return f"min {min(valeurs)} | mean {st.mean(valeurs):.1f} | median {st.median(valeurs)} | max {max(valeurs)}"


def calculer(i):
    s = {}
    demandes = Counter()
    par_endpoint = Counter()
    for v, e, n in i.req:
        demandes[v] += n
        par_endpoint[e] += n
    total = sum(demandes.values())
    videos_demandees = set(demandes)
    taille_demandee = sum(i.taille[v] for v in videos_demandees)
    trop_grandes = [v for v in range(i.V) if i.taille[v] > i.X]
    sans_cache = [e for e in range(i.E) if not i.liens[e]]
    perdu = sum(n for v, e, n in i.req if not i.liens[e] or i.taille[v] > i.X)
    deg_cache = Counter(c for l in i.liens for c in l)
    gains = [i.Ld[e] - lc for e in range(i.E) for lc in i.liens[e].values()]
    tri = sorted(demandes.values(), reverse=True)
    top = max(1, len(tri) // 10)

    s["Placement: videos vs cache space"] = [
        ("videos", i.V),
        ("video size (MB)", resume(i.taille)),
        ("videos never requested", i.V - len(videos_demandees)),
        ("videos bigger than X (can never be cached)", len(trop_grandes)),
        ("caches", f"{i.C} x {i.X} MB = {i.C * i.X} MB"),
        ("total size of requested videos", f"{taille_demandee} MB"),
        ("cache space / requested size", f"{i.C * i.X / max(1, taille_demandee):.2f}"),
        ("videos per cache on average (X / mean size)", f"{i.X / st.mean(i.taille):.1f}"),
    ]
    s["Graph: datacenter, endpoints, caches"] = [
        ("endpoints", i.E),
        ("endpoint-cache links", sum(len(l) for l in i.liens)),
        ("caches per endpoint", resume([len(l) for l in i.liens])),
        ("endpoints with no cache", len(sans_cache)),
        ("endpoints per cache", resume([deg_cache[c] for c in range(i.C)])),
        ("caches linked to no endpoint", sum(1 for c in range(i.C) if deg_cache[c] == 0)),
        ("datacenter latency Ld (ms)", resume(i.Ld)),
        ("cache latency Lc (ms)", resume([lc for l in i.liens for lc in l.values()])),
        ("time saved per link Ld - Lc (ms)", resume(gains)),
    ]
    s["Requests"] = [
        ("request lines R", i.R),
        ("total requests (sum of Rn)", total),
        ("requests per endpoint", resume(list(par_endpoint.values()))),
        ("share taken by the top 10 % videos", f"{100 * sum(tri[:top]) / max(1, total):.1f} %"),
        ("requests that can never be sped up", f"{100 * perdu / max(1, total):.1f} %"),
        ("score upper bound", borne_superieure(i)),
    ]
    return s, demandes, par_endpoint, gains, deg_cache


def dessiner_reseau(plt, i, chemin, maxi=25):
    rng = random.Random(0)
    endpoints = list(range(i.E)) if i.E <= maxi else sorted(rng.sample(range(i.E), maxi))
    caches = sorted({c for e in endpoints for c in i.liens[e]})
    fig, ax = plt.subplots(figsize=(12, 6))
    xe = {e: k / max(1, len(endpoints) - 1) for k, e in enumerate(endpoints)}
    xc = {c: k / max(1, len(caches) - 1) for k, c in enumerate(caches)}
    for e in endpoints:
        ax.plot([0.5, xe[e]], [1, 0], color="tab:blue", alpha=0.25, lw=0.8)
        for c, lc in i.liens[e].items():
            ax.plot([xc[c], xe[e]], [0.5, 0], color="tab:red", alpha=0.5, lw=0.8)
            if len(endpoints) <= 8:
                ax.text((xc[c] + xe[e]) / 2, 0.25, f"{lc}", fontsize=7, color="tab:red")
    ax.scatter([0.5], [1], s=600, marker="h", color="tab:blue", zorder=3)
    ax.text(0.5, 1.07, "datacenter", ha="center")
    ax.scatter(list(xc.values()), [0.5] * len(xc), s=200, marker="s", color="tab:red", zorder=3)
    for c, x in xc.items():
        ax.text(x, 0.56, f"c{c}", ha="center", fontsize=7)
    ax.scatter(list(xe.values()), [0] * len(xe), s=150, color="tab:green", zorder=3)
    for e, x in xe.items():
        ax.text(x, -0.08, f"e{e}\n{i.Ld[e]}ms", ha="center", fontsize=7)
    titre = f"Graph {i.nom}"
    if len(endpoints) < i.E:
        titre += f" (sample of {len(endpoints)} endpoints out of {i.E})"
    ax.set_title(titre)
    ax.set_ylim(-0.25, 1.15)
    ax.axis("off")
    fig.savefig(chemin, dpi=120, bbox_inches="tight")
    plt.close(fig)


def graphiques(plt, i, demandes, par_endpoint, gains, deg_cache, d):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    ax[0].hist(i.taille, bins=40, color="tab:purple")
    ax[0].axvline(i.X, color="red", ls="--", label=f"X = {i.X}")
    ax[0].set_title("Video size (MB)")
    ax[0].legend()
    taille_dem = sum(i.taille[v] for v in demandes)
    ax[1].bar(["requested videos", "cache space"], [taille_dem, i.C * i.X], color=["tab:purple", "tab:red"])
    ax[1].set_title("Placement: what must fit vs available space")
    fig.savefig(os.path.join(d, "placement.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    ax[0][0].hist([len(l) for l in i.liens], bins=range(0, max(len(l) for l in i.liens) + 2), color="tab:green")
    ax[0][0].set_title("Caches per endpoint")
    ax[0][1].hist([deg_cache[c] for c in range(i.C)], bins=30, color="tab:red")
    ax[0][1].set_title("Endpoints per cache")
    ax[1][0].hist(i.Ld, bins=40, color="tab:blue")
    ax[1][0].set_title("Datacenter latency Ld (ms)")
    ax[1][1].hist(gains or [0], bins=40, color="tab:orange")
    ax[1][1].set_title("Time saved per link Ld - Lc (ms)")
    fig.tight_layout()
    fig.savefig(os.path.join(d, "graphe.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    tri = sorted(demandes.values(), reverse=True)
    ax[0].loglog(range(1, len(tri) + 1), tri, color="tab:purple")
    ax[0].set_title("Video popularity (rank vs requests, log-log)")
    ax[1].hist(list(par_endpoint.values()), bins=40, color="tab:green")
    ax[1].set_title("Requests per endpoint")
    fig.savefig(os.path.join(d, "requetes.png"), dpi=110, bbox_inches="tight")
    plt.close(fig)

    dessiner_reseau(plt, i, os.path.join(d, "reseau.png"))


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python stats_instance.py instance.in")
    i = lire_instance(sys.argv[1])
    s, demandes, par_endpoint, gains, deg_cache = calculer(i)
    d = dossier_sortie(i.nom, "instance")
    texte = [f"=== Instance statistics: {i.nom} ==="]
    for partie, lignes in s.items():
        texte.append(f"\n[{partie}]")
        texte += [f"  {k:<50} {v}" for k, v in lignes]
    texte = "\n".join(texte)
    print(texte)
    with open(os.path.join(d, "rapport.txt"), "w") as f:
        f.write(texte + "\n")
    plt = plt_ou_rien()
    if plt:
        graphiques(plt, i, demandes, par_endpoint, gains, deg_cache, d)
        print(f"\n  charts -> {d}")


if __name__ == "__main__":
    main()
