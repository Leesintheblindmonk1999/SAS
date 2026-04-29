from sqlalchemy.orm import Session
from app.db import models

def get_user_by_api_key(db: Session, api_key_hash: str):
    return db.query(models.User).filter(models.User.api_key_hash == api_key_hash).first()
