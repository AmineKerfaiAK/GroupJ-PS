import glob
import json
import os
import random
import shutil
import subprocess
import sys
import threading
import time
import uuid
import webbrowser

from flask import Flask, jsonify, request, send_from_directory

import analyse
from analyse import RACINE

import generateur as gen
import validateur

app = Flask(__name__, static_folder="static")
DATA = os.path.join(RACINE, "site", "data")
BUILD = os.path.join(RACINE, "build")
SORTIES = os.path.join(RACINE, "outputs")
SCORES = os.path.join(DATA, "scores.json")
MSYS = r"C:\msys64\ucrt64\bin"
JOBS = {}
VERROU = threading.Lock()


def rel(p):
    return os.path.relpath(p, RACINE).replace("\\", "/")


def absolu(r):
    p = os.path.abspath(os.path.join(RACINE, r))
    if not p.startswith(RACINE):
        raise ValueError("path not allowed")
    return p


def cle_instance(r):
    return r[:-3].replace("/", "__")


def cle_code(r):
    return r.replace("/", "__").replace(".", "_")


def lister_instances():
    res = []
    for p in sorted(glob.glob(os.path.join(RACINE, "*.in"))) + \
             sorted(glob.glob(os.path.join(RACINE, "instances", "*.in"))) + \
             sorted(glob.glob(os.path.join(RACINE, "instances", "generated", "*.in"))) + \
             sorted(glob.glob(os.path.join(RACINE, "instances", "generees", "*.in"))):
        with open(p) as f:
            tete = f.readline().split()
        res.append({"id": rel(p), "nom": os.path.basename(p)[:-3],
                    "groupe": "generated" if ("generated" in p or "generees" in p) else "official" if "instances" in p else "statement",
                    "VERCX": tete, "taille": os.path.getsize(p)})
    return res


def lister_codes():
    res = []
    for motif in ("*.cpp", "*.py", "versions/*.cpp", "versions/*.py"):
        for p in sorted(glob.glob(os.path.join(RACINE, motif))):
            if os.path.basename(p) != "score.py":
                res.append(rel(p))
    return res


def lire_scores():
    if not os.path.exists(SCORES):
        return []
    with open(SCORES) as f:
        return json.load(f)


def ajouter_score(entree):
    with VERROU:
        s = lire_scores()
        s.append(entree)
        os.makedirs(DATA, exist_ok=True)
        with open(SCORES, "w") as f:
            json.dump(s, f, indent=1)


def env_compil():
    env = dict(os.environ)
    if os.name == "nt" and os.path.isdir(MSYS):
        env["PATH"] = MSYS + os.pathsep + env["PATH"]
    return env


def ecrire_log(job, texte):
    job["log"] += texte if texte.endswith("\n") else texte + "\n"


def executer(job, code, instances):
    try:
        source = absolu(code)
        os.makedirs(BUILD, exist_ok=True)
        if code.endswith(".cpp"):
            exe = os.path.join(BUILD, cle_code(code) + (".exe" if os.name == "nt" else ""))
            ecrire_log(job, f"$ g++ -std=c++17 -O2 {code}")
            cmd = ["g++", "-std=c++17", "-O2", source, "-o", exe]
            if os.name == "nt":
                cmd.insert(3, "-static")
            p = subprocess.run(cmd, capture_output=True, text=True, env=env_compil())
            if p.returncode != 0:
                ecrire_log(job, p.stderr)
                ecrire_log(job, "Compilation failed: read the first error above.")
                job["statut"] = "error"
                return
            lancer = [exe]
        else:
            lancer = [sys.executable, source]
        for r in instances:
            nom = os.path.basename(r)[:-3]
            ecrire_log(job, f"\n===== {nom} =====")
            dossier = os.path.join(SORTIES, cle_code(code))
            os.makedirs(dossier, exist_ok=True)
            sortie = os.path.join(dossier, cle_instance(r) + ".out")
            t0 = time.time()
            with open(absolu(r), "rb") as fin, open(sortie, "wb") as fout:
                p = subprocess.Popen(lancer, stdin=fin, stdout=fout, stderr=subprocess.PIPE,
                                     text=True, env=env_compil(), cwd=RACINE)
                for ligne in p.stderr:
                    ecrire_log(job, ligne)
                p.wait()
            duree = round(time.time() - t0, 2)
            try:
                sc = analyse.score_rapide(absolu(r), sortie)
            except Exception as ex:
                sc = {"score": 0, "borne": 0, "valide": False, "erreurs": [str(ex)]}
            res = {"code": code, "instance": r, "nom": nom, "temps": duree,
                   "date": time.strftime("%Y-%m-%d %H:%M"), **sc}
            job["resultats"].append(res)
            ajouter_score(res)
            etat = "valid" if sc["valide"] else "INVALID " + "; ".join(sc["erreurs"])
            ecrire_log(job, f"score {sc['score']}  (best possible {sc['borne']})  {duree} s  {etat}")
        job["statut"] = "done"
    except Exception as ex:
        ecrire_log(job, f"Error: {ex}")
        job["statut"] = "error"


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/instances")
def api_instances():
    return jsonify(lister_instances())


@app.get("/api/instance")
def api_instance():
    return jsonify(analyse.stats_instance(absolu(request.args["id"])))


@app.get("/api/valider")
def api_valider():
    erreurs, avert = validateur.valider(absolu(request.args["id"]))
    return jsonify({"erreurs": erreurs, "avertissements": avert})


@app.post("/api/generer")
def api_generer():
    d = request.get_json()
    type_ = d.pop("type")
    nom = "".join(ch for ch in d.pop("nom", "") if ch.isalnum() or ch in "_-") or "_".join([type_] + ([d["variante"]] if type_ == "edge" else []) + [str(d.get("seed", 42))])
    seed = int(d.pop("seed", 42))
    params = {k: (v if k == "variante" else float(v) if k == "a" else int(v)) for k, v in d.items() if v != ""}
    try:
        gen.verifier(type_, params)
    except ValueError as ex:
        return jsonify({"erreur": str(ex)}), 400
    inst = gen.TYPES[type_](random.Random(seed), **params)
    chemin = os.path.join(RACINE, "instances", "generated", nom + ".in")
    gen.ecrire(chemin, inst)
    return jsonify({"id": rel(chemin)})


@app.get("/api/codes")
def api_codes():
    return jsonify(lister_codes())


@app.get("/api/code")
def api_code():
    with open(absolu(request.args["chemin"]), encoding="utf-8") as f:
        return jsonify({"contenu": f.read()})


@app.post("/api/code")
def api_code_ecrire():
    d = request.get_json()
    chemin = d["chemin"]
    if not chemin.endswith((".cpp", ".py")):
        return jsonify({"erreur": "the file must end in .cpp or .py"}), 400
    p = absolu(chemin)
    if os.path.exists(p) and not d.get("nouveau"):
        shutil.copy(p, p + ".bak")
    elif os.path.exists(p):
        return jsonify({"erreur": "this file already exists"}), 400
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(d["contenu"])
    return jsonify({"chemin": rel(p)})


@app.post("/api/lancer")
def api_lancer():
    d = request.get_json()
    instances = d["instances"] if d["instances"] != "all" else [x["id"] for x in lister_instances()]
    jid = uuid.uuid4().hex[:8]
    JOBS[jid] = {"statut": "running", "log": "", "resultats": [], "total": len(instances)}
    threading.Thread(target=executer, args=(JOBS[jid], d["code"], instances), daemon=True).start()
    return jsonify({"job": jid})


@app.get("/api/job/<jid>")
def api_job(jid):
    return jsonify(JOBS[jid])


@app.get("/api/solution")
def api_solution():
    code, r = request.args["code"], request.args["id"]
    sortie = os.path.join(SORTIES, cle_code(code), cle_instance(r) + ".out")
    if not os.path.exists(sortie):
        return jsonify({"absent": True})
    return jsonify(analyse.stats_solution(absolu(r), sortie))


@app.get("/api/scores")
def api_scores():
    return jsonify(lire_scores())


if __name__ == "__main__":
    port = 5000
    print(f"Site: http://127.0.0.1:{port}")
    if "--no-browser" not in sys.argv:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
