from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse
from snippets import posts
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

#routes
#template  response
@app.get("/")
@app.get("/home")
def home(request: Request):
    return templates.TemplateResponse(
            request,
            "home.html",
            {"posts": posts, "title": "Home"},
        )
    
#html response
@app.get("/posts", response_class=HTMLResponse,include_in_schema=False)# will exclude from api doc
def home():
    return f'<h1>{posts[0]['title']}</h1>'

@app.get("/api/posts/")
def get_posts():
    return posts


