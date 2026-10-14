
from fastapi import Depends, HTTPException, status

from app.auth import get_current_user
from app.models import User


VALID_ROLES = {
    "marketing",
    "communication",
    "vigilance",
    "support",
    "sales",
}


def require_roles(*allowed_roles: str):
    """
    Create a dependency that allows only specified roles.
    """

    # Fail early if a developer accidentally specifies an invalid role.
    invalid_roles = set(allowed_roles) - VALID_ROLES

    if invalid_roles:
        raise ValueError(
            f"Invalid role(s): {', '.join(sorted(invalid_roles))}"
        )

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return role_checker
