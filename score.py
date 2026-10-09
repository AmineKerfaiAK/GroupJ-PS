import sys

def score(inp, out):
    f = open(inp).read().split('\n')
    V,E,R,C,X = map(int, f[0].split())
    sz = list(map(int, f[1].split()))
    line = 2
    Ld = []
    lat = []
    for e in range(E):
        d,k = map(int, f[line].split()); line += 1
        Ld.append(d)
        m = {}
        for _ in range(k):
            c,l = map(int, f[line].split()); line += 1
            m[c] = l
        lat.append(m)
    req = []
    for _ in range(R):
        v,e,n = map(int, f[line].split()); line += 1
        req.append((v,e,n))
    g = open(out).read().split('\n')
    if not g[0].strip():
        return 'empty output: the program did not run'
    N = int(g[0])
    hold = {}
    for i in range(1, N+1):
        parts = list(map(int, g[i].split()))
        c = parts[0]
        vids = parts[1:]
        assert sum(sz[v] for v in vids) <= X, "cache %d over capacity" % c
        hold[c] = set(vids)
    tot = 0
    nb = 0
    for v,e,n in req:
        best = Ld[e]
        for c,l in lat[e].items():
            if v in hold.get(c, ()) and l < best:
                best = l
        tot += n*(Ld[e]-best)
        nb += n
    return tot*1000//nb

print(score(sys.argv[1], sys.argv[2]))
