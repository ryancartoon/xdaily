import click
from loguru import logger

from backend.service import start_news_chain


@click.group()
def cli():
    """News Analysis CLI Tool"""
    pass


@cli.command()
def analyze():
    """Analyze fetched news articles"""

    start_news_chain()


if __name__ == '__main__':
    cli() 