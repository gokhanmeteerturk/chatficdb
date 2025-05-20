import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional

import feedgenerator  # Install it using: pip install feedgenerator
import pytz
from fastapi import APIRouter, HTTPException, Query, Header
from fastapi_utilities import repeat_every
from pydantic.types import PositiveInt, NonNegativeInt
from starlette.responses import FileResponse
from tortoise.exceptions import OperationalError
# import Q from tortoise orm:
from tortoise.expressions import Subquery, RawSQL
from tortoise.transactions import atomic

import settings
from database import models
from database.models import SeriesIn_Pydantic
from endpoints.response_models import ItemExistsResponse, StoryResponse, \
    ServerMetadataResponse, MetadataTheme, SeriesLookupResponse, \
    StoryBasicModel, StoriesResponse, SeriesBasicModel, SeriesResponse, \
    LatestSeriesResponse, WeeklyProgramResponse, SeriesTagsResponse, \
    TagsResponse
from helpers.utils import getUniqueRandomStoryKey
from helpers.auth import validate_token  # Import validate_token

S3_LINK = settings.S3_LINK
FEED_PATH = "/feed.xml"

router = APIRouter()

CACHED_WEEKLY_PROGRAM_PATH = "./cached_program_weekly.json"
logging.getLogger().setLevel(
    logging.INFO if settings.DEBUG else logging.WARNING)


@router.get('/item', response_model=ItemExistsResponse, tags=["misc"])
async def check_item_exists(item_id: str = Query("", description="Series ID")) -> ItemExistsResponse:
    """
    Simple endpoint to verify if a series exists.
    Returns 200 if exists, 404 if not.

    This endpoint is called /items because in the future,
    it will be used to check different types of items as well.
    """
    try:
        exists = await models.Series.exists(
            seriesGlobalId=item_id
        )

        if not exists:
            raise HTTPException(status_code=404, detail="Item not found")

        return ItemExistsResponse(exists=True)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Item check error: {e}")
        raise HTTPException(status_code=500,
                            detail="Error checking item") from e


@router.get("/story", response_model=StoryResponse, tags=["stories & series"])
async def get_story(storyGlobalId: str = Query("", description="Story's Global ID")) -> StoryResponse:
    try:
        if settings.SHOW_PUBLISHED_ONLY:
            story = models.Story.filter(
                storyGlobalId=storyGlobalId,
                release_date__lte=datetime.now()).limit(1)
        else:
            story = models.Story.filter(
                storyGlobalId=storyGlobalId
            ).limit(1)
        result = await models.Story_Pydantic.from_queryset(story)

        if not result:
            story = models.Story.filter(
                storyGlobalId=storyGlobalId
            ).limit(1)
            result = await models.Story_Pydantic.from_queryset(story)

            if not result:
                raise HTTPException(status_code=404, detail="Not found")

            # TODO: let access to user with story pass
            #     row = result[0]
            # 403: FORBIDDEN
            raise HTTPException(status_code=403, detail="Not Published")

        if result:
            row = result[0]
            return StoryResponse(
                isFound=True,
                title=row.title,
                description=row.description,
                author=row.author,
                patreonusername=row.patreonusername,
                cdn=S3_LINK
            )

    except Exception as e:
        logging.error(e)
        return StoryResponse(
            isFound=False,
            title="",
            description="",
            author="",
            patreonusername="",
            cdn=""
        )


@router.get("/", response_model=ServerMetadataResponse, tags=["misc"])
async def get_server_metadata() -> ServerMetadataResponse:
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

        theme_data = {"primary": settings.THEME["primary"]}
        tags_data = dict(await models.Tag.all().values_list("idtag", "tag"))

        return ServerMetadataResponse(
            **meta,
            theme=MetadataTheme(**theme_data),
            tags=tags_data
        )
    except Exception as e:
        logging.error(e)
        return ServerMetadataResponse(theme=MetadataTheme(primary=""), tags={})


@router.get("/series/lookup", response_model=SeriesLookupResponse, tags=["stories & series"])
async def lookup_series_by_stories(
        story_ids: List[str] = Query(None, description="List of storyGlobalId values")
) -> SeriesLookupResponse:
    """
    Endpoint to return seriesGlobalId for given storyGlobalId values.
    """
    try:
        # Fetch all stories matching the provided storyGlobalId values
        stories = await models.Story.filter(
            storyGlobalId__in=story_ids).prefetch_related("series")

        if not stories:
            return SeriesLookupResponse(
                isFound=False,
                message="No matching series found",
                data={}
            )
        # Create a dictionary mapping storyGlobalId to seriesGlobalId
        story_to_series = {
            story.storyGlobalId: story.series.seriesGlobalId
            for story in stories if story.series
        }

        return SeriesLookupResponse(
            isFound=True,
            data=story_to_series
        )
    except Exception as e:
        logging.error(f"Error in lookup_series_by_stories: {e}")
        return SeriesLookupResponse(
            isFound=False,
            message="An error occurred while processing the request",
            data={}
        )


@router.get("/stories", response_model=StoriesResponse,
            tags=["stories & series"])
async def get_stories(
        page: NonNegativeInt = Query(1, description="Page number,"
                                                    " default: 1"),
        seriesGlobalId: Optional[str] = Query(
            None, description="Series global id"
        ),
        from_series_of_story: Optional[str] = Query(
            None, description="Story Global ID for series lookup"
        ),
        sort_by: str = Query("date", description="Sort by 'date', '-date' (reverse date), or 'name'"),
        tags_required: List[str] = Query([], description="Required tag "
                                                         "'names'. These are "
                                                         "limited to 3 tags."),
        include_upcoming: NonNegativeInt = Query(0,
                                                 description="Include upcoming"
                                                             " releases"),
        authorization: Optional[str] = Header(None, convert_underscores=False)
) -> StoriesResponse:

    per_page = 60
    try:
        skip = (page - 1) * per_page
        limit = per_page
        stories_query = models.Story.all()

        if include_upcoming and include_upcoming != 0:
            validate_token(authorization)  # Validate token if include_upcoming is true
        else:
            stories_query = stories_query.filter(
                release_date__lte=datetime.now()
            )

        if seriesGlobalId:
            stories_query = stories_query.filter(
                series__seriesGlobalId=seriesGlobalId
            )
        else:
            if from_series_of_story:
                stories = await models.Story.filter(
                    storyGlobalId=from_series_of_story).limit(1)
                series_id = None
                for story in stories:
                    series_id = story.series_id
                if series_id:
                    stories_query = stories_query.filter(
                        series__idseries=series_id
                    )

        if tags_required:
            tags_required = tags_required[:3]
            stories_query = stories_query.filter(
                series__tags_rel__tag__tag__in=tags_required
            )

        if sort_by == "date":
            stories_query = stories_query.order_by("idstory")
        elif sort_by == "-date":
            stories_query = stories_query.order_by("-idstory")
        elif sort_by == "name":
            stories_query = stories_query.order_by("title")
        else:
            raise HTTPException(
                status_code=400, detail="Invalid sort_by value"
            )
        stories = await models.Story_Pydantic.from_queryset(
            stories_query.offset(skip).limit(limit + 1)
        )

        if stories:
            next_page = page + 1 if len(stories) == limit + 1 else None
            story_list = [
                StoryBasicModel(
                    **story.model_dump(),
                    cdn=S3_LINK
                ) for story in stories[:limit]
            ]

            return StoriesResponse(
                isFound=True,
                next=next_page,
                page=page,
                stories=story_list
            )
        raise Exception("No stories found")
    except Exception as e:
        logging.error(e)
        return StoriesResponse(
            isFound=False,
            next=None,
            page=page,
            stories=[]
        )


@router.get("/landing", tags=["misc"])
@atomic()
async def get_landing():
    """
    Endpoint to get server metadata along with latest series.
    Good for landing pages. Chatfic Lab's /cfs-slug server pages use this endpoint.

    Returns:
        The server metadata as a dictionary and latest series as a
        list with key "series".
    """
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

@router.get("/tags", response_model=TagsResponse, tags=["tags"])
async def get_tags():
    """
    Retrieve all tags with their IDs and names.
    """
    try:
        tags = await models.Tag.all().values("idtag", "tag")
        tag_list = [{tag["idtag"]: tag["tag"]} for tag in tags]
        return TagsResponse(tags=tag_list)
    except Exception as e:
        logging.error(f"Error retrieving tags: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving tags")

@router.get("/series", response_model=SeriesResponse, tags=["stories & series"])
async def get_series(
        page: NonNegativeInt = Query(1, description="Page number,"
                                                    " default: 1"),
        storyGlobalId: Optional[str] = Query(
            None, description="Story Global ID for series lookup"
        ),
        sort_by: str = Query("new",
                             description="Sort by 'new' or 'name"),
        tags_required: List[str] = Query([],
                                         description="Required tags"),
        include_drafts: bool = Query(False, description="Include series with unpublished or no stories"),
        authorization: Optional[str] = Header(None, convert_underscores=False)
):
    per_page = 60
    page = min(page, 20)

    try:
        skip = (page - 1) * per_page
        limit = per_page
        series_query = None

        if include_drafts:
            validate_token(authorization)  # Validate token if include_drafts is true

        if storyGlobalId:
            stories = await models.Story.filter(
                storyGlobalId=storyGlobalId).limit(1)
            for story in stories:
                series_query = models.Series.filter(
                    idseries=story.series_id).all()

        else:
            series_query = models.Series.all()

        if tags_required:
            tags_required = tags_required[:3]
            series_query = series_query.filter(
                tags_rel__tag__tag__in=tags_required
            )

        if not include_drafts:
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
            next_page = page + 1 if len(series) == limit + 1 else None
            series_list = [
                SeriesBasicModel(**series_item.model_dump())
                for series_item in series[:limit]
            ]

            return SeriesResponse(
                isFound=True,
                offset=skip,
                next=next_page,
                page=page,
                series=series_list
            )

        raise Exception("No series found")

    except Exception as e:
        logging.error(e)
        return SeriesResponse(
            isFound=False,
            offset=0,
            next=None,
            page=page,
            series=[]
        )

@router.post("/series", response_model=SeriesBasicModel)
async def create_series(series: SeriesIn_Pydantic) -> SeriesBasicModel:
    random_story_key = getUniqueRandomStoryKey()
    series_global_id = f"{random_story_key[4:]}{random_story_key[:4]}"
    try:
        new_series = await models.Series.create(
            name=series.name,
            seriesGlobalId=series_global_id,
            creator=series.creator,
            episodes=0
        )

        new_series_pydantic = await models.SeriesWithRels_Pydantic.from_tortoise_orm(new_series)

        return SeriesBasicModel(**new_series_pydantic.model_dump())
    except Exception as e:
        logging.error(f"Error creating series: {e}")
        raise HTTPException(status_code=500, detail="Error creating series")

@router.put("/series/{series_id}/tags", response_model=SeriesTagsResponse)
async def add_tags_to_series(series_id: int, tags: List[str]):
    try:
        series = await models.Series.get(idseries=series_id).prefetch_related(
            "tags_rel__tag")

        # Fetch all tags from the database in a single query
        submitted_valid_tags = await models.Tag.filter(tag__in=tags).all()
        submitted_valid_tag_names = {str(tag.tag) for tag in submitted_valid_tags}

        if not submitted_valid_tag_names:
            raise HTTPException(status_code=400, detail="No valid tags provided")

        # Get the current tags associated with the series
        current_tags = {str(tag_rel.tag.tag) for tag_rel in series.tags_rel}

        # Determine tags to add and tags to delete
        tags_to_add = submitted_valid_tag_names - current_tags
        tags_to_delete = current_tags - submitted_valid_tag_names

        # Delete unused tags
        if tags_to_delete:
            await models.SeriesTagsRel.filter(
                series=series, tag__tag__in=tags_to_delete
            ).delete()

        # Add new tags
        if tags_to_add:
            tag_objects = [tag for tag in submitted_valid_tags if tag.tag in tags_to_add]
            await models.SeriesTagsRel.bulk_create([
                models.SeriesTagsRel(series=series, tag=tag) for tag in tag_objects
            ])

        return SeriesTagsResponse(series_id=series_id, tags=list(submitted_valid_tag_names))
    except Exception as e:
        logging.error("Error adding tags: %s", e)
        raise HTTPException(status_code=500, detail="Error adding tags")

@router.get("/latest", response_model=LatestSeriesResponse, tags=["stories & series"])
@atomic()
async def get_latest_series(
        offset: NonNegativeInt = Query(0,
                                       description="Offset, default: 0"),
        exclude_tags: List[PositiveInt] = Query(None, description="Tag ids to exclude, optional. You can retrieve them from '/'"),
        include_tags: List[PositiveInt] = Query(None, description="Tag ids to include, optional. You can retrieve them from '/'")) -> LatestSeriesResponse:
    """
    Endpoint to get latest series (no metadata).

    Args:
        offset: Offset, default: 0
        exclude_tags: Tag ids to exclude, optional
        include_tags: Tag ids to include, optional

    Returns:
        List of series

    """
    offset = min(max(offset, 0), 500)
    try:
        for attempt in range(3):  # Try up to 3 times
            try:
                if not exclude_tags and not include_tags:
                    queryset = models.Series.filter(
                        stories__release_date__lt=datetime.now()
                    ).order_by("-idseries").distinct().offset(offset).limit(10)
                else:
                    if exclude_tags:
                        if include_tags:
                            all_tags = list(set(exclude_tags + include_tags))

                            ex_text = ','.join(str(x) for x in exclude_tags)
                            # in_text = ','.join(str(x) for x in include_tags)
                            all_text = ','.join(str(x) for x in all_tags)

                            sql = f"""(SELECT series_id FROM ( SELECT sr.series_id, SUM(CASE WHEN sr.tag_id IN ({ex_text}) THEN 1 ELSE 0 END) AS x_clude, COUNT(*) AS all_count FROM ( SELECT sr.*, ( SELECT MIN(st.idstory) AS stories_aired FROM stories AS st WHERE st.series_id = sr.series_id AND st.release_date < NOW() LIMIT 1) AS stories_aired FROM series_tags_rel AS sr WHERE sr.tag_id IN ( {all_text} ) ORDER BY NULL) AS sr WHERE sr.stories_aired IS NOT NULL GROUP BY sr.series_id HAVING x_clude = 0 AND all_count = ( x_clude + {len(include_tags)} ) ORDER BY sr.id DESC LIMIT 10 OFFSET {offset}) AS ss)"""
                        else:
                            ex_text = ','.join(str(x) for x in exclude_tags)
                            sql = f"""(SELECT series_id FROM ( SELECT sr.series_id, SUM(CASE WHEN sr.tag_id IN ({ex_text}) THEN 1 ELSE 0 END) AS x_clude FROM ( SELECT sr.*, ( SELECT MIN(st.idstory) AS stories_aired FROM stories AS st WHERE st.series_id = sr.series_id AND st.release_date < NOW() LIMIT 1) AS stories_aired FROM series_tags_rel AS sr ORDER BY NULL) AS sr WHERE sr.stories_aired IS NOT NULL GROUP BY sr.series_id HAVING x_clude = 0 ORDER BY sr.id DESC LIMIT 10 OFFSET {offset}) AS ss)"""
                    else:
                        if len(include_tags) == 1:
                            sql = f"""(SELECT series_id FROM (SELECT sr.series_id FROM ( SELECT sr.*, ( SELECT MIN(st.idstory) AS stories_aired FROM stories AS st WHERE st.series_id = sr.series_id AND st.release_date < NOW() LIMIT 1) AS stories_aired FROM series_tags_rel AS sr WHERE sr.tag_id = {include_tags[0]} ORDER BY NULL) AS sr WHERE sr.stories_aired IS NOT NULL GROUP BY sr.series_id ORDER BY sr.id DESC LIMIT 10 OFFSET {offset}) AS ss)"""
                        else:
                            in_text = ','.join(str(x) for x in include_tags)
                            sql = f"""(SELECT series_id FROM ( SELECT sr.series_id, COUNT(*) AS total FROM ( SELECT sr.*, ( SELECT MIN(st.idstory) AS stories_aired FROM stories AS st WHERE st.series_id = sr.series_id AND st.release_date < NOW() LIMIT 1) AS stories_aired FROM series_tags_rel AS sr WHERE sr.tag_id IN ({in_text}) ORDER BY NULL) AS sr WHERE sr.stories_aired IS NOT NULL GROUP BY sr.series_id HAVING total = {len(include_tags)} ORDER BY sr.id DESC LIMIT 10 OFFSET {offset}) AS ss)"""

                    queryset = models.Series.filter(
                        idseries__in=RawSQL(sql)).order_by(
                        "-idseries").limit(10)

                series = await models.SeriesWithRels_Pydantic.from_queryset(
                    queryset
                )

                if series:
                    series_list = [
                        SeriesBasicModel(**series_item.dict())
                        for series_item in series
                    ]

                    return LatestSeriesResponse(
                        isFound=True,
                        offset=offset,
                        series=series_list
                    )

                raise Exception("No series found")

            except OperationalError as e:
                if "Packet sequence number wrong" in str(e) and attempt < 2:
                    # Log the retry attempt
                    logging.warning(
                        f"Retrying query due to sequence number error (attempt {attempt + 1})")
                    await asyncio.sleep(
                        0.5 * (attempt + 1))  # Exponential backoff
                    continue
                raise
    except Exception as e:
        logging.error(f"Error in get_latest_series: {str(e)}", exc_info=True)
        return LatestSeriesResponse(
            isFound=False,
            offset=offset,
            series=[]
        )

@router.get("/program", response_model=WeeklyProgramResponse,
            tags=["misc"])
async def get_current_week_program() -> WeeklyProgramResponse:
    """
    Get the current weekly program.

    Returns:
        WeeklyProgramResponse: The current weekly program.

    """
    # using FileResponse wouldn't help when we switch to a proper cache. So we'll load the json instead:
    cached_program = await get_cached_weekly_program()

    if not cached_program:
        return WeeklyProgramResponse(
            status="error",
            message="Program not available."
        )

    return WeeklyProgramResponse(
        status="success",
        data=cached_program
    )


async def get_cached_weekly_program():
    try:
        with open(CACHED_WEEKLY_PROGRAM_PATH, "r") as file:
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
                "release_date": rounded_release_date.strftime(
                    "%Y-%m-%dT%H:%M:00Z"),
                # "release_date": story.release_date,
                "storyGlobalId": story_global_id,
                "series_name": series_name,
                "seriesGlobalId": series_global_id
            })

        with open(CACHED_WEEKLY_PROGRAM_PATH, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, default=str)
            f.flush()
        return response_data

    except Exception as e:
        logging.error(e)
        return None
        # Handle exceptions and log errors


@router.get("/feed.xml", response_class=FileResponse, tags=["misc"])
async def get_recent_stories_feed():
    try:
        with open("feed.xml", "r") as file:
            pass
        logging.info("Received feed with cache")
        return "feed.xml"
    except FileNotFoundError:
        await build_rss_feed()
        logging.info("Received feed without cache")
        return "feed.xml"
    except Exception as e:
        logging.error(e)
        return None


async def build_rss_feed():
    # Get the 5 most recent published stories
    recent_stories = await models.Story.filter(
        release_date__lte=datetime.now(),
        exclude_from_rss=False
    ).order_by('-release_date').limit(5).prefetch_related('series',
                                                          'series__tags_rel',
                                                          'series__tags_rel__tag')

    server_name = settings.SERVER_METADATA.get("name", "")
    server_url = settings.SERVER_METADATA.get("url", "")
    server_slug = settings.SERVER_METADATA.get("slug", "")
    feed = feedgenerator.Rss201rev2Feed(
        title=f"{server_name} Chatfic Server RSS Feed",
        link=f"https://{server_url}/feed",
        description="Latest stories from our chatfic server.",
    )

    # Add each story to the feed
    for story in recent_stories:
        feed.add_item(
            title=story.title,
            link=f"https://chatficlab.com/cfs-{server_slug}/story-{story.storyGlobalId}",
            unique_id=f"{story.storyGlobalId}",
            author_name=story.author,
            categories=tuple(story.series.tagList()),
            author_link=f"https://patreon.com/{story.patreonusername}" if story.patreonusername else "https://chatficlab.com",
            description=story.description,
            pubdate=story.release_date,
        )

    rss_file_path = "./feed.xml"
    with open(rss_file_path, 'w', encoding='utf-8') as rss_file:
        feed.write(rss_file, 'utf-8')
        rss_file.flush()
        os.fsync(rss_file)

@router.on_event("startup")
@repeat_every(seconds=60)  # 1 minute
async def startup_event() -> None:
    now = datetime.now()
    if now.minute in [1, 31]:
        logging.info(
            "Rebuilding weekly program for minute: {}".format(now.minute))
        await build_weekly_program()
    elif now.minute in [4, 34]:
        logging.info("Rebuilding rss feed for minute: {}".format(now.minute))
        await build_rss_feed()
