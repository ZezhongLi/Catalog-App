from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import *
import datetime

DBSession = sessionmaker(bind=engine)
session = DBSession()

session.query(Category).delete()
session.query(Item).delete()
session.query(User).delete()

user1 = User(name="Zezhong Li",
            email="neillizezhong@gmail.com",
            picture="http://dummyimage.com/200x200.png/ff4444/ffffff")
session.add(user1)
session.commit()

category1 = Category(name="Soccer", user_id=1)
session.add(category1)

category2 = Category(name="Snowboarding", user_id=1)
session.add(category2)

session.commit()

item1_desc = """
            A type of eyewear fit tightly against the face so that 
            the only light entering is through the slits, 
            and soot is sometimes applied to the inside to 
            help cut down on glare.
            """
item1 = Item(name="Goggles",
            date=datetime.datetime.now(),
            description=item1_desc,
            category_id=2,
            user_id=1)

session.add(item1)

item2_desc = """
            Snowboards are boards where both feet are secured 
            to the same board, which are wider than skis, 
            with the ability to glide on snow.
            """
item2 = Item(name="Snowboard",
            date=datetime.datetime.now(),
            description=item2_desc,
            category_id=2,
            user_id=1)

session.add(item2)

item3_desc = """
            A shin guard or shin pad is a piece of 
            equipment worn on the front of a player's 
            shin to protect them from injury. 
            """
item3 = Item(name="Two shinguards",
            date=datetime.datetime.now(),
            description=item3_desc,
            category_id=1,
            user_id=1)

session.add(item3)

item4_desc = """
            Shirt of the game. 
            """
item4 = Item(name="Jersey",
            date=datetime.datetime.now(),
            description=item4_desc,
            category_id=1,
            user_id=1)

session.add(item4)

item5_desc = """
            Soccer Cleats.
            """
item5 = Item(name="Soccer Cleats",
            date=datetime.datetime.now(),
            description=item5_desc,
            category_id=1,
            user_id=1)

session.add(item5)

session.commit()

print("Sample data has been added.")