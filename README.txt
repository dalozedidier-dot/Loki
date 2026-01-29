Zip band_suite entrypoint v2

Pourquoi v2
- Ton workflow echoue avec rc=2, sans message utile.
- Ici, toute erreur imprime aussi la fin du log correspondant dans la console GitHub.

A copier dans ton repo
- scripts/ci_band_suite.py
- .github/workflows/band_suite_isolated.yml

Ensuite commit + push, relance band-suite (isolated).
Si ca echoue encore, le log dans l'onglet Actions te montrera l'erreur exacte,
et l'artefact contiendra _ci_out/*.log.
