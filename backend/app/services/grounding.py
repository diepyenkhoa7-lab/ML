"""Source-grounded prediction features; raw model extraction remains untouched."""


def description_skills(source):
    # Lazy reuse avoids the chart/data import cycle in the offline review utilities.
    from scripts.refine_gemma_references import literal_skills

    return literal_skills(
        source, aliases={"graphql api": "GraphQL", "ant design mobile": "Ant Design Mobile"}
    )
