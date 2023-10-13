from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `series` (
    `idseries` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `seriesGlobalId` VARCHAR(20) NOT NULL,
    `creator` VARCHAR(45) NOT NULL,
    `episodes` INT NOT NULL  DEFAULT 1
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `series_tags_rel` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `series_id` INT NOT NULL,
    `tag_id` INT NOT NULL,
    CONSTRAINT `fk_series_t_series_3dfed8f9` FOREIGN KEY (`series_id`) REFERENCES `series` (`idseries`) ON DELETE CASCADE,
    CONSTRAINT `fk_series_t_tags_11cf0435` FOREIGN KEY (`tag_id`) REFERENCES `tags` (`idtag`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `stories` (
    `idstory` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(45),
    `description` VARCHAR(45),
    `author` VARCHAR(45),
    `patreonusername` VARCHAR(45),
    `storyGlobalId` VARCHAR(45),
    `series_id` INT NOT NULL,
    CONSTRAINT `fk_stories_series_a4ea5833` FOREIGN KEY (`series_id`) REFERENCES `series` (`idseries`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `tags` (
    `idtag` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `tag` VARCHAR(45) NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `series`;
        DROP TABLE IF EXISTS `series_tags_rel`;
        DROP TABLE IF EXISTS `stories`;
        DROP TABLE IF EXISTS `tags`;"""
