# noinspection PyPackageRequirements
from tortoise import Model, fields
# noinspection PyPackageRequirements
from tortoise.contrib.pydantic import pydantic_model_creator


class Series(Model):
    idseries = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    seriesGlobalId = fields.CharField(max_length=20)
    creator = fields.CharField(max_length=45)
    episodes = fields.IntField(default=1)

    class Meta:
        table = "series"


Series_Pydantic = pydantic_model_creator(Series,
                                         name="Series")
SeriesIn_Pydantic = pydantic_model_creator(Series,
                                           name="SeriesIn",
                                           exclude_readonly=True)


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


Tag_Pydantic = pydantic_model_creator(Tag, name="Tag")
TagIn_Pydantic = pydantic_model_creator(Tag, name="TagIn",
                                        exclude_readonly=True)
