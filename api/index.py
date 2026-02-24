import sys
import os

# Make the project root importable so `from backend.main import app` works
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app  # noqa: E402
from mangum import Mangum      # noqa: E402

handler = Mangum(app, lifespan="off")
