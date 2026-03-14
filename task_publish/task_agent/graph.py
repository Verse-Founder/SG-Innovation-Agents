from langgraph.graph import StateGraph, END
from task_publish.task_agent.state import AgentState
from task_publish.task_agent.nodes.analyst import analyst_node
from task_publish.task_agent.nodes.advisor import advisor_node
from task_publish.task_agent.nodes.writer import writer_node

def build_copy_subgraph():
    g = StateGraph(AgentState)
    g.add_node("analyst", analyst_node)
    g.add_node("advisor", advisor_node)
    g.add_node("writer",  writer_node)

    g.set_entry_point("analyst")

    g.add_edge("analyst", "advisor")
    g.add_edge("advisor", "writer")
    g.add_edge("writer",  END)

    return g.compile()

copy_subgraph = build_copy_subgraph()
