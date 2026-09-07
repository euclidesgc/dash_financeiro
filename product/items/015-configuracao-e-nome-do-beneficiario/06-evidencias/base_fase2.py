import os
from pathlib import Path

from app.auth.seed import seed_user
from app.db import connect
from app.migrate import run_migrations
from tests.conftest import transaction
from tests.test_plan import MONTHS, prepare, rent, salary

# A base with six closed months, which is the base the phase 2 criteria
# describe: a median window of twelve has to be refused, and over the owner's
# thirteen closed months it would be accepted and the criterion would pass
# without ever exercising the refusal.
target = os.environ["DASH_DB_PATH"]
Path(target).unlink(missing_ok=True)
run_migrations(target)

conn = connect(target)
seed_user(conn, os.environ["LOGIN"], os.environ["PASSWORD"])
extra = transaction(
    "out-extra", f"{MONTHS[-1]}-20", -1000.0, descricao="Moradia", categoria="Housing"
)
prepare(conn, salary(5000.0) + rent(-1000.0) + [extra])
print("meses fechados:", len(MONTHS))
conn.close()
