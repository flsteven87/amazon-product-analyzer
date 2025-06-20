"""Amazon competitor discovery using recommendation algorithms."""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from selectolax.parser import HTMLParser

logger = logging.getLogger(__name__)


@dataclass
class CompetitorCandidate:
    """Represents a potential competitor product."""

    asin: str
    title: str
    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    brand: Optional[str] = None
    url: str = ""
    source_section: str = ""  # 來源推薦區域
    confidence_score: float = 0.0

    def __post_init__(self):
        if not self.url and self.asin:
            self.url = f"https://www.amazon.com/dp/{self.asin}"


class AmazonCompetitorExtractor:
    """Extract competitor products from Amazon recommendation sections."""

    def __init__(self):
        self.recommendation_selectors = {
            # Customers who viewed this item also viewed - highest priority
            "customers_also_viewed": {
                "container": "[data-feature-name='customers-who-viewed'], [id*='customers-who-viewed'], [data-feature-name='dp-desktop-btf']",
                "items": "[data-asin]:not([data-asin=''])",
                "confidence": 0.95,
            },
            # Frequently bought together
            "frequently_bought_together": {
                "container": "[data-feature-name='frequently-bought-together'], [id*='frequently-bought']",
                "items": "[data-asin]:not([data-asin=''])",
                "confidence": 0.93,
            },
            # Products related to this item
            "related_products": {
                "container": "[data-feature-name*='related'], [id*='related-products'], [data-feature-name='sp-atf']",
                "items": "[data-asin]:not([data-asin=''])",
                "confidence": 0.9,
            },
            # Sponsored products section
            "sponsored_detail": {
                "container": "[id*='sp_detail_thematic'], [data-feature-name*='sponsored']",
                "items": "[data-asin][data-adfeedbackdetails], [data-asin]:not([data-asin=''])",
                "confidence": 0.88,
            },
            # Similar items recommendations  
            "similar_items": {
                "container": "[id*='sims-consolidated'], [data-feature-name*='sims'], [data-feature-name='similarities']",
                "items": "[data-asin]:not([data-asin=''])",
                "confidence": 0.85,
            },
            # Compare similar items section
            "compare_similar": {
                "container": "[data-feature-name='compare-similar-items'], [id*='compare-similar']",
                "items": "[data-asin]:not([data-asin=''])",
                "confidence": 0.82,
            },
            # Carousel recommendations (generic)
            "carousel_items": {
                "container": ".a-carousel, [data-feature-name*='carousel']",
                "items": ".a-carousel-card[data-asin], [data-asin]:not([data-asin=''])",
                "confidence": 0.75,
            },
            # Personalized recommendations
            "personalized": {
                "container": "[class*='p13n-asin'], [data-feature-name*='personal']",
                "items": "[data-asin]:not([data-asin=''])",
                "confidence": 0.7,
            },
            # General data-asin fallback
            "general_recommendations": {
                "container": "body",
                "items": "[data-asin]:not([data-asin=''])",
                "confidence": 0.5,
            },
        }

    async def extract_competitors(self, html_content: str, main_product_asin: str) -> List[CompetitorCandidate]:
        """從Amazon頁面HTML提取競品候選者。"""
        logger.info(f"Extracting competitors for main product: {main_product_asin}")
        logger.info(f"HTML content length: {len(html_content)} characters")

        # 使用 selectolax 進行高效HTML解析
        tree = HTMLParser(html_content)

        competitors = []
        seen_asins = {main_product_asin}  # 避免重複和包含主產品

        # 調試：檢查頁面中所有data-asin元素
        all_data_asin_elements = tree.css("[data-asin]")
        logger.info(f"Total data-asin elements found: {len(all_data_asin_elements)}")
        
        # 顯示前5個ASIN作為調試信息
        for i, elem in enumerate(all_data_asin_elements[:5]):
            asin = elem.attributes.get("data-asin", "")
            logger.info(f"Sample ASIN {i+1}: {asin}")

        # 遍歷所有推薦區域
        for section_name, selector_config in self.recommendation_selectors.items():
            logger.info(f"Processing section: {section_name}")
            section_competitors = await self._extract_from_section(tree, section_name, selector_config, seen_asins)
            competitors.extend(section_competitors)

            # 更新已見過的ASIN
            seen_asins.update(comp.asin for comp in section_competitors)

            logger.info(f"Found {len(section_competitors)} competitors from {section_name}")
            for comp in section_competitors[:3]:  # 顯示前3個作為樣本
                logger.info(f"  Sample: {comp.asin} - {comp.title[:50]}...")

        # 智能過濾和排序
        filtered_competitors = self._filter_and_rank_competitors(competitors, main_product_asin)

        logger.info(f"Raw competitors: {len(competitors)}, Filtered competitors: {len(filtered_competitors)}")
        return filtered_competitors[:10]  # 返回top 10競品

    async def _extract_from_section(
        self, tree: HTMLParser, section_name: str, selector_config: Dict[str, Any], seen_asins: Set[str]
    ) -> List[CompetitorCandidate]:
        """從特定推薦區域提取競品。"""
        competitors = []

        try:
            # 找到推薦區域容器
            containers = tree.css(selector_config["container"])

            for container in containers:
                # 在容器內查找產品項目
                items = container.css(selector_config["items"])

                for item in items:
                    try:
                        candidate = self._parse_competitor_item(item, section_name, selector_config["confidence"])

                        if candidate and candidate.asin not in seen_asins:
                            competitors.append(candidate)

                    except Exception as e:
                        logger.debug(f"Error parsing item in {section_name}: {str(e)}")
                        continue

        except Exception as e:
            logger.warning(f"Error extracting from section {section_name}: {str(e)}")

        return competitors

    def _parse_competitor_item(
        self, item_element, section_name: str, confidence: float
    ) -> Optional[CompetitorCandidate]:
        """解析單個競品項目。"""
        # 提取ASIN
        asin = item_element.attributes.get("data-asin")
        if not asin:
            return None

        # 提取標題
        title = self._extract_title(item_element)
        if not title:
            return None

        # 提取價格
        price = self._extract_price(item_element)

        # 提取評分
        rating = self._extract_rating(item_element)

        # 提取評論數量
        review_count = self._extract_review_count(item_element)

        # 提取品牌
        brand = self._extract_brand(item_element, title)

        return CompetitorCandidate(
            asin=asin,
            title=title,
            price=price,
            rating=rating,
            review_count=review_count,
            brand=brand,
            source_section=section_name,
            confidence_score=confidence,
        )

    def _extract_title(self, element) -> Optional[str]:
        """提取產品標題。"""
        # 多種標題選擇器
        title_selectors = ["a[title]", "[data-rows] span", "h3 a", ".s-size-mini span", "[aria-label*='title']"]

        for selector in title_selectors:
            title_elem = element.css_first(selector)
            if title_elem:
                title = title_elem.attributes.get("title") or title_elem.text()
                if title and len(title.strip()) > 10:  # 合理的標題長度
                    return title.strip()

        return None

    def _extract_price(self, element) -> Optional[float]:
        """Extract product price with improved Amazon-specific methods."""
        # First try to extract from data attributes (most reliable)
        feedback_data = element.attributes.get("data-adfeedbackdetails")
        if feedback_data:
            try:
                import json

                data = json.loads(feedback_data)
                price_amount = data.get("priceAmount")
                if price_amount and isinstance(price_amount, (int, float)):
                    return float(price_amount)
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass

        # Then try CSS selectors
        price_selectors = [
            ".a-price .a-offscreen",
            ".a-price-whole",
            "[class*='price'] .a-offscreen",
            "[data-a-price]",
            "span[class*='price']",
        ]

        for selector in price_selectors:
            price_elem = element.css_first(selector)
            if price_elem:
                price_text = price_elem.text()
                if price_text:
                    # Use TextProcessor for consistent price extraction
                    from .product_parser import TextProcessor

                    price = TextProcessor.extract_price(price_text)
                    if price:
                        return price

        return None

    def _extract_rating(self, element) -> Optional[float]:
        """Extract product rating with improved Amazon patterns."""
        # Method 1: Extract from aria-label attributes (most reliable)
        rating_links = element.css("a[aria-label*='out of']")
        for link in rating_links:
            aria_label = link.attributes.get("aria-label", "")
            match = re.search(r"(\d+\.?\d*)\s+out\s+of\s+5", aria_label)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        # Method 2: Extract from star class names
        star_elements = element.css("i[class*='a-star-']")
        for star_elem in star_elements:
            rating_class = star_elem.attributes.get("class", "")
            # Match patterns like "a-star-4-5" or "a-star-mini-4-5"
            rating_match = re.search(r"a-star(?:-mini)?-(\d+)(?:-(\d+))?", rating_class)
            if rating_match:
                try:
                    whole = int(rating_match.group(1))
                    fraction = int(rating_match.group(2)) if rating_match.group(2) else 0
                    return float(f"{whole}.{fraction}")
                except (ValueError, TypeError):
                    continue

        # Method 3: Generic star pattern fallback
        rating_elem = element.css_first("[class*='star']")
        if rating_elem:
            rating_class = rating_elem.attributes.get("class", "")
            rating_match = re.search(r"star[^0-9]*(\d+(?:[-_]\d+)?)", rating_class)
            if rating_match:
                rating_str = rating_match.group(1).replace("-", ".").replace("_", ".")
                try:
                    return float(rating_str)
                except ValueError:
                    pass

        return None

    def _extract_review_count(self, element) -> Optional[int]:
        """Extract review count from competitor elements."""
        # Method 1: Look for review count in aria-labels
        review_links = element.css("a[aria-label*='ratings'], a[aria-label*='Reviews']")
        for link in review_links:
            aria_label = link.attributes.get("aria-label", "")
            # Use TextProcessor for consistent extraction
            from .product_parser import TextProcessor

            count = TextProcessor.extract_review_count(aria_label)
            if count:
                return count

        # Method 2: Look for review count in text elements
        review_selectors = [
            "span[aria-hidden='true']",  # Amazon often puts counts here
            ".a-size-mini",
            ".a-color-secondary",
            "span[class*='review']",
        ]

        for selector in review_selectors:
            elements = element.css(selector)
            for elem in elements:
                text = elem.text()
                if text and any(keyword in text.lower() for keyword in ["rating", "review"]):
                    from .product_parser import TextProcessor

                    count = TextProcessor.extract_review_count(text)
                    if count:
                        return count

        return None

    def _extract_brand(self, element, title: str) -> Optional[str]:
        """提取產品品牌。"""
        # 從標題中提取品牌（通常是第一個詞）
        if title:
            title_words = title.split()
            if title_words:
                potential_brand = title_words[0]
                # 過濾明顯不是品牌的詞
                if len(potential_brand) > 2 and potential_brand.lower() not in ["the", "for", "with"]:
                    return potential_brand

        return None

    def _filter_and_rank_competitors(
        self, competitors: List[CompetitorCandidate], main_product_asin: str
    ) -> List[CompetitorCandidate]:
        """智能過濾和排序競品。"""
        if not competitors:
            return []

        # 獲取主產品品牌用於過濾
        main_brand = self._infer_main_brand(competitors)

        filtered = []
        for competitor in competitors:
            # 過濾條件
            if self._is_valid_competitor(competitor, main_brand, main_product_asin):
                # 計算綜合評分
                competitor.confidence_score = self._calculate_composite_score(competitor)
                filtered.append(competitor)

        # 按評分排序
        filtered.sort(key=lambda x: x.confidence_score, reverse=True)

        return filtered

    def _infer_main_brand(self, competitors: List[CompetitorCandidate]) -> Optional[str]:
        """從競品列表推斷主產品品牌。"""
        # 統計品牌出現頻率，最高頻的可能是主產品品牌
        brand_counts = {}
        for comp in competitors:
            if comp.brand:
                brand_counts[comp.brand] = brand_counts.get(comp.brand, 0) + 1

        if brand_counts:
            return max(brand_counts.items(), key=lambda x: x[1])[0]

        return None

    def _is_valid_competitor(
        self, competitor: CompetitorCandidate, main_brand: Optional[str], main_product_asin: str
    ) -> bool:
        """判斷是否為有效競品。"""
        # 基本驗證
        if not competitor.asin or not competitor.title:
            return False

        # ASIN格式驗證
        if not re.match(r"^B[0-9A-Z]{9}$", competitor.asin):
            return False

        # 排除主產品
        if competitor.asin == main_product_asin:
            return False

        # 排除同品牌產品（可選，根據需求調整）
        if main_brand and competitor.brand and competitor.brand.lower() == main_brand.lower():
            logger.debug(f"Filtering same brand product: {competitor.asin}")
            return False

        # 標題長度合理性檢查
        if len(competitor.title) < 10 or len(competitor.title) > 200:
            return False

        return True

    def _calculate_composite_score(self, competitor: CompetitorCandidate) -> float:
        """計算競品綜合評分。"""
        score = competitor.confidence_score

        # 評分加分
        if competitor.rating and competitor.rating >= 4.0:
            score += 0.1

        # 價格合理性加分
        if competitor.price and 10 <= competitor.price <= 500:
            score += 0.05

        # 標題完整性加分
        if competitor.title and len(competitor.title) > 50:
            score += 0.05

        return min(score, 1.0)  # 限制最高分為1.0


# 添加到tools/__init__.py
from dataclasses import dataclass
