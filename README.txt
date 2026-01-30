Structure de travail DD / CI (pack minimal)

Objectif
- Ranger sans perdre d'information
- Garder la traçabilité (qu'est-ce qui vient d'où)
- Éviter toute suppression définitive tant que les incohérences ne sont pas levées

Arborescence proposée
- sboms/                     JSON SPDX
- csvs/github_insights/       Exports GitHub "Commits", "Code frequency"
- csvs/ci_metrics/            Exports CI (failure rate, runtime, queue_seconds, etc.)
- images/                     Captures graphiques et pages exportées
- archives/                   Doublons et versions à écarter mais à conserver
- externes/                   Projets non liés (client-python, coingecko-*, tradingeconomics-*)

Méthode recommandée
1) Déplacer sans renommer dans un premier temps (juste classer par type)
2) Remplir RENAMING_MAP.csv au fur et à mesure des renommages
3) Pour chaque fichier renommé, noter l'origine dans INDEX.md (repo, date d'export, source UI ou outil)

Point critique: incohérence Code frequency
- Ne supprime pas "Code frequency (1).csv" tant que tu n'as pas validé lequel est correct.
- Range les deux dans csvs/github_insights/ et renomme temporairement:
  code_frequency_export_A.csv
  code_frequency_export_B.csv
- Renseigne NOTES_INCOHERENCES.md avec les différences observées.

Dernière mise à jour: 2026-01-30
