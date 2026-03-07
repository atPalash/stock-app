from typing import Any


def draw_graph(graph: Any, path: str):
    try:
        # Generate the PNG visualization
        png_data = graph.get_graph().draw_mermaid_png()

        # Save to file
        with open(path, "wb") as f:
            f.write(png_data)

        print(f"Graph visualization saved as '{path}'")
    except Exception as e:
        print(f"Exception generating graph visualization: {e}")
        print("Make sure you have the required dependencies installed:")
        print("pip install 'langgraph[mermaid]'")


def extract_gherkin(ai_content: str | Any) -> str:
    """Extract Gherkin scenario from AI response, removing any extraneous text."""
    lines = ai_content.split('\n')

    # Valid Gherkin keywords that start a line
    gherkin_keywords = {'Feature:', 'Scenario:',
                        'Given', 'When', 'Then', '*', 'And', 'But'}

    # Find the last line that is part of Gherkin
    first_gherkin_line = 0
    last_gherkin_line = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:  # Skip empty lines
            continue
        # Check if line starts with a Gherkin keyword
        if stripped.startswith("Feature:"):
            first_gherkin_line = i  # Always include Feature line
        if any(stripped.startswith(kw) for kw in gherkin_keywords):
            last_gherkin_line = i

    if last_gherkin_line < first_gherkin_line:
        # No valid Gherkin found, return original content
        return ai_content.strip()

    # Extract up to and including the last Gherkin line
    gherkin_section = '\n'.join(
        lines[first_gherkin_line:last_gherkin_line + 1]).strip()
    return gherkin_section
