from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `stories` ADD `username` VARCHAR(45) NOT NULL  DEFAULT 'admin';
        ALTER TABLE `story_submissions` ADD `username` VARCHAR(45) NOT NULL  DEFAULT 'admin';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `stories` DROP COLUMN `username`;
        ALTER TABLE `story_submissions` DROP COLUMN `username`;"""
