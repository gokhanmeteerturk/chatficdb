from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `story_submissions` (
    `idstorysubmission` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `title` VARCHAR(45),
    `description` VARCHAR(45),
    `story_text` LONGTEXT,
    `author` VARCHAR(45),
    `storyGlobalId` VARCHAR(45),
    `submission_date` DATETIME(6) NOT NULL,
    `files_list` JSON,
    `upload_links` JSON,
    `status` SMALLINT NOT NULL  COMMENT 'NOT_ACCEPTED: 15\nWAITING_VALIDATION: 20\nVALIDATION_FAILED: 25\nREPEATED: 26\nWAITING_USER_UPLOAD: 30\nUSER_UPLOAD_FAILED: 35\nWAITING_POST_PROCESSING: 40\nPOST_PROCESSING_FAILED: 45\nPROCESSED: 60' DEFAULT 20,
    `logs` LONGTEXT,
    `series_id` INT NOT NULL,
    `story_id` INT,
    CONSTRAINT `fk_story_su_series_c211a4a1` FOREIGN KEY (`series_id`) REFERENCES `series` (`idseries`) ON DELETE CASCADE,
    CONSTRAINT `fk_story_su_stories_3fb30624` FOREIGN KEY (`story_id`) REFERENCES `stories` (`idstory`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='Represents a story submission in the database.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `story_submissions`;"""
