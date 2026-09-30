#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> System packages (graphviz for pygraphviz / graph edit distance metric)"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  build-essential pkg-config graphviz libgraphviz-dev
sudo rm -rf /var/lib/apt/lists/*

# uv and Claude Code are installed by devcontainer features (see devcontainer.json).
# The ~/.claude volume is created root-owned on first mount -> hand it to the user.
sudo chown -R "$(id -u):$(id -g)" "$HOME/.claude" 2>/dev/null || true

echo "==> SciGym submodule"
git submodule update --init --recursive

echo "==> Python env (Python 3.10 + SciGym, via uv)"
uv python install 3.10
uv sync

# libroadrunner's wheel links against libpython3.10.so dynamically, which the
# uv-managed interpreter keeps in its own lib/ dir -> make it visible to ld.so.
PY_LIBDIR="$(uv run python -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))')"
echo "$PY_LIBDIR" | sudo tee /etc/ld.so.conf.d/uv-python310.conf >/dev/null
sudo ldconfig

echo "==> Smoke test"
uv run python -c "import scigym, tellurium, roadrunner, libsbml, pygraphviz; print('scigym OK, roadrunner', roadrunner.__version__)"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — fill in VERCEL_AI_GATEWAY_API_KEY if not using Codespaces secrets."
fi

echo "Done. Run 'claude' to start Claude Code."
