# Superset Configuration for Data Mesh MVP
import os

# Secret key for session management
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'datamesh-mvp-secret-key-change-in-prod')

# Database configuration
SQLALCHEMY_DATABASE_URI = 'postgresql://superset:superset@superset-postgres:5432/superset'

# Redis for caching and celery
REDIS_HOST = os.environ.get('REDIS_HOST', 'superset-redis')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': REDIS_HOST,
    'CACHE_REDIS_PORT': REDIS_PORT,
    'CACHE_REDIS_DB': 1,
}

# Disable CSRF for simplicity in dev
WTF_CSRF_ENABLED = False

# Enable SQL Lab
ENABLE_SQL_LAB = True

# Feature flags
FEATURE_FLAGS = {
    'ENABLE_TEMPLATE_PROCESSING': True,
}

# Talisman configuration (for HTTPS headers, disabled for local dev)
TALISMAN_ENABLED = False

# Enable public role
PUBLIC_ROLE_LIKE = 'Gamma'

