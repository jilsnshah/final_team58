import pathway as pw
from typing import Optional


class VerraSchema(pw.Schema):
    project_id: Optional[str]
    project_name: Optional[str]
    description: Optional[str]
    methodology: Optional[str]
    registry_status: Optional[str]
    country: Optional[str]
    vintage: Optional[int]
    price: Optional[float]
    available_credits: Optional[int]
    category: Optional[str]
    image_url: Optional[str]
    buy_link: Optional[str]
    project_summary: Optional[str]


class CarbonmarkSchema(pw.Schema):
    project_id: Optional[str]
    project_name: Optional[str]
    vintage: Optional[int]
    amount: Optional[float]
    project_summary: Optional[str]
    project_link: Optional[str]


class FinanceSchema(pw.Schema):
    ticker: Optional[str]
    company_name: Optional[str]
    industry: Optional[str]
    description: Optional[str]
    gii_score: Optional[int]
    stock_price: Optional[float]
    market_cap: Optional[str]
    sustainability_update: Optional[str]
    esg_rating: Optional[str]
    website: Optional[str]
    price: Optional[float]
    volume: Optional[int]
    change_percent: Optional[float]
    timestamp: Optional[int]


class NewsSchema(pw.Schema):
    news_id: Optional[str]
    title: Optional[str]
    summary: Optional[str]
    body: Optional[str]
    author: Optional[str]
    date: Optional[str]
    source: Optional[str]
    sentiment: Optional[str]
    image_url: Optional[str]
    guid: Optional[str]
    link: Optional[str]
    published: Optional[str]
