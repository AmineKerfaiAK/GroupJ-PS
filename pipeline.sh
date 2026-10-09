#!/bin/bash
python3 generateur/generateur.py --suite -o instances/generated || exit 1
python3 generateur/validateur.py instances instances/generated || exit 1
g++ -std=c++17 -O2 my_solution.cpp -o solution 2>/dev/null || exit 1
mkdir -p outputs
for f in instances/*.in instances/generated/*.in; do
  n=$(basename "$f" .in)
  echo
  echo "==================== $n ===================="
  ./solution < "$f" > "outputs/$n.out" 2>/dev/null
  echo "score.py : $(python3 score.py "$f" "outputs/$n.out")"
  python3 statistiques/stats_instance.py "$f" > /dev/null
  python3 statistiques/stats_solution.py "$f" "outputs/$n.out" | sed -n '2,5p'
done
echo
echo "reports and charts: statistiques/sorties/<instance>/"
