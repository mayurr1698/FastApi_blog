from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from snippets import posts

app = FastAPI()

#routes

@app.get("/", response_class=HTMLResponse)
@app.get("/posts", response_class=HTMLResponse,include_in_schema=False)# will exclude from api doc
def home():
    return f'<h1>{posts[0]['title']}</h1>'

@app.get("/api/posts/")
def get_posts():
    return posts


