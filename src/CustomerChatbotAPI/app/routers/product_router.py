"""Product router — product catalog endpoints for card rendering."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.domain.models import ProductResponse
from app.infrastructure.auth_middleware import get_current_user

router = APIRouter()


def _get_product_service(request: Request):
    return request.app.state.product_service


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    user: dict = Depends(get_current_user),
    product_service=Depends(_get_product_service),
) -> ProductResponse:
    """Get product details for front-end card rendering.

    Args:
        product_id: The product identifier.

    Returns:
        Product data including name, price, image URL, and attributes.
    """
    product = await product_service.get_product_async(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return ProductResponse(**product)
