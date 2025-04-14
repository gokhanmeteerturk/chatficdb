import json

from huey import SqliteHuey

from database.models import StorySubmission, SubmissionStatus
import helpers.chatfic_tools as chatfic_tools
from helpers.utils import run_async_task, getUniqueRandomStoryKey, \
    create_s3_client

from settings import S3_BUCKET
huey = SqliteHuey(filename="queue_db/huey_tasks.db")


@huey.task()
def run_submission_preprocess(submission_id: int):
    """
    Runs _run_submission_preprocess_async, which does a few things:
    "Runs story_text validation for a submission, and generates S3 upload links if valid.
    Updates the submission status to one of these:
        VALIDATION_FAILED = 25
        WAITING_USER_UPLOAD = 30"
    """

    run_async_task(_run_submission_preprocess_async(submission_id))

@huey.task()
def run_submission_postprocess(submission_id: int):
    run_async_task(_run_submission_postprocess_async(submission_id))

async def _run_submission_preprocess_async(submission_id: int):
    submission = await get_submission_or_raise(submission_id)

    multimedia_list = extract_multimedia_list(submission.files_list)
    validation_result = chatfic_tools.validate_storybasic_json(submission.story_text, multimedia_list)

    if not validation_result.is_valid:
        await mark_validation_failed(submission, validation_result)
        return

    story_global_id = getUniqueRandomStoryKey()
    submission.storyGlobalId = story_global_id

    used_multimedia = filter_used_multimedia(multimedia_list, validation_result.warnings)
    valid_files = filter_valid_files(submission.files_list, used_multimedia)

    if not valid_files:
        await mark_no_valid_files(submission)
        return

    s3_client = create_s3_client()
    presigned_urls = generate_presigned_urls(s3_client, story_global_id, valid_files)

    upload_storybasic_json(s3_client, story_global_id, submission.story_text)

    await update_submission_with_upload_links(submission, presigned_urls)

async def _run_submission_postprocess_async(submission_id: int):
    submission = await get_submission_or_raise(submission_id)

    if submission.status != SubmissionStatus.WAITING_POST_PROCESSING:
        raise ValueError("Submission is not in WAITING_POST_PROCESSING status.")

    # 1/3: CREATE STORY.JSON CONTENT:
    compiled_story = chatfic_tools.create_chatfic(
        submission.story_text,
        submission.storyGlobalId
    )
    # 2/3: RUN SENTIMENT ANALYSIS:
    compiled_story = chatfic_tools.analyze_sentiment(compiled_story)

    # 3/3: UPLOAD STORY.JSON:
    s3_client = create_s3_client()
    if s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=f"story/{submission.storyGlobalId}/story.json",
        Body=json.dumps(compiled_story, indent=4, ensure_ascii=False),
        ContentType='application/json',
    ):
        submission.status = SubmissionStatus.PROCESSED
    else:
        submission.status = SubmissionStatus.POST_PROCESSING_FAILED
        submission.logs = (str(submission.logs) or "") + "- Story.json couldn't upload:\n" + json.dumps(compiled_story, indent=4, ensure_ascii=False) + "\n"
    await submission.save()


async def get_submission_or_raise(submission_id: int):
    submission = await StorySubmission.get_or_none(idstorysubmission=submission_id)
    if not submission:
        raise ValueError(f"Submission with ID {submission_id} not found.")
    return submission


def extract_multimedia_list(files_list):
    return [file.name[6:] for file in files_list if file.name.startswith("media/")]


async def mark_validation_failed(submission, validation_result):
    submission.logs = (str(submission.logs) or "") + "- Validation failed with errors:\n" + "\n - -".join([e.message for e in validation_result.errors]) + "\n"
    submission.status = SubmissionStatus.VALIDATION_FAILED
    await submission.save()


def filter_used_multimedia(multimedia_list, warnings):
    for warning in warnings or []:
        if warning.startswith("Multimedia not used: "):
            unused = warning.split(": ")[1]
            if unused in multimedia_list:
                multimedia_list.remove(unused)
    return multimedia_list


def filter_valid_files(files_list, multimedia_list):
    return [
        file for file in files_list
        if (file.name.startswith("media/") and file.name[6:] in multimedia_list) or
           file.name == "storybasic.md"
    ]

async def mark_no_valid_files(submission):
    submission.logs = (str(submission.logs) or "") + "- No valid files found for upload.\n"
    submission.status = SubmissionStatus.VALIDATION_FAILED
    await submission.save()

def generate_presigned_urls(s3_client, story_id, files):
    urls = []
    for file in files:
        key = f"story/{story_id}/{file['name']}"
        presigned_post = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET,
            Key=key,
            Conditions=[["content-length-range", max(0, file["size"] - 100), file["size"]]],
            ExpiresIn=3600
        )
        urls.append({"name": file["name"], "url": presigned_post})
    return urls


def upload_storybasic_json(s3_client, story_id, story_text):
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=f"story/{story_id}/storybasic.json",
        Body=story_text,
        ContentType='application/json',
    )


async def update_submission_with_upload_links(submission, urls):
    submission.upload_links = urls
    submission.status = SubmissionStatus.WAITING_USER_UPLOAD
    await submission.save()
