from fastapi import APIRouter, HTTPException
from endpoints.response_models import StorySubmissionResponse
from database.models import StorySubmission, Story_SubmissionIn_Pydantic, \
    Story_Submission_Pydantic, SubmissionStatus
from helpers.tasks import run_submission_preprocess
from helpers.utils import create_s3_client
from settings import S3_BUCKET
from botocore.exceptions import ClientError
router = APIRouter()

@router.post("/story_submissions", response_model=StorySubmissionResponse)
async def create_story_submission(
        story_submission: Story_SubmissionIn_Pydantic):
    try:
        if "storybasic.json" not in [file.get("name","") for file in story_submission.files_list]:
            raise HTTPException(status_code=400,
                                detail="storybasic.json file is required.")
        for file in story_submission.files_list:
            if 'name' not in file or 'size' not in file:
                raise HTTPException(status_code=400,
                                    detail="Each file must contain 'name' and 'size' keys.")

        # Create a new story submission in the database
        new_submission = await StorySubmission.create(
            **story_submission.dict())

        # Serialize the created submission
        submission_data = await Story_Submission_Pydantic.from_tortoise_orm(
            new_submission)

        # Add the submission preprocessing task to the Huey queue
        run_submission_preprocess(new_submission.idstorysubmission)

        # Return the serialized submission data
        return StorySubmissionResponse(
            **submission_data.model_dump()
        )
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error creating story submission: {str(e)}")

@router.get("/story_submissions/{submission_id}", response_model=StorySubmissionResponse)
async def get_story_submission(submission_id: int):
    try:
        # Fetch the story submission from the database
        submission = await StorySubmission.get_or_none(idstorysubmission=submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found.")

        # Serialize the submission data
        submission_data = await Story_Submission_Pydantic.from_tortoise_orm(submission)

        # Return the serialized submission data
        return StorySubmissionResponse(**submission_data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving story submission: {str(e)}")

@router.post("/story_submissions/{submission_id}/register_upload")
async def register_upload(submission_id: int):
    try:
        # Fetch the story submission from the database
        submission = await StorySubmission.get_or_none(
            idstorysubmission=submission_id
        )
        if not submission:
            raise HTTPException(status_code=404,
                                detail="Submission not found.")

        # Check if the submission status is WAITING_USER_UPLOAD
        if submission.status != SubmissionStatus.WAITING_USER_UPLOAD:
            raise HTTPException(status_code=400,
                                detail="Submission is not in WAITING_USER_UPLOAD status.")

        # Check if upload_links exist
        if not submission.upload_links:
            raise HTTPException(status_code=400,
                                detail="No upload links found for this submission.")

        # Verify uploaded files in S3
        s3_client = create_s3_client()
        all_files_uploaded = True
        submission_logs = (str(submission.logs) or "")
        for file in submission.upload_links:
            key = f"story/{submission.storyGlobalId}/{file['name']}"
            try:
                s3_client.head_object(Bucket=S3_BUCKET, Key=key)
            except (ClientError, s3_client.exceptions.NoSuchKey) as e:
                submission_logs = submission_logs + f"- File {file['name']} not found in S3.\n"
                await submission.save()
                all_files_uploaded = False
                break

        # Update submission status based on file upload verification
        if all_files_uploaded:
            submission.status = SubmissionStatus.WAITING_POST_PROCESSING
            submission_logs = submission_logs + "- All files uploaded successfully.\n"
            submission.logs = submission_logs
            await submission.save()
            # Trigger the post processing task
            run_submission_post_process(submission.idstorysubmission)
        else:
            submission.status = SubmissionStatus.USER_UPLOAD_FAILED
            submission_logs = submission_logs + "- Some files are missing in S3.\n"
            submission.logs = submission_logs
            await submission.save()

        return {"status": submission.status}
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error registering upload: {str(e)}")
