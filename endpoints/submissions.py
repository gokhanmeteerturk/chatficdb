from fastapi import APIRouter, HTTPException, Query, Path, Depends
from endpoints.response_models import StorySubmissionResponse, SubmissionListResponse, SubmissionToStoryRequest, SubmissionToStoryResponse
from database.models import StorySubmission, Story_SubmissionIn_Pydantic, \
    Story_Submission_Pydantic, SubmissionStatus, Story
from helpers.auth import validate_token
from helpers.tasks import run_submission_preprocess, run_submission_postprocess
from helpers.utils import create_s3_client
from settings import S3_BUCKET
from botocore.exceptions import ClientError
from typing import Optional, List
from datetime import datetime
router = APIRouter()

@router.post("/story_submissions", response_model=StorySubmissionResponse, dependencies=[Depends(validate_token)])
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

@router.get("/story_submissions/{submission_id}", response_model=StorySubmissionResponse, dependencies=[Depends(validate_token)])
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

@router.post("/story_submissions/{submission_id}/register_upload", dependencies=[Depends(validate_token)])
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
            run_submission_postprocess(submission.idstorysubmission)
        else:
            submission.status = SubmissionStatus.USER_UPLOAD_FAILED
            submission_logs = submission_logs + "- Some files are missing in S3.\n"
            submission.logs = submission_logs
            await submission.save()

        return {"status": submission.status}
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error registering upload: {str(e)}")

@router.get("/story_submissions", response_model=SubmissionListResponse, dependencies=[Depends(validate_token)])
async def list_submissions(
    page: int = Query(1, description="Page number, starting from 1"),
    filter_type: str = Query("with_story", description="Filter type: all, with_story, without_story"),
    status: Optional[int] = Query(None, description="Filter by submission status")
):
    try:
        per_page = 10
        skip = (page - 1) * per_page

        # Base query
        query = StorySubmission.all().order_by("-submission_date")

        # Apply filters
        if filter_type == "without_story":
            query = query.filter(story_id__isnull=True)
        elif filter_type == "with_story":
            query = query.filter(story_id__isnull=False)

        if status is not None:
            query = query.filter(status=status)

        # Count total items for pagination
        total = await query.count()

        # Get data for current page
        submissions = await query.offset(skip).limit(per_page + 1)

        # Calculate if there's a next page
        has_next = len(submissions) > per_page
        if has_next:
            submissions = submissions[:per_page]
            next_page = page + 1
        else:
            next_page = None

        # Convert to pydantic models
        submission_data = [
            await Story_Submission_Pydantic.from_tortoise_orm(submission)
            for submission in submissions
        ]
        print(submission_data)
        print("----")
        print(submission_data[0])

        # Create response objects
        submission_responses = [
            StorySubmissionResponse(story_id=data.story.idstory if hasattr(data, 'story') and hasattr(data.story, 'idstory') else None, **data.model_dump())
            for data in submission_data
        ]

        return SubmissionListResponse(
            submissions=submission_responses,
            total=total,
            page=page,
            next_page=next_page
        )
    except Exception as e:
        raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching submissions: {str(e)}"
        )

@router.post("/story_submissions/{submission_id}/convert", response_model=SubmissionToStoryResponse, dependencies=[Depends(validate_token)])
async def convert_submission_to_story(
    submission_id: int = Path(..., description="ID of submission to convert"),
    conversion_data: SubmissionToStoryRequest = None
):
    try:
        # Get the submission
        submission = await StorySubmission.get_or_none(idstorysubmission=submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        # Check if submission is already linked to a story
        if submission.story_id is not None:
            return SubmissionToStoryResponse(
                success=False,
                message="Submission is already linked to a story",
                story_id=submission.story_id
            )

        # Check if submission status is appropriate
        if submission.status != SubmissionStatus.PROCESSED:
            return SubmissionToStoryResponse(
                success=False,
                message=f"Submission status {submission.status} is not appropriate for story creation"
            )

        # Set release date (default to now if not provided)
        release_date = datetime.now()
        if conversion_data and conversion_data.release_date:
            try:
                release_date = datetime.fromisoformat(conversion_data.release_date.replace("Z", "+00:00"))
            except ValueError:
                # release_date = datetime.now()
                raise HTTPException(status_code=400, detail="Invalid release_date format. Use ISO 8601 format.")

        # Set exclude_from_rss
        exclude_from_rss = False
        if conversion_data:
            exclude_from_rss = conversion_data.exclude_from_rss

        # Create the story
        new_story = await Story.create(
            title=submission.title,
            description=submission.description,
            author=submission.author,
            patreonusername=None,
            storyGlobalId=submission.storyGlobalId,
            series_id=submission.series_id,
            release_date=release_date,
            exclude_from_rss=exclude_from_rss
        )

        # Update the submission to link to the story
        submission.story = new_story
        await submission.save()

        return SubmissionToStoryResponse(
            success=True,
            message="Successfully converted submission to story",
            story_id=new_story.idstory,
            storyGlobalId=new_story.storyGlobalId
        )
    except HTTPException:
        raise
    except Exception as e:
        raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error converting submission to story: {str(e)}"
        )

