from peewee import *

database = SqliteDatabase('smk.sqlite3.db')

class BaseModel(Model):
    class Meta:
        database = database

class Conf(BaseModel):
    key = CharField(unique=True)
    value = CharField()

class Host(BaseModel):
    name = CharField(unique=True)
    address = CharField()
    user = CharField()
    port = IntegerField()
    sshkey = CharField()

class Miner(BaseModel):
    name = CharField(unique=True)
    pubkey = CharField(unique=True)
    host = ForeignKeyField(Host, backref='hosts')
    container = CharField()
    command = CharField()
    fixtime = IntegerField(default=0)

    def gethost(self):
        pass

def create_tables():
    with database:
        database.create_tables([Conf, Host, Miner])
