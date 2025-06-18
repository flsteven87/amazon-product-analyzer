"""
Product-related SQLAlchemy models for the Amazon Product Analyzer.

This module defines the Product and Competitor models with their relationships
and database schema.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped

from ..core.database import Base


class Product(Base):
    """
    Product model representing Amazon products being analyzed.
    
    Stores core product information including ASIN, title, pricing,
    ratings, and specifications.
    """
    
    __tablename__ = "products"
    
    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    
    # Amazon-specific identifiers
    asin: Mapped[str] = Column(String(20), unique=True, index=True, nullable=False)
    url: Mapped[str] = Column(Text, nullable=False)
    
    # Basic product information
    title: Mapped[str] = Column(Text, nullable=False)
    brand: Mapped[Optional[str]] = Column(String(255), nullable=True)
    category: Mapped[Optional[str]] = Column(String(255), nullable=True)
    
    # Pricing information
    price: Mapped[Optional[float]] = Column(Float, nullable=True)
    currency: Mapped[Optional[str]] = Column(String(10), default="USD")
    discount_percentage: Mapped[Optional[float]] = Column(Float, nullable=True)
    original_price: Mapped[Optional[float]] = Column(Float, nullable=True)
    
    # Rating and review information
    rating: Mapped[Optional[float]] = Column(Float, nullable=True)
    review_count: Mapped[Optional[int]] = Column(Integer, nullable=True, default=0)
    
    # Product details
    description: Mapped[Optional[str]] = Column(Text, nullable=True)
    specifications: Mapped[Optional[dict]] = Column(JSON, nullable=True)
    features: Mapped[Optional[list]] = Column(JSON, nullable=True)
    images: Mapped[Optional[list]] = Column(JSON, nullable=True)
    
    # Availability and seller information
    availability: Mapped[Optional[str]] = Column(String(100), nullable=True)
    seller: Mapped[Optional[str]] = Column(String(255), nullable=True)
    is_amazon_choice: Mapped[bool] = Column(Integer, default=False)
    is_bestseller: Mapped[bool] = Column(Integer, default=False)
    
    # SEO and marketing
    keywords: Mapped[Optional[list]] = Column(JSON, nullable=True)
    tags: Mapped[Optional[list]] = Column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # Relationships
    competitors: Mapped[List["Competitor"]] = relationship("Competitor", back_populates="product")
    analysis_sessions: Mapped[List["AnalysisSession"]] = relationship("AnalysisSession", back_populates="product")
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, asin='{self.asin}', title='{self.title[:50]}...')>"


class Competitor(Base):
    """
    Competitor model representing competing products discovered during analysis.
    
    Links to the main product and stores competitive analysis data.
    """
    
    __tablename__ = "competitors"
    
    # Primary key
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to main product
    product_id: Mapped[int] = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Competitor product identifiers
    competitor_asin: Mapped[str] = Column(String(20), nullable=False, index=True)
    competitor_url: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # Basic competitor information
    title: Mapped[Optional[str]] = Column(Text, nullable=True)
    brand: Mapped[Optional[str]] = Column(String(255), nullable=True)
    price: Mapped[Optional[float]] = Column(Float, nullable=True)
    rating: Mapped[Optional[float]] = Column(Float, nullable=True)
    review_count: Mapped[Optional[int]] = Column(Integer, nullable=True)
    
    # Competitive analysis metrics
    price_difference: Mapped[Optional[float]] = Column(Float, nullable=True)  # % difference
    rating_difference: Mapped[Optional[float]] = Column(Float, nullable=True)  # rating difference
    review_count_ratio: Mapped[Optional[float]] = Column(Float, nullable=True)  # ratio comparison
    
    # Competitive advantages/disadvantages
    competitive_advantages: Mapped[Optional[list]] = Column(JSON, nullable=True)
    competitive_disadvantages: Mapped[Optional[list]] = Column(JSON, nullable=True)
    
    # Discovery information
    discovery_method: Mapped[Optional[str]] = Column(String(100), nullable=True)  # e.g., "related_products", "search_results"
    similarity_score: Mapped[Optional[float]] = Column(Float, nullable=True)  # 0-1 similarity
    
    # Timestamps
    discovered_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    last_analyzed_at: Mapped[Optional[datetime]] = Column(DateTime, nullable=True)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="competitors")
    
    def __repr__(self) -> str:
        return f"<Competitor(id={self.id}, asin='{self.competitor_asin}', title='{self.title[:30] if self.title else 'N/A'}...')>" 