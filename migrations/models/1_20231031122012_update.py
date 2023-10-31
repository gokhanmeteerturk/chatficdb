from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `stories` ADD `release_date` DATETIME(6) NOT NULL DEFAULT NOW(6);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `stories` DROP COLUMN `release_date`;"""
