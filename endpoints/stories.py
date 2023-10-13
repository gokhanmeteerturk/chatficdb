from fastapi import APIRouter, HTTPException

from database import models
import logging

S3_LINK = "https://topaltdb.s3.us-east-2.amazonaws.com"

router = APIRouter()


@router.get("/story")
async def get_story(storyGlobalId: str):
    try:
        story = models.Story.filter(storyGlobalId=storyGlobalId).limit(1)
        result = await models.Story_Pydantic.from_queryset(story)
        if result:
            row = result[0]
            return {"isFound": True, "title": row.title,
                    "description": row.description, "author": row.author,
                    "patreonusername": row.patreonusername, "cdn": S3_LINK}
        raise HTTPException(status_code=404, detail="Not found")
    except Exception as e:
        logging.error(e)
        return {"isFound": False, "title": "", "description": "", "author": "",
                "patreonusername": "", "cdn": ""}


@router.get("/stories")
async def get_stories():
    try:
        stories = await models.Story_Pydantic.from_queryset(models.Story.all())
        # return {"isFound": True, "stories": get_latest_stories_from_db()}
        return {"isFound": True, "stories": stories}
    except Exception as e:
        logging.error(e)
        return {"isFound": False, "stories": []}
