import os
import sys

LIM = dict(V=10000, E=1000, R=1000000, C=1000, X=500000, S=1000,
           LD_MIN=2, LD_MAX=4000, LC_MAX=500, RN=10000)


def valider(chemin):
    erreurs = []
    avert = []

    def verif(cond, msg):
        if not cond and len(erreurs) < 10:
            erreurs.append(msg)

    with open(chemin, "rb") as f:
        brut = f.read()
    if b"\r" in brut:
        avert.append("the file uses Windows line endings (\\r\\n) instead of \\n")
    lignes = brut.decode("ascii", errors="replace").replace("\r", "").split("\n")
    pos = 0

    def ligne(n):
        nonlocal pos
        if pos >= len(lignes):
            raise ValueError("file too short")
        vals = lignes[pos].split()
        pos += 1
        if n is not None and len(vals) != n:
            raise ValueError(f"line {pos}: expected {n} numbers, read {len(vals)}")
        return list(map(int, vals))

    try:
        V, E, R, C, X = ligne(5)
        verif(1 <= V <= LIM["V"], f"V={V} outside [1,{LIM['V']}]")
        verif(1 <= E <= LIM["E"], f"E={E} outside [1,{LIM['E']}]")
        verif(1 <= R <= LIM["R"], f"R={R} outside [1,{LIM['R']}]")
        verif(1 <= C <= LIM["C"], f"C={C} outside [1,{LIM['C']}]")
        verif(1 <= X <= LIM["X"], f"X={X} outside [1,{LIM['X']}]")
        tailles = ligne(V)
        for i, s in enumerate(tailles):
            verif(1 <= s <= LIM["S"], f"video {i}: size {s} outside [1,{LIM['S']}]")
        for e in range(E):
            ld, k = ligne(2)
            verif(LIM["LD_MIN"] <= ld <= LIM["LD_MAX"], f"endpoint {e}: Ld={ld} outside [2,4000]")
            verif(0 <= k <= C, f"endpoint {e}: K={k} outside [0,C]")
            vus = set()
            for _ in range(k):
                c, lc = ligne(2)
                verif(0 <= c < C, f"endpoint {e}: cache {c} does not exist")
                verif(c not in vus, f"endpoint {e}: cache {c} listed twice")
                verif(1 <= lc <= LIM["LC_MAX"], f"endpoint {e}: Lc={lc} outside [1,500]")
                verif(lc < ld, f"endpoint {e}: Lc={lc} >= Ld={ld}")
                vus.add(c)
        paires = set()
        doublons = 0
        for i in range(R):
            v, e, n = ligne(3)
            verif(0 <= v < V, f"request {i}: video {v} does not exist")
            verif(0 <= e < E, f"request {i}: endpoint {e} does not exist")
            verif(0 < n <= LIM["RN"], f"request {i}: Rn={n} outside ]0,{LIM['RN']}]")
            if (v, e) in paires:
                doublons += 1
            paires.add((v, e))
        if doublons:
            avert.append(f"{doublons} lines repeat the same video and endpoint")
        if any(l.strip() for l in lignes[pos:]):
            erreurs.append("extra lines after the R requests")
    except ValueError as ex:
        erreurs.append(str(ex))
    return erreurs, avert


def fichiers(args):
    for a in args:
        if os.path.isdir(a):
            yield from sorted(os.path.join(a, f) for f in os.listdir(a) if f.endswith(".in"))
        else:
            yield a


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: python validateur.py file.in|folder ...")
    tous_ok = True
    for chemin in fichiers(sys.argv[1:]):
        erreurs, avert = valider(chemin)
        print(("VALID     " if not erreurs else "INVALID   ") + chemin)
        for m in erreurs:
            print("    error: " + m)
        for m in avert:
            print("    warning: " + m)
        tous_ok &= not erreurs
    sys.exit(0 if tous_ok else 1)


if __name__ == "__main__":
    main()
