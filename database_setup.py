from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import create_engine

from flask import jsonify

engine = create_engine('sqlite:///catalog.db')
DBSession = sessionmaker(bind=engine)
session = DBSession()
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    gid = Column(String(100))
    name = Column(String(250), nullable=False)
    email = Column(String(500), nullable=False)
    picture = Column(String(1000))


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(String(1000))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship("Category")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, cascade="save-update")

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'user_id': self.user_id
        }


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, cascade="save-update")
    items = relationship("Item", cascade="all, delete-orphan")

    @property
    def serialize(self):
        items = session.query(Item).filter_by(category_id=self.id)
        items_data = [i.serialize for i in items]
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'items': items_data
        }


Base.metadata.create_all(engine)
