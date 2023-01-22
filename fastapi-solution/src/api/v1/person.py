from typing import Optional
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.person import PersonService, get_person_service

router = APIRouter()


class Person(BaseModel):
    id: str
    full_name: str
    roles: Optional[list[str]]
    film_ids: Optional[list[str]]


@router.get('/{person_id}', response_model=Person)
async def person_details(person_id: str, person_service: PersonService = Depends(get_person_service)) -> Person:
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return Person(id=person.id, full_name=person.full_name, roles=person.roles, film_ids=person.film_ids)
