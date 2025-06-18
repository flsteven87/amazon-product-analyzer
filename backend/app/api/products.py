"""
Product API endpoints for Amazon Product Analyzer.

This module provides RESTful API endpoints for product management,
including CRUD operations and product information retrieval.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, HttpUrl

from ..core.database import get_async_db
from ..models.product import Product, Competitor

router = APIRouter()


# Pydantic models for request/response
class ProductBase(BaseModel):
    """Base product model for common fields."""
    asin: str
    url: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "USD"
    discount_percentage: Optional[float] = None
    original_price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    description: Optional[str] = None
    specifications: Optional[dict] = None
    features: Optional[list] = None
    images: Optional[list] = None
    availability: Optional[str] = None
    seller: Optional[str] = None
    is_amazon_choice: bool = False
    is_bestseller: bool = False
    keywords: Optional[list] = None
    tags: Optional[list] = None


class ProductCreate(ProductBase):
    """Product creation model."""
    pass


class ProductUpdate(BaseModel):
    """Product update model with optional fields."""
    title: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    discount_percentage: Optional[float] = None
    original_price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    description: Optional[str] = None
    specifications: Optional[dict] = None
    features: Optional[list] = None
    images: Optional[list] = None
    availability: Optional[str] = None
    seller: Optional[str] = None
    is_amazon_choice: Optional[bool] = None
    is_bestseller: Optional[bool] = None
    keywords: Optional[list] = None
    tags: Optional[list] = None


class ProductResponse(ProductBase):
    """Product response model."""
    id: int
    created_at: str
    updated_at: str
    last_scraped_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class CompetitorResponse(BaseModel):
    """Competitor response model."""
    id: int
    product_id: int
    competitor_asin: str
    competitor_url: Optional[str] = None
    title: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_difference: Optional[float] = None
    rating_difference: Optional[float] = None
    review_count_ratio: Optional[float] = None
    competitive_advantages: Optional[list] = None
    competitive_disadvantages: Optional[list] = None
    discovery_method: Optional[str] = None
    similarity_score: Optional[float] = None
    discovered_at: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term for product title or ASIN"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve a list of products with optional filtering and pagination.
    
    Args:
        skip (int): Number of records to skip for pagination.
        limit (int): Maximum number of records to return.
        search (Optional[str]): Search term for product title or ASIN.
        category (Optional[str]): Filter products by category.
        db (AsyncSession): Database session dependency.
    
    Returns:
        List[ProductResponse]: List of product records.
    """
    query = select(Product)
    
    # Apply search filter
    if search:
        query = query.where(
            (Product.title.ilike(f"%{search}%")) |
            (Product.asin.ilike(f"%{search}%"))
        )
    
    # Apply category filter
    if category:
        query = query.where(Product.category.ilike(f"%{category}%"))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve a specific product by ID.
    
    Args:
        product_id (int): Product ID to retrieve.
        db (AsyncSession): Database session dependency.
    
    Returns:
        ProductResponse: Product details.
    
    Raises:
        HTTPException: If product not found.
    """
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.get("/asin/{asin}", response_model=ProductResponse)
async def get_product_by_asin(
    asin: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve a product by its ASIN.
    
    Args:
        asin (str): Amazon Standard Identification Number.
        db (AsyncSession): Database session dependency.
    
    Returns:
        ProductResponse: Product details.
    
    Raises:
        HTTPException: If product not found.
    """
    query = select(Product).where(Product.asin == asin)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new product record.
    
    Args:
        product_data (ProductCreate): Product data to create.
        db (AsyncSession): Database session dependency.
    
    Returns:
        ProductResponse: Created product details.
    
    Raises:
        HTTPException: If product with ASIN already exists.
    """
    # Check if product with ASIN already exists
    existing_query = select(Product).where(Product.asin == product_data.asin)
    existing_result = await db.execute(existing_query)
    existing_product = existing_result.scalar_one_or_none()
    
    if existing_product:
        raise HTTPException(
            status_code=400,
            detail=f"Product with ASIN '{product_data.asin}' already exists"
        )
    
    # Create new product
    product = Product(**product_data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update an existing product.
    
    Args:
        product_id (int): Product ID to update.
        product_data (ProductUpdate): Product data to update.
        db (AsyncSession): Database session dependency.
    
    Returns:
        ProductResponse: Updated product details.
    
    Raises:
        HTTPException: If product not found.
    """
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update product fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a product and its associated data.
    
    Args:
        product_id (int): Product ID to delete.
        db (AsyncSession): Database session dependency.
    
    Raises:
        HTTPException: If product not found.
    """
    query = select(Product).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.delete(product)
    await db.commit()


@router.get("/{product_id}/competitors", response_model=List[CompetitorResponse])
async def get_product_competitors(
    product_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Retrieve all competitors for a specific product.
    
    Args:
        product_id (int): Product ID to get competitors for.
        db (AsyncSession): Database session dependency.
    
    Returns:
        List[CompetitorResponse]: List of competitor records.
    
    Raises:
        HTTPException: If product not found.
    """
    # Verify product exists
    product_query = select(Product).where(Product.id == product_id)
    product_result = await db.execute(product_query)
    product = product_result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get competitors
    competitors_query = select(Competitor).where(Competitor.product_id == product_id)
    competitors_result = await db.execute(competitors_query)
    competitors = competitors_result.scalars().all()
    
    return competitors 