from dataclasses import dataclass

from mash.servers.repository import create_user


@dataclass
class RawUser:
    name: str
    email: str


def init_users():
    for i in range(10):
        user = generate_user(i)
        create_user(user.name, user.email)


def generate_user(i: int) -> RawUser:
    return RawUser(f'name_{i}', f'name.{i}@company.com')
