# main.py

import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from tortoise.contrib.fastapi import register_tortoise

from endpoints import stories

import settings

app = FastAPI()


logging.basicConfig(level=logging.INFO)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.include_router(products.router)
# app.include_router(orders.router)

load_dotenv()

app = FastAPI()
app.include_router(stories.router)

# s3_link = "https://chatficdottop.s3.us-east-2.amazonaws.com"
S3_LINK = "https://topaltdb.s3.us-east-2.amazonaws.com"


# Connect to the database
# def get_db():
#     return mysql.connector.connect(**DATABASE_SETTINGS)


# def get_story_from_db(storyGlobalId):
#
#     db_connection = get_db()
#     cursor = db_connection.cursor(dictionary=True)
#
#     select_query = "SELECT * FROM stories WHERE storyGlobalId=%s LIMIT 1"
#     values = (storyGlobalId,)
#
#     try:
#         cursor.execute(select_query, values)
#         items = cursor.fetchall()
#     except Exception as e:
#         logging.error(e)
#         raise HTTPException(status_code=500, detail="Error connecting DB")
#     finally:
#         cursor.close()
#         db_connection.close()
#
#     if items is not None and len(items) > 0:
#         item = items[0]
#         return {
#             "isFound": True,
#             "title": item["title"],
#             "description": item["description"],
#             "author": item["author"],
#             "patreonusername": item["patreonusername"],
#             "cdn": S3_LINK
#         }
#     else:
#         raise HTTPException(status_code=404, detail="Story not found")


# def get_latest_stories_from_db():
#     db_connection = get_db()
#     cursor = db_connection.cursor(dictionary=True)
#
#     select_query = "SELECT * FROM stories ORDER BY idstory DESC LIMIT 50"
#
#     try:
#         cursor.execute(select_query)
#         items = cursor.fetchall()
#     except Exception as e:
#         logging.error(e)
#         raise HTTPException(status_code=500, detail="Error connecting DB")
#     finally:
#         cursor.close()
#         db_connection.close()
#
#     stories_list = []
#     for item in items:
#         stories_list.append({
#             "title": item["title"],
#             "description": item["description"],
#             "author": item["author"],
#             "patreonusername": item["patreonusername"],
#             "cdn": S3_LINK
#         })
#
#     return stories_list


# @app.get("/stories")
# async def get_stories():
#     try:
#         stories = await models.Story_Pydantic.from_queryset(models.Story.all())
#         # return {"isFound": True, "stories": get_latest_stories_from_db()}
#         return {"isFound": True, "stories": stories}
#     except Exception as e:
#         logging.error(e)
#         return {"isFound": False, "stories": []}


# @app.get("/story")
# async def get_story(storyGlobalId: str):
#     try:
#         story = models.Story.filter(storyGlobalId=storyGlobalId).limit(1)
#         result = await models.Story_Pydantic.from_queryset(story)
#         if result:
#             row = result[0]
#             return {"isFound": True, "title": row.title, "description": row.description, "author": row.author,
#                 "patreonusername": row.patreonusername, "cdn": S3_LINK}
#         raise Exception("Not found")
#         # return get_story_from_db(storyGlobalId)
#     except Exception as e:
#         logging.error(e)
#         return {"isFound": False, "title": "", "description": "", "author": "",
#                 "patreonusername": "", "cdn": ""}


@app.get("/submit", response_class=HTMLResponse)
async def show_submit_page():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Submit Page</title>
        <style>
            body {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background-color: #2d2d2d;
            }
            #centered-div {
                text-align: left;
                padding: 20px;
                border: 1px solid #000;
                border-radius: 5px;
                color:white !important;
                background-color: #111;
            }
            .btn {
                display: inline-block;
                padding: 10px 20px;
                font-size: 18px;
                font-weight: 500;
                text-align: center;
                text-decoration: none;
                border-radius: 4px;
                background-color: #2196F3;
                color: #fff;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }

            .btn:hover {
                background-color: #1976D2;
            }

        </style>
    </head>
    <body>
        <div id="centered-div">
            <h1>How to create</h1>
            <p>Chatfics generally get created using the chatfic-format. It is possible to create one without any tools. But using an editor is much easier.<br><br>You can use editor.chatficlab.com to create your own chatfic. No prior experience required.</p>
            <hr>
            <h1>Submit Your Chatfic Story</h1>
            <p>You can submit your chatfic as a .zip archive as suggested by the chatfic-format (Our online editor creates this automatically).<br><br>Once ready, upload your file to any popular file sharing platform(Wetransfer, Google Drive, Dropbox etc) and send us the link using below button.</p>
            <div style="text-align:center;"><a class="btn" href="https://forms.gle/scmCtU15PPNocE739" target="_blank">Submit your chatfic</a></div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

register_tortoise(
    app,
    config=settings.TORTOISE_CONFIG,
    modules={"models": ["database.models"]},
    generate_schemas=True,
    add_exception_handlers=False,
)
