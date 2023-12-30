import json
import math
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi_utilities import repeat_every

import settings
import pytz
from database import models
import logging
from datetime import datetime, timedelta
from tortoise.functions import Count, Sum
# import Q from tortoise orm:
from tortoise.expressions import Q, Subquery

S3_LINK = settings.S3_LINK

router = APIRouter()

cached_weekly_program_path = "./cached_program_weekly.json"
logging.getLogger().setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
@router.get("/story")
async def get_story(storyGlobalId: str):
    try:
        story = models.Story.filter(
            storyGlobalId=storyGlobalId,
            release_date__lte=datetime.now()
        ).limit(1)
        result = await models.Story_Pydantic.from_queryset(story)
        if result:
            row = result[0]
            return {
                "isFound": True,
                "title": row.title,
                "description": row.description,
                "author": row.author,
                "patreonusername": row.patreonusername,
                "cdn": S3_LINK,
            }
        else:
            story = models.Story.filter(
                storyGlobalId=storyGlobalId
            ).limit(1)
            result = await models.Story_Pydantic.from_queryset(story)
            if result:
                # TODO: let access to user with story pass
                #     row = result[0]
                raise HTTPException(status_code=404, detail="Not Published")

        raise HTTPException(status_code=404, detail="Not found")
    except Exception as e:
        logging.error(e)
        return {
            "isFound": False,
            "title": "",
            "description": "",
            "author": "",
            "patreonusername": "",
            "cdn": "",
        }


# create another endpoint that will print out server metadata:
@router.get("/")
async def get_server_metadata():
    """
    Get the server metadata.

    This function retrieves the server metadata by accessing
    the `SERVER_METADATA` variable in the `settings` module.

    Returns:
        The server metadata as a dictionary.

    Raises:
        Exception: If there is an error retrieving the server metadata.
    """
    try:
        meta = settings.SERVER_METADATA
        meta["theme"] = {
            "primary": settings.THEME["primary"],
        }
        return meta
    except Exception as e:
        logging.error(e)
        return {}


@router.get("/stories")
async def get_stories(
        page: int = Query(1, description="Page number, default: 1"),
        seriesGlobalId: Optional[str] = Query(
            None, description="Series global id"
        ),
        sort_by: str = Query("date", description="Sort by 'date' or 'name"),
        tags_required: List[str] = Query([], description="Required tags"),
        include_upcoming: int = Query(0,
                                      description="Include upcoming releases")
):
    print(seriesGlobalId)
    per_page = 60
    try:
        skip = (page - 1) * per_page
        limit = per_page
        stories_query = models.Story.all()

        if not include_upcoming:
            stories_query = stories_query.filter(
                release_date__lte=datetime.now()
            )

        if seriesGlobalId:
            stories_query = stories_query.filter(
                series__seriesGlobalId=seriesGlobalId
            )

        if tags_required:
            tags_required = tags_required[:3]
            print(tags_required)
            stories_query = stories_query.filter(
                series__tags_rel__tag__tag__in=tags_required
            )

        if sort_by == "date":
            stories_query = stories_query.order_by("idstory")
        elif sort_by == "name":
            stories_query = stories_query.order_by("title")
        else:
            raise HTTPException(
                status_code=400, detail="Invalid sort_by value"
            )
        print(stories_query.sql())
        stories = await models.Story_Pydantic.from_queryset(
            stories_query.offset(skip).limit(limit + 1)
        )

        if stories:
            next = None
            if len(stories) == limit + 1:
                next = page + 1

            for ix, story in enumerate(stories):
                stories[ix] = story.model_dump()
                stories[ix]["cdn"] = S3_LINK

            return {
                "isFound": True,
                "next": next,
                "page": page,
                "stories": stories[:limit],
            }
        raise Exception("No stories found")
    except Exception as e:
        logging.error(e)
        return {"isFound": False, "stories": []}


@router.get("/landing")
async def get_landing():
    try:
        meta = settings.SERVER_METADATA
        meta["theme"] = {
            "primary": settings.THEME["primary"],
        }
    except Exception as e:
        logging.error(e)
        meta = {}

    series_query = models.Series.all().order_by("-idseries").limit(10)
    series = await models.SeriesWithRels_Pydantic.from_queryset(series_query)
    if series:
        for ix, single_series in enumerate(series):
            series[ix] = single_series.model_dump()
            del series[ix]["stories"]
            del series[ix]["tags_rel"]
    else:
        series = []
    meta["series"] = series
    return meta


@router.get("/series")
async def get_series(
        page: int = Query(1, description="Page number, default: 1"),
        sort_by: str = Query("new", description="Sort by 'new' or 'name"),
        tags_required: List[str] = Query([], description="Required tags"),
):
    per_page = 60
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

        series_query = series_query.filter(stories__idstory__in=Subquery(
            models.Story.filter(release_date__lte=datetime.now()).values(
                "idstory"))).distinct()

        # If tortoise orm's Count can introduce "filter" in the future,
        # this will be used instead:
        # series_query = series_query.annotate(
        #     story_count=Count("stories", filter=Q(release_date__lte=datetime.now()))
        # ).filter(story_count__gte=1)

        if sort_by == "new":
            series_query = series_query.order_by("-idseries")
        elif sort_by == "name":
            series_query = series_query.order_by("name")
        else:
            raise HTTPException(
                status_code=400, detail="Invalid sort_by value"
            )

        series = await models.SeriesWithRels_Pydantic.from_queryset(
            series_query.offset(skip).limit(limit + 1)
        )
        if series:
            for ix, single_series in enumerate(series):
                series[ix] = single_series.model_dump()
                del series[ix]["stories"]
                del series[ix]["tags_rel"]
            next_page = None
            if len(series) == limit + 1:
                next_page = page + 1
            return {
                "isFound": True,
                "next": next_page,
                "page": page,
                "series": series,
            }

        raise Exception("No series found")
    except Exception as e:
        logging.error(e)
        return {"isFound": False, "next": None, "page": page, "series": []}


@router.get("/program")
async def get_current_week_program():
    # using FileResponse wouldn't help when we switch to a proper cache. So we'll load the json instead:
    cached_program = await get_cached_weekly_program()

    if cached_program:
        return {"status": "success", "data": cached_program}
    else:
        return {"status": "error", "message": "Program not available."}


async def get_cached_weekly_program():
    try:
        with open(cached_weekly_program_path, "r") as file:
            cached_program = json.load(file)
        logging.info("Received weekly program from cache")
        return cached_program
    except FileNotFoundError:
        logging.info("Received weekly program without cache")
        return await build_weekly_program()
    except Exception as e:
        logging.error(e)
        return None


async def build_weekly_program():
    try:
        # Calculate the start and end date of the current week
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Query for stories within the current week
        current_week_stories = await models.Story.filter(
            release_date__gte=start_of_week,
            release_date__lte=end_of_week
        ).order_by("release_date").prefetch_related('series')

        # Format the response
        response_data = {
            "week_start_date": start_of_week.strftime("%Y-%m-%d"),
            "week_end_date": end_of_week.strftime("%Y-%m-%d"),
            "stories": []
        }
        for story in current_week_stories:
            series_name = story.series.name if story.series else None
            series_global_id = story.series.seriesGlobalId if story.series else None

            story_release_date_minute = story.release_date.minute
            rounded_release_date = story.release_date + timedelta(
                minutes=(
                                30 - story_release_date_minute % 30
                        ) % 30
            ) if story_release_date_minute != 0 and story_release_date_minute != 30 else story.release_date

            # Check if the story is released
            if rounded_release_date <= datetime.now(pytz.utc):
                story_global_id = story.storyGlobalId
            else:
                story_global_id = None

            response_data["stories"].append({
                "idstory": story.idstory,
                "title": story.title,
                "description": story.description,
                "release_date": rounded_release_date.strftime("%Y-%m-%dT%H:%M:00Z"),
                # "release_date": story.release_date,
                "storyGlobalId": story_global_id,
                "series_name": series_name,
                "seriesGlobalId": series_global_id
            })

        with open(cached_weekly_program_path, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, default=str)
            f.flush()
        return response_data

    except Exception as e:
        logging.error(e)
        return None
        # Handle exceptions and log errors


@router.on_event("startup")
@repeat_every(seconds=60)  # 1 minute
async def task_build_weekly_program() -> None:
    now = datetime.now()
    if now.minute in [1, 31]:
        logging.info("Rebuilding weekly program for minute: {}".format(now.minute))
        await build_weekly_program()
