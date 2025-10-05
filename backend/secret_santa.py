
from handler import setup_database
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Text

setup_database()  # Ensure the engine is initialized
from handler import engine

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Import models from a single source to avoid duplication
from db_utils.setup_table import Wishlist, SecretSanta
# CRUD functions
def create_wishlist_item(user_id, item_name, item_comment=None, item_link=None):
	with SessionLocal() as session:
		item = Wishlist(
			user_id=user_id,
			item_name=item_name,
			item_comment=item_comment,
			item_link=item_link
		)
		session.add(item)
		session.commit()
		return item

def get_wishlist_items(user_id):
	with SessionLocal() as session:
		return session.query(Wishlist).filter_by(user_id=user_id).all()

def update_wishlist_item(user_id, item_name, item_comment=None, item_link=None):
	with SessionLocal() as session:
		item = session.query(Wishlist).filter_by(user_id=user_id, item_name=item_name).first()
		if item:
			if item_comment is not None:
				item.item_comment = item_comment
			if item_link is not None:
				item.item_link = item_link
			session.commit()
		return item

def delete_wishlist_item(user_id, item_name):
	with SessionLocal() as session:
		item = session.query(Wishlist).filter_by(user_id=user_id, item_name=item_name).first()
		if item:
			session.delete(item)
			session.commit()
			return True
		return False

def create_secret_santa(giver, receiver):
	with SessionLocal() as session:
		entry = SecretSanta(giver=giver, receiver=receiver)
		session.add(entry)
		session.commit()
		return entry

def get_secret_santa(giver):
	with SessionLocal() as session:
		return session.query(SecretSanta).filter_by(giver=giver).first()

def update_secret_santa(giver, receiver):
	with SessionLocal() as session:
		entry = session.query(SecretSanta).filter_by(giver=giver).first()
		if entry:
			entry.receiver = receiver
			session.commit()
		return entry

def delete_secret_santa(giver):
	with SessionLocal() as session:
		entry = session.query(SecretSanta).filter_by(giver=giver).first()
		if entry:
			session.delete(entry)
			session.commit()
			return True
		return False