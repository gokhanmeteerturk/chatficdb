from __future__ import annotations

import pytz
from tortoise import Model, fields, Tortoise
# noinspection PyPackageRequirements
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import NoValuesFetched
from datetime import datetime
from enum import IntEnum


class SubmissionStatus(IntEnum):
    """
    Enumeration for the different statuses a submission can have.

    Attributes:
        15 NOT_ACCEPTED (int): The submission is not accepted.
        20 WAITING_VALIDATION (int): The submission is waiting for validation.
        25 VALIDATION_FAILED (int): The submission validation has failed.
        26 REPEATED (int): The submission is a repeated submission.
        30 WAITING_USER_UPLOAD (int): The submission is waiting for user upload.
        35 USER_UPLOAD_FAILED (int): The user upload has failed.
        40 WAITING_POST_PROCESSING (int): The submission is waiting for post-processing.
        45 POST_PROCESSING_FAILED (int): The post-processing has failed.
        60 PROCESSED (int): The submission has been processed.

        # if status code ends with 0, it is a success.
    """
    NOT_ACCEPTED = 15
    WAITING_VALIDATION = 20
    VALIDATION_FAILED = 25
    REPEATED = 26
    WAITING_USER_UPLOAD = 30
    USER_UPLOAD_FAILED = 35
    WAITING_POST_PROCESSING = 40
    POST_PROCESSING_FAILED = 45
    PROCESSED = 60


class Series(Model):
    """
    Represents a series in the database.

    Attributes:
        idseries (int): The primary key of the series.
        name (str): The name of the series.
        seriesGlobalId (str): The unique ID of the series.
        creator (str): The creator of the series.
        episodes (int): The number of episodes in the series.
        stories (ReverseRelation): The stories associated with the series.
        tags_rel (ReverseRelation): The tags associated with the series, Many to many.
    """
    idseries = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    seriesGlobalId = fields.CharField(max_length=20)
    creator = fields.CharField(max_length=45)
    episodes = fields.IntField(default=1)
    stories = fields.ReverseRelation["Story"]
    tags_rel = fields.ReverseRelation["SeriesTagsRel"]

    def numStories(self) -> int:
        """
        Compute the number of stories associated with this series.

        Returns:
            int: The number of stories that have been released (i.e.,
                their release date is in the past).
                Returns -1 if the stories have not been fetched.
        """
        # Compute the number of stories associated with this series
        try:
            # Terrible performance, but maybe tortoise's pydantic integration
            # can let us cache this property in the future.
            # TODO: make this a calculated field and trigger its update when
            # stories are published.
            if type(self.stories) == list and len(self.stories) > 0:
                return sum(
                    story.release_date <= datetime.now(pytz.utc) for story in
                    self.stories)
            return len(self.stories)
        except NoValuesFetched:
            return -1

    def tagList(self) -> list[str]:
        """
        Compute a list of tags associated with this series.

        This method iterates over the `tags_rel` reverse relation to extract
        the tag names. This is necessary because the tags are stored in a
        many-to-many relationship with the series, and this method provides
        a convenient way to access the tag names directly from the series
        instance.

        Returns:
        list[str]: A list of tag names associated with this series.
        """
        # Compute a list of tags associated with this series
        tags = [str(tag_rel.tag.tag) for tag_rel in
                self.tags_rel]
        return tags

    class Meta:
        table = "series"

    class PydanticMeta:
        computed = ["numStories", "tagList"]


class SeriesTagsRel(Model):
    """
    Represents the relationship between a series and its tags.
    """
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


class StorySubmission(Model):
    """
    Represents a story submission in the database.
    """

    idstorysubmission = fields.IntField(pk=True)
    title = fields.CharField(max_length=45, null=True)
    description = fields.CharField(max_length=45, null=True)
    story_text = fields.TextField(null=True)
    author = fields.CharField(max_length=45, null=True)
    storyGlobalId = fields.CharField(max_length=45, null=True)
    series = fields.ForeignKeyField('models.Series',
                                    related_name='submissions')
    submission_date = fields.DatetimeField(auto_now_add=True,
                                           default=datetime.now)
    files_list = fields.JSONField(null=True)
    # Proper files list will be something like below. originalName is useless:
    # files=[
    #  {'name': 'storybasic.json', 'originalName': 'x7z/storybasic.json', 'size': 26939},
    #  {'name': 'storybasic.md', 'originalName': 'aeg5/storybasic.md', 'size': 8665},
    #  {'name': 'media/7.jpg', 'originalName': 'dv8/media/7.jpg', 'size': 734905},
    #  {'name': 'media/19.jpg', 'originalName': 'eg1/media/19.jpg', 'size': 131964},
    #  ]
    upload_links = fields.JSONField(null=True)
    status = fields.IntEnumField(SubmissionStatus,
                                 default=SubmissionStatus.WAITING_VALIDATION,
                                 null=False)
    logs = fields.TextField(null=True)

    class Meta:
        table = "story_submissions"


Story_Submission_Pydantic = pydantic_model_creator(StorySubmission,
                                                   name="StorySubmission")
Story_SubmissionIn_Pydantic = pydantic_model_creator(StorySubmission,
                                                     exclude=('idstorysubmission',
                                                              'submission_date',
                                                              'status',
                                                              'logs',
                                                              'upload_links'),
                                                   name="StorySubmissionIn",
                                                     exclude_readonly=True)


class Story(Model):
    """
    Represents a story in the database.
    """
    idstory = fields.IntField(pk=True)
    title = fields.CharField(max_length=45, null=True)
    description = fields.CharField(max_length=45, null=True)
    author = fields.CharField(max_length=45, null=True)
    patreonusername = fields.CharField(max_length=45, null=True)
    storyGlobalId = fields.CharField(max_length=45, null=True)
    series = fields.ForeignKeyField('models.Series', related_name='stories')
    release_date = fields.DatetimeField(auto_now_add=True,
                                        default=datetime.now)
    exclude_from_rss = fields.BooleanField(default=False, null=False)

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
                                           exclude=('seriesGlobalId','episodes'),
                                           exclude_readonly=True)

Tag_Pydantic = pydantic_model_creator(Tag, name="Tag")
TagIn_Pydantic = pydantic_model_creator(Tag, name="TagIn",
                                        exclude_readonly=True)

Tortoise.init_models(["database.models"], "models")

SeriesWithRels_Pydantic = pydantic_model_creator(Series, name="SeriesWithRels")
