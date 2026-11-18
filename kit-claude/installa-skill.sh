#!/usr/bin/env bash
# Installa nel repository corrente le skill di design (impeccable, Taste, Emil Kowalski, GSAP...),
# il CLAUDE.md e i design-references, prendendoli dal branch dove sono salvati.
# Uso: dalla cartella principale del repository, `bash installa-skill.sh`
set -euo pipefail

REPO="https://github.com/gabrielebonacci7-coder/Portale-piscina"
BRANCH="claude/serene-edison-4osy11"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git clone --quiet --depth 1 --branch "$BRANCH" --filter=blob:none --sparse "$REPO" "$TMP/kit"
git -C "$TMP/kit" sparse-checkout set .claude/skills design-references
git -C "$TMP/kit" checkout --quiet

mkdir -p .claude/skills
cp -r "$TMP/kit/.claude/skills/." .claude/skills/
cp -r "$TMP/kit/design-references" .
cp "$TMP/kit/skills-lock.json" .

# CLAUDE.md: se esiste già lo lascia com'è e aggiunge le regole in fondo
if [ -f CLAUDE.md ]; then
  if ! grep -q "Quando si fa un sito o un'interfaccia" CLAUDE.md; then
    printf '\n' >> CLAUDE.md
    cat "$TMP/kit/CLAUDE.md" >> CLAUDE.md
  fi
else
  cp "$TMP/kit/CLAUDE.md" CLAUDE.md
fi

echo "Fatto: $(ls .claude/skills | wc -l) skill in .claude/skills"
echo "Ora: git add .claude CLAUDE.md design-references skills-lock.json && git commit && git push"
echo "Poi apri una nuova sessione di Claude Code su questo repository."
