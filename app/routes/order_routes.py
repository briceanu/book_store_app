from typing import Annotated

from fastapi import (APIRouter, Body, Depends, Form, HTTPException, Security,
                     status)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_async_db
from app.models.app_models import Author, User
from app.repositories.order_repository import OrderRepository
from app.repositories.user_logic import get_current_active_user
from app.schemas.order_schema import (OrderItemCreateRequest,
                                      OrderPlaceSuccessfully)
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/v1/order", tags=["routes for the order"])


@router.post(
    "/place-order",
    response_model=OrderPlaceSuccessfully,
    status_code=status.HTTP_200_OK,
)
async def buy_products(
    user: Annotated[User, Depends(get_current_active_user)],
    order_data: Annotated[OrderItemCreateRequest, Body()],
    async_session: Annotated[AsyncSession, Depends(get_async_db)],
) -> OrderPlaceSuccessfully:
    try:
        repo = OrderRepository(
            user=user, order_data=order_data, async_session=async_session
        )
        service = OrderService(repo)
        return await service.buy_books()
    except HTTPException:
        raise
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred: {str(e.orig)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )
