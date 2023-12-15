from __future__ import annotations

from typing import List

from tortoise import Model, fields, Tortoise
# noinspection PyPackageRequirements
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import NoValuesFetched
from datetime import datetime

class Series(Model):
    idseries = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    seriesGlobalId = fields.CharField(max_length=20)
    creator = fields.CharField(max_length=45)
    episodes = fields.IntField(default=1)
    stories = fields.ReverseRelation["Story"]
    tags_rel = fields.ReverseRelation["SeriesTagsRel"]

    def numStories(self) -> int:
        # Compute the number of stories associated with this series
        try:
            return len(self.stories)
        except NoValuesFetched:
            return -1

    def tagList(self) -> list[str]:
        # Compute a list of tags associated with this series
        tags = [str(tag_rel.tag.tag) for tag_rel in
                         self.tags_rel]
        return tags

    class Meta:
        table = "series"

    class PydanticMeta:
        computed = ["numStories", "tagList"]


class SeriesTagsRel(Model):
    id = fields.IntField(pk=True)
    series = fields.ForeignKeyField('models.Series', related_name='tags_rel')
    tag = fields.ForeignKeyField('models.Tag', related_name='series_rel')

    class Meta:
        table = "series_tags_rel"


SeriesTagsRel_Pydantic = pydantic_model_creator(SeriesTagsRel,
                                                name="SeriesTagsRel")
SeriesTagsRelIn_Pydantic = pydantic_model_creator(SeriesTagsRel,
                                                  name="SeriesTagsRelIn",
                                                  exclude_readonly=True)


class Story(Model):
    idstory = fields.IntField(pk=True)
    title = fields.CharField(max_length=45, null=True)
    description = fields.CharField(max_length=45, null=True)
    author = fields.CharField(max_length=45, null=True)
    patreonusername = fields.CharField(max_length=45, null=True)
    storyGlobalId = fields.CharField(max_length=45, null=True)
    series = fields.ForeignKeyField('models.Series', related_name='stories')
    release_date = fields.DatetimeField(auto_now_add=True, default=datetime.now)

    # this won't be hashed since it is not really a value with
    # critical security. this will usually be shared with patreon supporters
    # of the author and leak all the time. keeping it as raw string will help
    # author to always come back and see their story pass
    # and modify it with ease of mind.
    # early_access_pass = fields.CharField(max_length=20, null=True)

    class Meta:
        table = "stories"


Story_Pydantic = pydantic_model_creator(Story, name="Story")
StoryIn_Pydantic = pydantic_model_creator(Story, name="StoryIn",
                                          exclude_readonly=True)


class Tag(Model):
    idtag = fields.IntField(pk=True)
    tag = fields.CharField(max_length=45)

    class Meta:
        table = "tags"


Series_Pydantic = pydantic_model_creator(Series,
                                         name="Series")
SeriesIn_Pydantic = pydantic_model_creator(Series,
                                           name="SeriesIn",
                                           exclude_readonly=True)

Tag_Pydantic = pydantic_model_creator(Tag, name="Tag")
TagIn_Pydantic = pydantic_model_creator(Tag, name="TagIn",
                                        exclude_readonly=True)

Tortoise.init_models(["database.models"], "models")

SeriesWithRels_Pydantic = pydantic_model_creator(Series, name="SeriesWithRels")
