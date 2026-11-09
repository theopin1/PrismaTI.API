import os
from pathlib import Path
from dotenv import load_dotenv


def load_config():
    load_dotenv(Path(__file__).resolve().parents[3] / '.env')
    url = os.getenv('DATABASE_URL', '')
    secret = os.getenv('SECRET_KEY', '')
    if not url.startswith('postgresql+psycopg://'):
        raise RuntimeError('Configure DATABASE_URL para PostgreSQL com psycopg no .env.')
    if len(secret) < 32 or secret.startswith('CHANGE_ME'):
        raise RuntimeError('Configure SECRET_KEY aleatória com pelo menos 32 caracteres.')
    return {'DATABASE_URL': url, 'SECRET_KEY': secret}
