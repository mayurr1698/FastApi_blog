from fastapi import FastAPI,Request,HTTPException,status
from fastapi.responses import HTMLResponse
from snippets import posts
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

#routes
#template  response
#web routers
@app.get("/")
@app.get("/home")
def home(request: Request):
    return templates.TemplateResponse(
            request,
            "home.html",
            {"posts": posts, "title": "Home"},
        )
    
@app.get("/posts/{post_id}",include_in_schema=False)
def get_post_page(request: Request, post_id: int):
    for post in posts:
         if(post.get("id") == post_id):
             return templates.TemplateResponse(
                 request,
                 "post.html",
                 {"post": post, "title":"Home"}
             )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

#html response
@app.get("/posts", response_class=HTMLResponse,include_in_schema=False)# will exclude from api doc
def home():
    return f'<h1>{posts[0]['title']}</h1>'


#API routes
@app.get("/api/posts/")
def get_posts():
    return posts


@app.get("/api/posts/{post_id}")
def get_posts(post_id: int):
    for post in posts:
         if(post.get("id") == post_id):
             return post
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )
    
@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )