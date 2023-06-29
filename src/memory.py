import pymongo, requests, json, os
from __init__ import Cache
from datetime import datetime

Memoria = pymongo.MongoClient(
    os.getenv(
        "MONGO_URL",
        "mongodb://mongo:QoodY7GX6kzhHebGIo2Q@containers-us-west-94.railway.app:7993",
    )
)


async def insert_one(database: str, collection: str, document):
    Database = Memoria.get_database(database)
    UserCollection = Database.get_collection(collection)
    data = UserCollection.insert_one(document)


async def find_one(database: str, collection: str, filter):
    Database = Memoria.get_database(database)
    UserCollection = Database.get_collection(collection)
    data = UserCollection.find_one(filter)
    return data


async def update_one(database: str, collection: str, filter, update):
    Database = Memoria.get_database(database)
    UserCollection = Database.get_collection(collection)
    UserCollection.update_one(filter, update)


async def create_identification(id: int):
    registermetadata = json.loads(Cache.get("registermetadata"))

    insert = {
        "type": "identification",
        "platform_username": "Steve",
    }

    for registerdata in registermetadata:
        insert[registerdata["key"]] = None

    await insert_one(
        "master",
        str(id),
        insert,
    )

    return await find_one("master", str(id), filter={"type": "identification"})


async def get_role_connection(id: int):
    registermetadata = json.loads(Cache.get("registermetadata"))
    Identification = await find_one("master", str(id), {"type": "identification"})

    if not Identification:
        Identification = await create_identification(id)

    metadata = dict()
    for registerdata in registermetadata:
        key = registerdata["key"]
        if Identification.get(key):
            metadata[key] = Identification[key]
        else:
            await update_one(
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


async def push_role_connection(tokens, body):
    # GET/PUT /users/@me/applications/:id/role-connection
    url = f"https://discord.com/api/v10/users/@me/applications/{os.environ.get('DISCORD_CLIENT_ID')}/role-connection"
    data = json.dumps(body)
    response = requests.put(
        url,
        data,
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
            "Content-Type": "application/json",
        },
    )
    if not response.ok:
        raise Exception(
            f"Error putting discord metadata: [{response.status_code}] {response.text}"
        )


async def update_role_connection(tokens, id: int):
    await update_one(
        "master",
        str(id),
        {"type": "identification"},
        {"$set": {"update": str(datetime.now().isoformat())}},
    )
    body = await get_role_connection(id)
    return await push_role_connection(tokens, body)


# async def get_role_connection(access_token, id:int):
#    # GET/PUT /users/@me/applications/:id/role-connection
#    url = f"https://discord.com/api/v10/users/@me/applications/{os.environ.get('CLIENT_ID')}/role-connection"
#    response = requests.get(url, headers={'Authorization': f'Bearer {access_token}'})
#    if response.ok:
#        data = response.json()
#        if data == {}:
#            data = role_connection_data
#        data['metadata'] = get_metadata(id)
#        return data
#    else:
#        raise Exception(f'Error getting discord metadata: [{response.status_code}] {response.text}')
