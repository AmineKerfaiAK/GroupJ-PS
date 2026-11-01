import heapq
import random
import sys
import time

debut = time.time()
LIMITE = float(sys.argv[1]) if len(sys.argv) > 1 else 300
# Optional: a solution file to start from (e.g. the output of the C++ version).
DEPART = sys.argv[2] if len(sys.argv) > 2 else None
# Step 5: number of neighbour caches emptied with the chosen cache.
VOISINS_ILS = 2
# Knapsack grid: at most 10,000 units per cache (exact sizes when X <= 10,000).
UNITES_MAX = 10_000


def log(texte):
    sys.stderr.write(texte + "\n")


def secondes():
    return time.time() - debut


def lire():
    d = sys.stdin.buffer.read().split()
    it = iter(map(int, d))
    V, E, R, C, X = (next(it) for _ in range(5))
    taille = [next(it) for _ in range(V)]
    Ld = [0] * E
    latE = [dict() for _ in range(E)]
    lienC = [[] for _ in range(C)]
    for e in range(E):
        Ld[e] = next(it)
        for _ in range(next(it)):
            c, l = next(it), next(it)
            if l < Ld[e]:
                latE[e][c] = l
                lienC[c].append((e, l))
    vu = {}
    rv, re, rn = [], [], []
    total = 0
    for _ in range(R):
        v, e, n = next(it), next(it), next(it)
        total += n
        k = v * E + e
        if k in vu:
            rn[vu[k]] += n
        else:
            vu[k] = len(rv)
            rv.append(v)
            re.append(e)
            rn.append(n)
    log("[Step 1] Reading the input             (%.2f s)" % secondes())
    log("         V=%d E=%d C=%d X=%d, %d different (video, endpoint) lines" % (V, E, C, X, len(rv)))
    return V, E, C, X, taille, Ld, latE, lienC, rv, re, rn, total


def lire_solution(chemin, C):
    contenu = [[] for _ in range(C)]
    lignes = open(chemin).read().split("\n")
    for k in range(1, int(lignes[0]) + 1):
        p = list(map(int, lignes[k].split()))
        contenu[p[0]] = p[1:]
    return contenu


def score_de(contenu, Ld, latE, rv, re, rn):
    # Total time saved by a given cache content (same rule as score.py).
    dans = {}
    for c, vids in enumerate(contenu):
        for v in vids:
            dans.setdefault(v, set()).add(c)
    total = 0
    for i in range(len(rv)):
        e = re[i]
        b = Ld[e]
        for c in dans.get(rv[i], ()):
            l = latE[e].get(c)
            if l is not None and l < b:
                b = l
        total += rn[i] * (Ld[e] - b)
    return total


def main():
    V, E, C, X, taille, Ld, latE, lienC, rv, re, rn, total = lire()
    R = len(rv)
    parV = [[] for _ in range(V)]
    parE = [[] for _ in range(E)]
    for i in range(R):
        parV[rv[i]].append(i)
        parE[re[i]].append(i)
    best = [Ld[re[i]] for i in range(R)]
    holders = [[] for _ in range(V)]
    contenu = [[] for _ in range(C)]
    libre = [X] * C
    gagne = 0

    tas = []
    for c in range(C):
        acc = {}
        for e, l in lienC[c]:
            d = Ld[e] - l
            for i in parE[e]:
                v = rv[i]
                if taille[v] <= X:
                    acc[v] = acc.get(v, 0) + rn[i] * d
        tas.extend((-g / taille[v], c, v) for v, g in acc.items())
    heapq.heapify(tas)
    log("[Step 2] Gains of %d (video, cache) pairs (%.2f s)" % (len(tas), secondes()))

    places = 0
    while tas:
        _, c, v = heapq.heappop(tas)
        if taille[v] > libre[c]:
            continue
        g = 0
        for i in parV[v]:
            l = latE[re[i]].get(c)
            if l is not None and l < best[i]:
                g += rn[i] * (best[i] - l)
        if g <= 0:
            continue
        cle = g / taille[v]
        if tas and cle < -tas[0][0]:
            heapq.heappush(tas, (-cle, c, v))
            continue
        for i in parV[v]:
            l = latE[re[i]].get(c)
            if l is not None and l < best[i]:
                best[i] = l
        contenu[c].append(v)
        holders[v].append(c)
        libre[c] -= taille[v]
        gagne += g
        places += 1
    log("[Step 3] Lazy greedy: %d videos placed (%.2f s)" % (places, secondes()))
    log("         score after greedy: %d" % (gagne * 1000 // total))

    unite = max(1, -(-X // UNITES_MAX))
    W = X // unite
    ordre = list(range(C))
    rng = random.Random(1)

    def optimiser(c):
        # Re-choose the content of cache c exactly (knapsack), the other
        # caches being fixed. Returns True if the score went up.
        nonlocal gagne
        val = {}
        bw = {}
        for e, l in lienC[c]:
            lat_e = latE[e]
            for i in parE[e]:
                v = rv[i]
                b = Ld[e]
                for h in holders[v]:
                    if h != c:
                        lh = lat_e.get(h)
                        if lh is not None and lh < b:
                            b = lh
                bw[i] = b
                if b > l and taille[v] <= X:
                    val[v] = val.get(v, 0) + rn[i] * (b - l)
        actuel = sum(val.get(v, 0) for v in contenu[c])
        videos = sorted(val, key=lambda v: val[v] / taille[v], reverse=True)
        items = []
        cumul = 0
        for v in videos:
            if cumul > 4 * X:
                break
            items.append(v)
            cumul += taille[v]
        dans_items = set(items)
        items += [v for v in contenu[c] if v not in dans_items and val.get(v, 0) > 0]
        dp = [0] * (W + 1)
        pris = []
        for v in items:
            w = -(-taille[v] // unite)
            g = val[v]
            ligne = set()
            for cap in range(W, w - 1, -1):
                s = dp[cap - w] + g
                if s > dp[cap]:
                    dp[cap] = s
                    ligne.add(cap)
            pris.append(ligne)
        choix = []
        choisis = set()
        place = nouveau = 0
        cap = W
        for k in range(len(items) - 1, -1, -1):
            if cap in pris[k]:
                v = items[k]
                choix.append(v)
                choisis.add(v)
                cap -= -(-taille[v] // unite)
                place += taille[v]
                nouveau += val[v]
        for v in videos:
            if v not in choisis and place + taille[v] <= X:
                choix.append(v)
                choisis.add(v)
                place += taille[v]
                nouveau += val[v]
        if nouveau > actuel:
            for v in contenu[c]:
                holders[v].remove(c)
            contenu[c] = choix
            for v in choix:
                holders[v].append(c)
            libre[c] = X - place
            for e, l in lienC[c]:
                for i in parE[e]:
                    best[i] = min(bw[i], l) if rv[i] in choisis else bw[i]
            gagne += nouveau - actuel
            return True
        return False

    def definir(c, nouveau_contenu):
        # Put exactly these videos in cache c and update best[] and the score.
        nonlocal gagne
        for v in contenu[c]:
            holders[v].remove(c)
        contenu[c] = list(nouveau_contenu)
        for v in contenu[c]:
            holders[v].append(c)
        libre[c] = X - sum(taille[v] for v in contenu[c])
        for e, l in lienC[c]:
            lat_e = latE[e]
            for i in parE[e]:
                b = Ld[e]
                for h in holders[rv[i]]:
                    lh = lat_e.get(h)
                    if lh is not None and lh < b:
                        b = lh
                gagne += rn[i] * (best[i] - b)
                best[i] = b

    tour = 0
    while secondes() < LIMITE:
        tour += 1
        rng.shuffle(ordre)
        avant = gagne
        ameliores = 0
        for c in ordre:
            if secondes() >= LIMITE:
                break
            if optimiser(c):
                ameliores += 1
        log("[Step 4] Local search round %d: %d caches improved, score %d (%.2f s)"
            % (tour, ameliores, gagne * 1000 // total, secondes()))
        if gagne == avant:
            break

    if DEPART:
        depart = lire_solution(DEPART, C)
        g = score_de(depart, Ld, latE, rv, re, rn)
        log("         starting solution %s: score %d" % (DEPART, g * 1000 // total))
        if g > gagne:
            for c in range(C):
                definir(c, depart[c])

    # ---------- Step 5: iterated local search (pure Python, no library) ----------
    # Step 4 changes one cache at a time, so it gets stuck when the only way
    # up is to change two caches together (e.g. move a video from cache A to
    # cache B to free room in A). Here we empty a cache and two of its
    # neighbours (caches sharing an endpoint), let the knapsack of step 4
    # refill them, and keep the result if the score did not go down.
    actifs = [c for c in range(C) if lienC[c]]
    voisins = {}
    essais = gardes = sans_progres = 0
    avant_ils = gagne
    log("[Step 5] Iterated local search (empty 1 + %d neighbour caches, refill)" % VOISINS_ILS)
    while actifs and secondes() < LIMITE and sans_progres < 200 * len(actifs):
        essais += 1
        c0 = rng.choice(actifs)
        if c0 not in voisins:
            s = set()
            for e, _ in lienC[c0]:
                s.update(latE[e])
            s.discard(c0)
            voisins[c0] = list(s)
        groupe = [c0] + rng.sample(voisins[c0], min(VOISINS_ILS, len(voisins[c0])))
        sauve = [(c, list(contenu[c])) for c in groupe]
        g0 = gagne
        for c in groupe:
            definir(c, [])
        for _ in range(3):
            rng.shuffle(groupe)
            bouge = False
            for c in groupe:
                bouge |= optimiser(c)
            if not bouge:
                break
        if gagne > g0:
            gardes += 1
            sans_progres = 0
        else:
            sans_progres += 1
            if gagne < g0:   # worse: put everything back as it was
                for c, ancien in sauve:
                    definir(c, ancien)
    log("         %d tries, %d kept, score %d -> %d (%.2f s)"
        % (essais, gardes, avant_ils * 1000 // total, gagne * 1000 // total, secondes()))

    utilises = [c for c in range(C) if contenu[c]]
    sortie = [str(len(utilises))] + [" ".join(map(str, [c] + contenu[c])) for c in utilises]
    sys.stdout.buffer.write(("\n".join(sortie) + "\n").encode())
    log("[Step 6] Writing the output            (%.2f s)" % secondes())
    log("         SCORE = %d" % (gagne * 1000 // total))


main()