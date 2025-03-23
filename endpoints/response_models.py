from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class MetadataTheme(BaseModel):
    primary: str


class ServerMetadataResponse(BaseModel):
    theme: MetadataTheme
    tags: Dict[int, str]

    # Include other metadata fields from settings.SERVER_METADATA
    class Config:
        extra = "allow"  # Allows additional fields from SERVER_METADATA


class ItemExistsResponse(BaseModel):
    exists: bool


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
