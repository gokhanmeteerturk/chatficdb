import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from database.models import SubmissionStatus

class MetadataTheme(BaseModel):
    primary: str

class TagsResponse(BaseModel):
    tags: List[Dict[int, str]]

class ServerMetadataResponse(BaseModel):
    theme: MetadataTheme
    tags: Dict[int, str]

    # Include other metadata fields from settings.SERVER_METADATA
    class Config:
        extra = "allow"  # Allows additional fields from SERVER_METADATA


class ItemExistsResponse(BaseModel):
    exists: bool

class SeriesTagsResponse(BaseModel):
    series_id: int
    tags: List[str]

class SeriesLookupResponse(BaseModel):
    isFound: bool
    message: Optional[str] = None
    data: Dict[str, str]


class StoryResponse(BaseModel):
    isFound: bool
    title: str = ""
    description: Optional[str] = None
    author: str = ""
    patreonusername: Optional[str] = ""
    cdn: str = ""

class StoryReleaseResponse(BaseModel):
    idstory: int
    storyGlobalId: Optional[str] = None
    release_date: datetime.datetime
    exclude_from_rss: bool



class StoryBasicModel(BaseModel):
    title: str
    description: Optional[str]
    author: Optional[str]
    patreonusername: Optional[str]
    storyGlobalId: Optional[str]
    cdn: str


class StoriesResponse(BaseModel):
    isFound: bool
    next: Optional[int]
    page: int
    stories: List[StoryBasicModel]


class SeriesBasicModel(BaseModel):
    idseries: int
    name: str
    seriesGlobalId: str
    creator: str
    episodes: int
    numStories: int
    tagList: List[str]


class SeriesResponse(BaseModel):
    isFound: bool
    offset: int
    next: Optional[int]
    page: int
    series: List[SeriesBasicModel]


class LatestSeriesResponse(BaseModel):
    isFound: bool
    offset: int
    series: List[SeriesBasicModel]


class WeeklyProgramStory(BaseModel):
    idstory: int
    title: str
    description: str
    release_date: str
    storyGlobalId: Optional[str]
    series_name: Optional[str]
    seriesGlobalId: Optional[str]


class WeeklyProgramResponse(BaseModel):
    status: str
    data: Optional[Dict[str, Any]]
    message: Optional[str] = None


class StorySubmissionResponse(BaseModel):
    idstorysubmission: int
    title: Optional[str]
    description: Optional[str]
    author: Optional[str]
    storyGlobalId: Optional[str]
    series: SeriesBasicModel
    submission_date: datetime.datetime
    files_list: Optional[List[Dict[str, Any]]]  # JSON field for files
    upload_links: Optional[List[Dict[str, Any]]]  # JSON field for upload links
    status: SubmissionStatus  # Enum field for status
    logs: Optional[str]
    story_id: Optional[int] = None
    story: Optional[StoryReleaseResponse] = None


class SubmissionListResponse(BaseModel):
    submissions: List[StorySubmissionResponse]
    total: int
    page: int
    next_page: Optional[int]

class SubmissionToStoryRequest(BaseModel):
    release_date: Optional[str] = None
    exclude_from_rss: bool = False

class SubmissionToStoryResponse(BaseModel):
    success: bool
    message: str
    story_id: Optional[int] = None
    storyGlobalId: Optional[str] = None

