import bcrypt
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    )
from .meta import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    nickname = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    role = Column(String(10), nullable=False)
    password_hash = Column(Text)

    def set_password(self, pw):
        pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
        self.password_hash = pwhash.decode('utf8')

    def check_password(self, pw):
        '''return True if password right'''
        if self.password_hash is not None:
            expected_hash = self.password_hash.encode('utf8')
            return bcrypt.checkpw(pw.encode('utf8'), expected_hash)
        return False

    def __repr__(self):
        return "<User(nickname='%s' email='%s' role='%s')>" % (
                self.nickname, self.email, self.role)