"""清空人物数据并写入示例族谱。

用法:
    python scripts/seed_sample_data.py
    python scripts/seed_sample_data.py --family-id 6
    python scripts/seed_sample_data.py --all-families
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.family import Family
from app.models.geo_place import GeoPlace
from app.models.media import Media
from app.models.person import Person
from app.models.person_relation import PersonRelation
from app.schemas.relation_type import RelationType


def clear_family_person_data(db, family_id: int) -> None:
    person_ids = list(
        db.scalars(select(Person.id).where(Person.family_id == family_id)).all()
    )
    db.execute(delete(GeoPlace).where(GeoPlace.family_id == family_id))
    if person_ids:
        db.execute(delete(Media).where(Media.person_id.in_(person_ids)))
    db.execute(delete(PersonRelation).where(PersonRelation.family_id == family_id))
    db.execute(delete(Person).where(Person.family_id == family_id))


def add_person(
    db,
    family_id: int,
    *,
    name: str,
    nickname: str,
    gender: int,
    generation: int,
    birth_year: int,
    birthplace: str | None = None,
    phone: str | None = None,
    address: str | None = None,
    biography: str | None = None,
    remark: str | None = None,
    is_alive: int = 1,
) -> Person:
    person = Person(
        family_id=family_id,
        name=name,
        nickname=nickname,
        gender=gender,
        generation=generation,
        birth_year=birth_year,
        birthplace=birthplace,
        phone=phone,
        address=address,
        biography=biography,
        remark=remark,
        is_alive=is_alive,
    )
    db.add(person)
    db.flush()
    return person


def add_parent(db, family_id: int, parent: Person, child: Person) -> None:
    db.add(
        PersonRelation(
            family_id=family_id,
            from_person_id=parent.id,
            to_person_id=child.id,
            relation_type=RelationType.parent.value,
        )
    )


def add_spouse(db, family_id: int, a: Person, b: Person) -> None:
    from_id, to_id = sorted([a.id, b.id])
    db.add(
        PersonRelation(
            family_id=family_id,
            from_person_id=from_id,
            to_person_id=to_id,
            relation_type=RelationType.spouse.value,
        )
    )


def seed_li_family(db, family_id: int) -> tuple[int, int]:
    """李氏示例：6 世、约 20 人，覆盖男系/全谱/以人为中心等查看模式。"""
    # 第 1 世
    g1 = add_person(
        db,
        family_id,
        name="李德成",
        nickname="德成",
        gender=1,
        generation=1,
        birth_year=1870,
        birthplace="河南南阳",
        biography="李氏始迁祖，清末迁居此地开基。",
        remark="始祖",
        is_alive=0,
    )
    g1_wife = add_person(
        db,
        family_id,
        name="陈秀兰",
        nickname="秀兰",
        gender=2,
        generation=1,
        birth_year=1875,
        is_alive=0,
    )
    add_spouse(db, family_id, g1, g1_wife)

    # 第 2 世
    g2_elder = add_person(
        db,
        family_id,
        name="李仁和",
        nickname="仁和",
        gender=1,
        generation=2,
        birth_year=1895,
        remark="长子",
        is_alive=0,
    )
    g2_second = add_person(
        db,
        family_id,
        name="李仁义",
        nickname="仁义",
        gender=1,
        generation=2,
        birth_year=1898,
        remark="次子",
        is_alive=0,
    )
    g2_daughter = add_person(
        db,
        family_id,
        name="李秀英",
        nickname="秀英",
        gender=2,
        generation=2,
        birth_year=1902,
        remark="之女，外嫁不续谱",
        is_alive=0,
    )
    g2_wife = add_person(
        db,
        family_id,
        name="王氏",
        nickname="王氏",
        gender=2,
        generation=2,
        birth_year=1898,
        is_alive=0,
    )
    add_parent(db, family_id, g1, g2_elder)
    add_parent(db, family_id, g1, g2_second)
    add_parent(db, family_id, g1, g2_daughter)
    add_spouse(db, family_id, g2_elder, g2_wife)

    # 第 3 世（仁和一支）
    g3_a = add_person(
        db,
        family_id,
        name="李建国",
        nickname="建国",
        gender=1,
        generation=3,
        birth_year=1920,
        is_alive=0,
    )
    g3_b = add_person(
        db,
        family_id,
        name="李建军",
        nickname="建军",
        gender=1,
        generation=3,
        birth_year=1923,
        is_alive=0,
    )
    g3_c = add_person(
        db,
        family_id,
        name="李建梅",
        nickname="建梅",
        gender=2,
        generation=3,
        birth_year=1926,
        is_alive=1,
    )
    g3_wife = add_person(
        db,
        family_id,
        name="张氏",
        nickname="张氏",
        gender=2,
        generation=3,
        birth_year=1922,
        is_alive=0,
    )
    add_parent(db, family_id, g2_elder, g3_a)
    add_parent(db, family_id, g2_elder, g3_b)
    add_parent(db, family_id, g2_elder, g3_c)
    add_spouse(db, family_id, g3_a, g3_wife)

    # 仁义一支（第 3 世）
    g3_d = add_person(
        db,
        family_id,
        name="李志刚",
        nickname="志刚",
        gender=1,
        generation=3,
        birth_year=1925,
        is_alive=0,
    )
    add_parent(db, family_id, g2_second, g3_d)

    # 第 4 世
    g4_a = add_person(
        db,
        family_id,
        name="李伟民",
        nickname="伟民",
        gender=1,
        generation=4,
        birth_year=1948,
        is_alive=1,
    )
    g4_b = add_person(
        db,
        family_id,
        name="李伟国",
        nickname="伟国",
        gender=1,
        generation=4,
        birth_year=1951,
        is_alive=1,
    )
    g4_c = add_person(
        db,
        family_id,
        name="李丽华",
        nickname="丽华",
        gender=2,
        generation=4,
        birth_year=1954,
        is_alive=1,
    )
    g4_wife = add_person(
        db,
        family_id,
        name="赵敏",
        nickname="敏敏",
        gender=2,
        generation=4,
        birth_year=1950,
        is_alive=1,
    )
    add_parent(db, family_id, g3_a, g4_a)
    add_parent(db, family_id, g3_a, g4_b)
    add_parent(db, family_id, g3_a, g4_c)
    add_spouse(db, family_id, g4_a, g4_wife)

    g4_d = add_person(
        db,
        family_id,
        name="李伟东",
        nickname="伟东",
        gender=1,
        generation=4,
        birth_year=1953,
        is_alive=1,
    )
    add_parent(db, family_id, g3_b, g4_d)

    # 第 5 世
    g5_a = add_person(
        db,
        family_id,
        name="李明远",
        nickname="明远",
        gender=1,
        generation=5,
        birth_year=1975,
        phone="13800001111",
        address="河南新乡卫滨区平原镇李庄 12 号",
        is_alive=1,
    )
    g5_b = add_person(
        db,
        family_id,
        name="李明辉",
        nickname="明辉",
        gender=1,
        generation=5,
        birth_year=1978,
        phone="13900002222",
        address="河南新乡牧野区建设路 88 号",
        is_alive=1,
    )
    g5_c = add_person(
        db,
        family_id,
        name="李晓燕",
        nickname="晓燕",
        gender=2,
        generation=5,
        birth_year=1980,
        is_alive=1,
    )
    g5_wife = add_person(
        db,
        family_id,
        name="孙婷",
        nickname="婷婷",
        gender=2,
        generation=5,
        birth_year=1977,
        is_alive=1,
    )
    add_parent(db, family_id, g4_a, g5_a)
    add_parent(db, family_id, g4_a, g5_b)
    add_parent(db, family_id, g4_a, g5_c)
    add_spouse(db, family_id, g5_a, g5_wife)

    g5_d = add_person(
        db,
        family_id,
        name="李明杰",
        nickname="明杰",
        gender=1,
        generation=5,
        birth_year=1982,
        is_alive=1,
    )
    add_parent(db, family_id, g4_d, g5_d)

    # 第 6 世
    g6_a = add_person(
        db,
        family_id,
        name="李子涵",
        nickname="子涵",
        gender=1,
        generation=6,
        birth_year=2002,
        is_alive=1,
    )
    g6_b = add_person(
        db,
        family_id,
        name="李子萱",
        nickname="子萱",
        gender=2,
        generation=6,
        birth_year=2005,
        is_alive=1,
    )
    g6_c = add_person(
        db,
        family_id,
        name="李子轩",
        nickname="子轩",
        gender=1,
        generation=6,
        birth_year=2008,
        is_alive=1,
    )
    add_parent(db, family_id, g5_a, g6_a)
    add_parent(db, family_id, g5_a, g6_b)
    add_parent(db, family_id, g5_b, g6_c)

    # 地理标记示例（河南南阳一带坐标，便于地图联调）
    db.add(
        GeoPlace(
            family_id=family_id,
            place_type="distribution",
            name="李氏祖居地（南阳）",
            longitude=112.528320,
            latitude=32.990760,
            address="河南省南阳市",
            description="李氏祖居与早期聚居地",
            related_person_id=g1.id,
        )
    )
    db.add(
        GeoPlace(
            family_id=family_id,
            place_type="distribution",
            name="当代族人分布（郑州）",
            longitude=113.625368,
            latitude=34.746611,
            address="河南省郑州市",
            description="近代外出求学、工作形成的聚居点",
        )
    )
    db.add(
        GeoPlace(
            family_id=family_id,
            place_type="cemetery",
            name="先祖墓地（桐柏）",
            longitude=113.428530,
            latitude=32.379170,
            address="河南省南阳市桐柏县",
            description="一至三世祖坟所在地",
            related_person_id=g1.id,
        )
    )

    persons = db.scalars(select(Person).where(Person.family_id == family_id)).all()
    relations = db.scalars(
        select(PersonRelation).where(PersonRelation.family_id == family_id)
    ).all()
    return len(persons), len(relations)


def resolve_family_id(db, family_id: int | None) -> int:
    if family_id is not None:
        family = db.get(Family, family_id)
        if family is None:
            raise SystemExit(f"家族 {family_id} 不存在")
        return family.id

    family = db.scalar(select(Family).order_by(Family.id.desc()).limit(1))
    if family is None:
        raise SystemExit("数据库中没有任何家族，请先在系统中创建家族")
    return family.id


def main() -> None:
    parser = argparse.ArgumentParser(description="清空人物数据并写入示例族谱")
    parser.add_argument("--family-id", type=int, default=None, help="目标家族 ID，默认取最新家族")
    parser.add_argument(
        "--all-families",
        action="store_true",
        help="清空所有家族的人物数据（仅在目标家族写入示例）",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        target_family_id = resolve_family_id(db, args.family_id)
        target_family = db.get(Family, target_family_id)
        assert target_family is not None

        if args.all_families:
            families = db.scalars(select(Family)).all()
            for family in families:
                clear_family_person_data(db, family.id)
                print(f"[DEL] 已清空家族 {family.id} ({family.name}) 的人物数据")
        else:
            clear_family_person_data(db, target_family_id)
            print(f"[DEL] 已清空家族 {target_family_id} ({target_family.name}) 的人物数据")

        target_family.name = "李氏"
        person_count, relation_count = seed_li_family(db, target_family_id)
        db.commit()

        print(
            f"[OK] 已在家族 {target_family_id} ({target_family.name}) 写入示例数据："
            f"{person_count} 人，{relation_count} 条关系"
        )
        print("     始祖：李德成（第1世）→ 可试「世系全图」「男系世系」「以人为中心」")
    except Exception as exc:
        db.rollback()
        raise SystemExit(f"失败: {exc}") from exc
    finally:
        db.close()


if __name__ == "__main__":
    main()
