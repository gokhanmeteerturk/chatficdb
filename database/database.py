from tortoise import Tortoise, run_async

import settings


async def init():
    await Tortoise.init(
        config=settings.TORTOISE_CONFIG,
    )
    # Generate the schema
    await Tortoise.generate_schemas(safe=True)


def run():
    run_async(init())
