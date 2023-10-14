from typing import List

from fastapi import APIRouter, HTTPException, Query
from tortoise.expressions import Q

import settings
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


# create another endpoint that will print out server metadata:
@router.get("/")
async def get_server_metadata():
    """
    Get the server metadata.

    This function retrieves the server metadata by accessing the `SERVER_METADATA` variable in the `settings` module.

    Returns:
        The server metadata as a dictionary.

    Raises:
        Exception: If there is an error retrieving the server metadata.
    """
    try:
        return settings.SERVER_METADATA
    except Exception as e:
        logging.error(e)
        return {}


@router.get("/stories")
async def get_stories(
        page: int = Query(1, description="Page number, default: 1"),
        sort_by: str = Query("new", description="Sort by 'new' or 'name"),
        tags_required: List[str] = Query([], description="Required tags")
):
    per_page = 10
    try:
        skip = (page - 1) * per_page
        limit = per_page

        stories_query = models.Story.all()

        if tags_required:
            tags_required = tags_required[:3]
            print(tags_required)
            stories_query = stories_query.filter(
                series__tags_rel__tag__tag__in=tags_required
            )

        if sort_by == "new":
            stories_query = stories_query.order_by("-idstory")
        elif sort_by == "name":
            stories_query = stories_query.order_by("title")
        else:
            raise HTTPException(status_code=400,
                                detail="Invalid sort_by value")
        print(stories_query.sql())
        stories = await models.Story_Pydantic.from_queryset(
            stories_query.offset(skip).limit(limit + 1))

        if stories:
            next = None
            if len(stories) == limit + 1:
                next = page + 1
            return {"isFound": True, "next": next, "page": page,
                    "stories": stories[:limit]}
        raise Exception("No stories found")
    except Exception as e:
        logging.error(e)
        return {"isFound": False, "stories": []}


@router.get("/series")
async def get_series(
        page: int = Query(1, description="Page number, default: 1"),
        sort_by: str = Query("new", description="Sort by 'new' or 'name"),
        tags_required: List[str] = Query([], description="Required tags")
):
    per_page = 10
    page = min(page, 20)
    try:
        skip = (page - 1) * per_page
        limit = per_page

        series_query = models.Series.all()

        if tags_required:
            tags_required = tags_required[:3]
            series_query = series_query.filter(
                tags_rel__tag__tag__in=tags_required
            )

        if sort_by == "new":
            series_query = series_query.order_by("-idseries")
        elif sort_by == "name":
            series_query = series_query.order_by("name")
        else:
            raise HTTPException(status_code=400,
                                detail="Invalid sort_by value")

        series = await models.Series_Pydantic.from_queryset(
            series_query.offset(skip).limit(limit + 1))
        if series:
            next_page = None
            if len(series) == limit + 1:
                next_page = page + 1
            return {"isFound": True,
                    "next": next_page,
                    "page": page,
                    "series": series}

        raise Exception("No series found")
    except Exception as e:
        logging.error(e)
        return {"isFound": False,
                "next": None,
                "page": page,
                "series": []
                }