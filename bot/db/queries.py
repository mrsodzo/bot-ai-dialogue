from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, Message


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    user = await get_user(session, telegram_id)
    if user:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        return user

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        stage="start",
    )
    session.add(user)
    await session.flush()
    return user


async def update_user_stage(session: AsyncSession, user: User, stage: str) -> None:
    user.stage = stage
    await session.flush()


async def update_user_profile(
    session: AsyncSession,
    user: User,
    name: str | None = None,
    age: int | None = None,
    goal: str | None = None,
) -> None:
    if name is not None:
        user.name = name
    if age is not None:
        user.age = age
    if goal is not None:
        user.goal = goal
    await session.flush()


async def reset_user(session: AsyncSession, user: User) -> None:
    user.name = None
    user.age = None
    user.goal = None
    user.stage = "start"
    await session.execute(delete(Message).where(Message.user_id == user.telegram_id))
    await session.flush()


async def add_message(
    session: AsyncSession,
    user_id: int,
    role: str,
    content: str,
) -> Message:
    message = Message(user_id=user_id, role=role, content=content)
    session.add(message)
    await session.flush()
    return message


async def get_user_history(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
) -> list[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return list(reversed(messages))


async def get_user_message_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(select(func.count(Message.id)).where(Message.user_id == user_id))
    return result.scalar() or 0