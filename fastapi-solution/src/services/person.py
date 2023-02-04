from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends

from src.db.elastic import get_elastic
from src.db.cache import get_cache, Cache
from src.models.person import Person
from src.services.film import FilmService


class PersonService:
    def __init__(self, cache: Cache, elastic: AsyncElasticsearch):
        self.cache = cache
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)

        return person

    async def get_films_by_id(self, person_id: str) -> Optional[list[dict]]:
        films = FilmService(self.cache, self.elastic)
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)

        films_info = [await films.get_by_id(film_id)
                      for film_id in person.film_ids]
        return [{'uuid': info.id,
                 'title': info.title,
                 'imdb_rating': info.imdb_rating} for info in films_info]

    async def get_all(
        self,
        page_number: Optional[int],
        size: Optional[int]
    ) -> list[Optional[Person]]:
        try:
            page = await self.elastic.search(
                    index='persons',
                    body={'query': {'match_all': {}}},
                    size=size,
                    scroll='2m'
            )
        except NotFoundError:
            return []

        scroll_id = page['_scroll_id']
        hits = page['hits']['hits']

        if page_number > 1:
            for _ in range(1, page_number):
                page = await self.elastic.scroll(scroll_id=scroll_id,
                                                    scroll='2m')
                scroll_id = page['_scroll_id']
                hits = page['hits']['hits']

        return [Person(**hit['_source']) for hit in hits]


    async def search(self,
                     query: str,
                     page_number: Optional[int],
                     size: Optional[int]) -> list[Optional[Person]]:
        body = {
                'query': {
                        'multi_match': {
                                'query': query,
                                'fields': list(Person.__fields__.keys())
                        }
                }
        }
        try:
            page = await self.elastic.search(
                    index='persons',
                    body=body,
                    size=size,
                    scroll='2m'
            )
        except NotFoundError:
            return []

        scroll_id = page['_scroll_id']
        hits = page['hits']['hits']

        if page_number > 1:
            for _ in range(1, page_number):
                page = await self.elastic.scroll(scroll_id=scroll_id,
                                                    scroll='2m')
                scroll_id = page['_scroll_id']
                hits = page['hits']['hits']
        return [Person(**hit['_source']) for hit in hits]


    async def _get_person_from_elastic(
            self,
            person_id: str
    ) -> Optional[Person]:
        try:
            doc = await self.elastic.get('persons', person_id)
        except NotFoundError:
            return None
        return Person(**doc['_source'])

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        data = await self.cache.get(f'person_id_{person_id}')
        if not data:
            return None

        person = Person.parse_raw(data)
        return person

    async def _put_person_to_cache(self, person: Person):
        await self.cache.set(
                f'person_id_{person.id}',
                person.json()
        )


@lru_cache()
def get_person_service(
        cache: Cache = Depends(get_cache),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(cache, elastic)
