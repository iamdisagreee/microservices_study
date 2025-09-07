from typing import List, Optional

from app.repositories.posts import PostRepository
from app.schemas.post import Post, PostBase


class PostService:
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo

    async def get_all_posts(self, skip: int = 0, limit: int = 100) -> List[Post]:
        return await self.post_repo.get_all(skip=skip, limit=limit)

    async def get_post_by_id(self, post_id: int) -> Optional[Post]:
        return await self.post_repo.get_by_id(post_id)

    '''    async def get_posts_by_category(self, category_id: int, skip: int = 0, limit: int = 100) -> List[Post]:
        category = await self.category_repo.get_by_id(category_id)
        if category is None:
            # В сервисе можем вернуть None или поднять специфичное исключение сервисного уровня
            # Роутер обработает это и вернет соответствующий HTTP ответ
            return None
        return await self.post_repo.get_by_category_id(category_id, skip=skip, limit=limit)'''


    async def create_post(self, post: PostBase) -> Optional[Post]:
        '''# Бизнес-логика: проверяем существование категории перед созданием поста
        category = await self.category_repo.get_by_id(post.category_id)
        if category is None:
            return None # Возвращаем None, если категория не найдена'''

        return await self.post_repo.create(
            title=post.title,
            content=post.content,
            category_id=post.category_id
        )
