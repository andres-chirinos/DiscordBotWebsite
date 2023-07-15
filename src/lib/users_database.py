import pymongo, json

class DatabaseClient:
    def __init__(self, app, mongo_url:str=None, *args, **kwargs):
        self.Memoria = pymongo.MongoClient(mongo_url or app.config["MONGO_URL"])
        self.registermetadata = list(app.config["METADATA_SET"])
        super().__init__(*args, **kwargs)

    async def insert_one(self, database: str, collection: str, document):
        Database = self.Memoria.get_database(database)
        UserCollection = Database.get_collection(collection)
        data = UserCollection.insert_one(document)


    async def find_one(self, database: str, collection: str, filter):
        Database = self.Memoria.get_database(database)
        UserCollection = Database.get_collection(collection)
        data = UserCollection.find_one(filter)
        return data


    async def update_one(self, database: str, collection: str, filter, update):
        Database = self.Memoria.get_database(database)
        UserCollection = Database.get_collection(collection)
        UserCollection.update_one(filter, update)


    async def create_identification(self, id: int):

        insert = {
            "type": "identification",
            "platform_username": "Steve",
        }

        for registerdata in self.registermetadata:
            insert[registerdata["key"]] = None

        await self.insert_one(
            "master",
            str(id),
            insert,
        )

        return await self.find_one("master", str(id), filter={"type": "identification"})


    async def get_role_connection(self, id: int):
        Identification = await self.find_one("master", str(id), {"type": "identification"})

        if not Identification:
            Identification = await self.create_identification(id)

        metadata = dict()
        for registerdata in self.registermetadata:
            key = registerdata["key"]
            if Identification.get(key):
                metadata[key] = Identification[key]
            else:
                await self.update_one(
                    "master",
                    str(id),
                    filter={"type": "identification"},
                    update={"$set": {key: None}},
                )

        role_connection_data = {
            "platform_name": Identification["type"],
            "platform_username": Identification["platform_username"],
            "metadata": metadata,
        }
        return role_connection_data
