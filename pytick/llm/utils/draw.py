from langgraph.graph import StateGraph

def draw_graph(graph: StateGraph, path:str) -> str:
    try:
        # Generate the PNG visualization
        png_data = graph.get_graph().draw_mermaid_png()
        
        # Save to file
        with open(path, "wb") as f:
            f.write(png_data)

        print(f"Graph visualization saved as '{path}'")
    except Exception as e:
        print(f"Error generating graph visualization: {e}")
        print("Make sure you have the required dependencies installed:")
        print("pip install 'langgraph[mermaid]'")
