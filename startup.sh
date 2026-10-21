#!/bin/sh
set -eu

# Serving must never provision, migrate, seed, or clean either database.
exec python -B -m app.start_backend
