from sqlalchemy import func, select

from sqlalchemy.orm import Session



from app.models.family import Family

from app.models.person import Person

from app.models.user import User

from app.schemas.family import FamilyCreate, FamilyUpdate

from app.schemas.tree import FamilyStatsResponse

from app.utils.exceptions import ForbiddenException, NotFoundException



GENDER_MALE = 1

GENDER_FEMALE = 2



def _get_owned_family(db: Session, family_id: int, current_user: User) -> Family:

    family = db.get(Family, family_id)

    if family is None:

        raise NotFoundException("家族不存在")

    if family.owner_id != current_user.id:

        raise ForbiddenException("无权访问该家族")

    return family





def create_family(db: Session, current_user: User, data: FamilyCreate) -> Family:

    family = Family(

        owner_id=current_user.id,

        name=data.name,

        description=data.description,

        origin_place=data.origin_place,

    )

    db.add(family)

    db.commit()

    db.refresh(family)

    return family





def list_families(db: Session, current_user: User) -> list[Family]:

    return list(

        db.scalars(

            select(Family)

            .where(Family.owner_id == current_user.id)

            .order_by(Family.id.desc())

        ).all()

    )





def get_family(db: Session, family_id: int, current_user: User) -> Family:

    return _get_owned_family(db, family_id, current_user)





def update_family(

    db: Session, family_id: int, current_user: User, data: FamilyUpdate

) -> Family:

    family = _get_owned_family(db, family_id, current_user)

    payload = data.model_dump(exclude_unset=True)

    for key, value in payload.items():

        setattr(family, key, value)

    db.commit()

    db.refresh(family)

    return family





def delete_family(db: Session, family_id: int, current_user: User) -> None:

    family = _get_owned_family(db, family_id, current_user)

    db.delete(family)

    db.commit()





def get_family_stats(db: Session, family_id: int, current_user: User) -> FamilyStatsResponse:

    _get_owned_family(db, family_id, current_user)

    persons = db.scalars(select(Person).where(Person.family_id == family_id)).all()

    generations = [person.generation for person in persons if person.generation is not None]

    min_gen = min(generations) if generations else None

    max_gen = max(generations) if generations else None

    return FamilyStatsResponse(

        person_count=len(persons),

        male_count=sum(1 for person in persons if person.gender == GENDER_MALE),

        female_count=sum(1 for person in persons if person.gender == GENDER_FEMALE),

        min_generation=min_gen,

        max_generation=max_gen,

        generation_span=(max_gen - min_gen + 1) if min_gen is not None and max_gen is not None else 0,

    )

