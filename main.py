'''
This includes SQLLite DB + SQLAlchemy +pydantic schmea
pydantic -> define api contract
sqlALchemy ->
pydantic validates data -> sqlalchemy store or retrive data -> pydantic will format response
'''
from __future__ import annotations
from fastapi import Depends,FastAPI,Request,HTTPException,status
from fastapi.responses import HTMLResponse
from snippets import posts
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import PostCreate, PostResponse, UserCreate, UserResponse, PostUpdate, UserUpdate
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import Base,engine,get_db

#creates tables if don't exists
#it's idempotence
Base.metadata.create_all(bind=engine)

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media",StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")

#routes
#template  response
#web routers
@app.get("/")
@app.get("/home")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(
            request,
            "home.html",
            {"posts": posts, "title": "Home"},
        )

@app.get("/posts/{post_id}",include_in_schema=False)
def get_post_page(request: Request, post_id: int,db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    for post in posts:
         if(post.id == post_id):
             return templates.TemplateResponse(
                 request,
                 "post.html",
                 {"post": post, "title":"Home"}
             )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@app.get(
    '/users/{user_id}/posts',
    include_in_schema=False,
    name='user_posts'
)
def user_posts_page(request:Request,user_id:int, db: Annotated[Session, Depends(get_db)]):
    posts = get_user_posts(user_id, db)
    user = posts[0].author
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )


#API routes
@app.get("/api/posts/",response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    posts = db.execute(select(models.Post)).scalars().all()
    if not posts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No posts found')
    return posts

@app.get("/api/posts/{post_id}",response_model=PostResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    post = db.execute(select(models.Post)).scalars().first()
    if(post.id == post_id):
        return post
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@app.put('/api/posts/{post_id}',response_model=PostResponse)
def update_post(
    post_id:int,
    post_data: PostCreate,
    db: Annotated[Session, Depends(get_db)]
):
    post = get_post(post_id, db)
    user = get_user(post_data.user_id,db)
    if user and post:
        post.tlte = post_data.title
        post.content = post_data.content
        post.user_id = post_data.user_id
            
        db.commit()
        db.refresh(post)
        return post

@app.patch('/api/posts/{post_id}', response_model=PostResponse)
def update_post_partial(
    post_id: int,
    post_data: PostUpdate,
    db : Annotated[Session, Depends(get_db)]
):
    post = get_post(post_id,db)
    if post:
        update_data = post_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(post,field,value)
        db.commit()
        db.refresh(post)
        return post
        
@app.delete('/api/posts/{post_id}', status_code = status.HTTP_204_NO_CONTENT)
def delete_post(post_id:int, db: Annotated[Session, Depends(get_db)]):
    post = get_post(post_id, db)
    if post:
        db.delete(post)
        db.commit()

@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
   
    new_post = models.Post(
      user_id = post.user_id,
      title = post.title,
      content = post.content,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return new_post

#create user
@app.post(
    '/api/users',
    response_model=UserResponse,
    status_code= status.HTTP_201_CREATED
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.username == user.username)
    )
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail="username already exists"
        )
        
    result = db.execute(
        select(models.User).where(models.User.email == user.email)
    )
    existing_email = result.scalars().first()
    
    if existing_email:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail="email already exists"
        )
        
        
    new_user = models.User(
        username = user.username,
        email = user.email,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.get(
    "/api/users/{user_id}",
    response_model=UserResponse
)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()
    
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user not found')

@app.get(
    '/api/users/{user_id}/posts',
    response_model=list[PostResponse]
)
def get_user_posts(user_id, db: Annotated[Session, Depends(get_db)]):
    user = check_user_existence(user_id, db)
    if user:
        results = db.execute(
            select(models.Post).where(models.Post.user_id == user_id)
        )
        posts = results.scalars().all()
        return posts
    
@app.patch('/api/users/{user_id}',response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    user =  get_user(user_id,db)
    if user:
        if user_update.username is not None and user_update.username != user.username:
            user_exist =db.execute(
                select(models.User).where(models.User.username == user_update.username)
            ).scalars().first()
            if user_exist:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="username already exists"
                )
        if user_update.email is not None and user_update.email !=user.email:
            existing_email = db.execute(
                select(models.User).where(models.User.email == user_update.email)
            ).scalars().first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="email already exists"
                )
        user.username = user_update.username if user_update.username is not None else user.username
        user.email = user_update.email if user_update.email is not None else user.email
        user.image_file = user_update.image_file if user_update.image_file is not None else user.image_file
            
        db.commit()
        db.refresh(user)
        return user

def check_user_existence(u_id, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.id == u_id)
    )
    user= result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= 'user not found.'
        )
    return user

@app.delete('api/users/{user_id}', status_code= status.HTTP_204_NO_CONTENT)
def delete_user(user_id:int, db: Annotated[Session, Depends(get_db)]):
    user =  get_user(user_id,db)
    if user:
        db.delete(user)
        db.commit()
        
        
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