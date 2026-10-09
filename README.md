# Hash Code 2017 Lab: Streaming videos

A small lab to test your solution to the Hash Code 2017 qualification problem *Streaming videos*.

It gives you:

- an **instance generator** that makes valid test files of 7 kinds
- a **validator** that checks a file follows every rule of the problem
- a **score** calculator, with the **best possible score** of each instance
- **statistics** on instances and on solutions
- a **website** to run your code, replay your solution step by step and compare scores

```
generate ─► check ─► run your code ─► score ─► statistics and replay
```

---

## 1. What you need

| Tool | Why | Check it with |
|---|---|---|
| Python 3.9 or newer | the lab is written in Python | `python --version` |
| g++ (C++17) | only if your solution is in C++ | `g++ --version` |
| Internet, the first time | to install Flask and matplotlib | |

**Windows:** install g++ with [MSYS2](https://www.msys2.org/), then run `pacman -S mingw-w64-ucrt-x86_64-gcc` in the MSYS2 UCRT64 terminal. The lab looks for g++ in `C:\msys64\ucrt64\bin` automatically.

---

## 2. Start the website

**Windows:** double-click `lancer_site.bat`

**Linux, macOS or WSL:**

```bash
./lancer_site.sh
```

The script installs what is missing, makes 12 test instances the first time, and opens **http://127.0.0.1:5000**.
Keep the terminal open while you use the site. Close it to stop the site.

---

## 3. Add your algorithm

Put your file in the **main folder**:

```
hashcode-lab/
├── YourAlogrithmFile.py           ◄── your algorithm goes here, any name
└── ...
```

Then:

1. Refresh the website (F5).
2. Pick your file in the **Code** list at the top.
3. Click **Run**.



**Rules for your file**

| Rule | Why |
|---|---|
| Name ends with  `.py` | Only these files appear in the Code list |
| Everything in **one file** | The site compiles only that file |
| Read the instance on **stdin** | The site sends the `.in` file to your program |
| Write the solution on **stdout**, in the official format | The site saves it and computes the score |
| Messages on **stderr** only | They appear in the Code tab without breaking the output |
| C++17, or Python 3 | The site uses `g++ -std=c++17 -O2` or `python` |
| Do not name it `score.py` | That name is the score tool |




---

## 4. The website

Pick an **instance** and a **code** at the top. **Run** compiles and runs your code on that instance.
Hover any number, chart or button to see what it means.

| Tab | What you do there |
|---|---|
| **Instances** | See an instance: numbers, network drawing, 8 charts. Make a new instance. Check a file. |
| **Demo** | Replay your solution one video at a time and watch the score grow. |
| **Statistics** | See how good your solution is, how the caches are used, and what to fix first. |
| **Code** | Edit your code, save it as a new version, run it on one or all instances, compare with your best score. |

Every run is saved in `site/data/scores.json`, so you can compare versions.

---

## 5. Make test instances

From the website (**Instances** tab, *Make a new instance*) or from the terminal:

```bash
python generateur/generateur.py --suite -o instances/generated
python generateur/generateur.py --type zipf --V 5000 --E 300 --R 50000 --C 50 --X 2000 --a 1.2 --seed 7 -o instances/generated/hits.in
python generateur/generateur.py --type edge --variante no_cache -o instances/generated/no_cache.in
```

| Type | How it is made | What it tests |
|---|---|---|
| `random` | All values random | An average case |
| `zipf` | A few videos get most of the views | Putting the popular videos first |
| `regional` | Groups of users with their own caches and favourite videos | Different videos in different caches |
| `dejavu` | Each endpoint asks for the same few videos again and again | Many repeated request lines |
| `giant` | Videos about as big as a cache | Never overfilling a cache |
| `knapsack_trap` | A small video looks best per MB, but it is not | Where sorting by gain ÷ size fails |
| `edge` | Tiny or extreme cases: `single`, `no_cache`, `too_big`, `exact_fit`, `maximum` | Your code does not crash |

Settings:

| Setting | Option | Meaning |
|---|---|---|
| Videos | `--V` | number of videos (1 to 10,000) |
| Endpoints | `--E` | number of endpoints (1 to 1,000) |
| Requests | `--R` | number of request lines |
| Caches | `--C` | number of caches (1 to 1,000) |
| Cache size | `--X` | MB in one cache |
| Min / max video size | `--smin`, `--smax` | video sizes in MB (1 to 1,000) |
| Caches per endpoint | `--kmax` | the most caches one endpoint can use |
| Popularity | `--a` | for `zipf` and `regional`: higher means a few videos get almost all views |
| Regions | `--G` | for `regional`: number of user groups |
| Seed | `--seed` | the same seed and settings always give the same file |

The generator refuses settings that would break the rules, and says why.

---

## 6. Check a file

```bash
python generateur/validateur.py instances
python generateur/validateur.py my_file.in
```

It prints `VALID` or `INVALID` with the reasons.

---

## 7. Statistics in the terminal

```bash
python statistiques/stats_instance.py instances/kittens.in
python statistiques/stats_solution.py instances/kittens.in kittens.out
```

Reports and charts are saved in `statistiques/sorties/<instance>/`.

To run everything on every instance at once:

```bash
./pipeline.sh        Linux, macOS, WSL
pipeline.bat         Windows
```

---

## 8. Two words to know

**Score:** the average time saved per request, in microseconds.

```
score = total of (requests × (datacenter wait − real wait)) × 1000 ÷ total requests
```

**Best possible score (upper bound):** the score you would get if every cache were big enough for all videos. Every request uses its fastest cache. No solution can beat it.

**Your score (lower bound):** a real valid solution. The true best score is between the two.

```
best possible score  ── nobody can go above
true best score      ── unknown
your score           ── you are here
```

---

## 9. Folders

```
hashcode-lab/
├── my_solution.cpp, my_solution.py   starters
├── your_file.cpp or .py             your algorithm, in the main folder
├── versions/                         your saved versions (made by the website)
├── sample.in                         example from the problem
├── instances/                        the 4 official instances
│   └── generated/                    instances you make
├── generateur/                       generator and validator
├── statistiques/                     statistics in the terminal
├── site/                             the website
├── score.py                          official score
├── lancer_site.bat / .sh             start the website
└── pipeline.bat / .sh                run everything in the terminal
```

---

## 10. Problems

| Problem | Fix |
|---|---|
| `g++ is not recognized` | Install g++ (see section 1), or use a `.py` solution |
| `python is not recognized` | Install Python and tick *Add Python to PATH* |
| The site does not open | Open http://127.0.0.1:5000 yourself |
| Port 5000 already used | Close the other program using it, or the other lab window |
| The charts or the code editor are missing | You need internet: they load from a CDN |
| "This program has not been run on this instance yet" | Click **Run** at the top |
