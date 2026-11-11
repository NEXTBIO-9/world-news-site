#!/usr/bin/env python3
"""Shared, conservative importance ranking for the news pipeline.

Importance changes processing order, never factual verification requirements.
"""
import re

HIGH_IMPACT = re.compile(
    r'(?i)\b(?:ceasefire|invasion|blockade|missile|airstrike|drone attack|'
    r'earthquake|tsunami|hurricane|typhoon|wildfire|mass casualty|'
    r'killed|deaths?|evacuat(?:ion|ed)|outbreak|pandemic|measles|'
    r'FDA approv(?:es|al|ed)|EMA approv(?:es|al|ed)|drug recall|'
    r'clinical trial|phase [123]|antimicrobial resistance|'
    r'central bank|interest rate|emergency declaration)\b|'
    r'휴전|침공|봉쇄|미사일|공습|드론 공격|지진|쓰나미|태풍|산불|'
    r'사망|대피|감염병|홍역|신약 승인|임상시험|항생제 내성|기준금리'
)
CAUTION = re.compile(r'(?i)\b(?:rumou?r|unconfirmed|allegedly|speculation)\b|미확인|루머')


def important(article):
    title = str(article.get('title') or '')
    return bool(HIGH_IMPACT.search(title)) and not bool(CAUTION.search(title))


def ordered(articles):
    """Stable ordering, urgent before routine."""
    return sorted(articles, key=lambda article: not important(article))
