#!/usr/bin/env python
"""
Bootstrap script to initialize Superset with Trino database connection
"""
import logging
from superset.app import create_app
from superset import db
from superset.models.core import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_trino_database():
    """Add Trino database connection if it doesn't exist"""
    app = create_app()
    with app.app_context():
        # Check if Trino database already exists
        existing = db.session.query(Database).filter_by(database_name='Trino - Data Mesh').first()
        if existing:
            logger.info("Trino database connection already exists, skipping...")
            return
        
        # Create Trino database connection
        trino_db = Database(
            database_name='Trino - Data Mesh',
            sqlalchemy_uri='trino://trino@datamesh-trino:8080/mariadb',
            expose_in_sqllab=True,
            allow_run_async=True,
            allow_ctas=True,
            allow_cvas=True,
            allow_dml=True,
            allow_file_upload=False,
        )
        
        db.session.add(trino_db)
        db.session.commit()
        logger.info("Successfully added Trino database connection!")

if __name__ == '__main__':
    add_trino_database()

