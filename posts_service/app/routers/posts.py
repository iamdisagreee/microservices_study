import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.core.dependencies import get_post_service
from app.schemas.post import Post, PostBase
from app.services.posts import PostService
from app.core.logging_config import logger
# from app.core.dependencies import get_redis_client_dependency
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache
from fastapi_limiter.depends import RateLimiter

import redis.asyncio as redis


router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

# # Тест подключения к Redis
# @router.get('/redis_connect')
# async def redis_connect_test(r: redis.Redis = Depends(get_redis_client_dependency)):
#     await r.ping()
#     return {'message': 'Успешное подключение к Redis'}

@router.get("/", response_model=List[Post])
@cache(expire=60)
async def read_posts(
        skip: int = 0,
        limit: int = 100,
        post_service: PostService = Depends(get_post_service)  # Инъекция сервиса поста
):
    """Получить список всех постов или постов по ID категории."""

    posts = await post_service.get_all_posts(skip=skip, limit=limit)
    return posts


@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(
        post: PostBase,
        post_service: PostService = Depends(get_post_service)  # Инъекция сервиса поста
):
    """Создать новый пост."""
    # Сервис вернет None, если категория не найдена или другая бизнес-логика запрещает создание
    db_post = await post_service.create_post(post=post)
    if db_post is None:
        # Здесь можно более точно определить причину, но мы упрощаем это, для простоты понимания
        raise HTTPException(status_code=400, detail="Invalid category_id or unable to create post")
    await FastAPICache.clear() # await FastAPICache.clear(key=f"/item/{item_id}") - обновление

    return db_post

@cache(expire=60)
@router.get("/{post_id}", response_model=Post, dependencies=[Depends(RateLimiter(times=5, minutes=5))])
async def read_post(
        post_id: int,
        post_service: PostService = Depends(get_post_service),
        # r: redis.Redis = Depends(get_redis_client_dependency)
):
    """Получить пост по ID + работа с кэшем"""
    #
    # cache_key = f"post:{post_id}"
    # cached = await r.get(cache_key)
    # if cached:
    #     post = Post.model_validate_json(cached)
    #     return post
    db_post = await post_service.get_post_by_id(post_id=post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    # await r.set(cache_key, Post.model_validate(db_post).model_dump_json(), ex=60)
    # logger.info(f"Post '{post_id}' успешно передан.")
    return db_post
