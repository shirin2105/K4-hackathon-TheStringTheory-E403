import discord
from typing import Dict, Any
from models.result import DecisionResult
from core.response_builder import ResponseBuilder


def create_result_embed(result: DecisionResult) -> discord.Embed:
    """
    Constructs a discord.Embed object from DecisionResult.
    """
    data = ResponseBuilder.build_embed_dict(result)
    embed = discord.Embed(
        title=data["title"],
        description=data["description"],
        color=data["color"]
    )

    for field in data.get("fields", []):
        embed.add_field(
            name=field["name"],
            value=field["value"],
            inline=field.get("inline", False)
        )

    if "footer" in data:
        embed.set_footer(text=data["footer"])

    return embed
