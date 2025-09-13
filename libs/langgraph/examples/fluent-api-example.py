"""
Comprehensive example demonstrating the LangGraph Fluent API.

This example shows how to use the new FluentNode and FluentWorkflow classes
to create workflows with a more intuitive, operator-overloaded syntax.

The example implements a simple document processing workflow that:
1. Validates input documents
2. Processes the content
3. Generates a summary
4. Saves the results

This demonstrates all the key features of the Fluent API including:
- Creating nodes with >> operator
- Chaining nodes together
- Conditional routing
- Error handling
- Integration with existing LangGraph features
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph.fluent import FluentNode, create_workflow


# Define the state schema
class DocumentProcessingState(TypedDict):
    """State schema for the document processing workflow."""
    document: str
    is_valid: bool
    processed_content: str
    summary: str
    error_message: str
    processing_step: str


# Node functions
def validate_document(state: DocumentProcessingState) -> Dict[str, Any]:
    """Validate the input document."""
    document = state.get("document", "")

    if not document or len(document.strip()) < 10:
        return {
            "is_valid": False,
            "error_message": "Document is too short or empty",
            "processing_step": "validation_failed"
        }

    return {
        "is_valid": True,
        "error_message": "",
        "processing_step": "validation_passed"
    }


def process_content(state: DocumentProcessingState) -> Dict[str, Any]:
    """Process the document content."""
    document = state.get("document", "")

    # Simple processing: convert to uppercase and add metadata
    processed = f"PROCESSED: {document.upper()}"

    return {
        "processed_content": processed,
        "processing_step": "content_processed"
    }


def generate_summary(state: DocumentProcessingState) -> Dict[str, Any]:
    """Generate a summary of the processed content."""
    content = state.get("processed_content", "")

    # Simple summary: first 100 characters + word count
    word_count = len(content.split())
    summary = f"Summary: {content[:100]}... (Total words: {word_count})"

    return {
        "summary": summary,
        "processing_step": "summary_generated"
    }


def save_results(state: DocumentProcessingState) -> Dict[str, Any]:
    """Save the processing results."""
    summary = state.get("summary", "")

    # In a real scenario, this would save to a database or file
    print(f"Saving results: {summary}")

    return {
        "processing_step": "results_saved"
    }


def handle_error(state: DocumentProcessingState) -> Dict[str, Any]:
    """Handle processing errors gracefully."""
    error_message = state.get("error_message", "Unknown error")

    return {
        "processing_step": f"error_handled: {error_message}",
        "summary": f"Error occurred: {error_message}"
    }


# Routing logic for conditional edges
def route_after_validation(state: DocumentProcessingState) -> str:
    """Determine next step after validation."""
    if state.get("is_valid", False):
        return "process_content"
    else:
        return "handle_error"


def main():
    """Main function demonstrating the Fluent API usage."""

    print("🚀 LangGraph Fluent API Example")
    print("=" * 50)

    # Create workflow using the fluent API
    workflow = create_workflow(DocumentProcessingState)

    # Create nodes using the fluent syntax
    validate_node = FluentNode("validate_document").with_function(validate_document)
    process_node = FluentNode("process_content").with_function(process_content)
    summary_node = FluentNode("generate_summary").with_function(generate_summary)
    save_node = FluentNode("save_results").with_function(save_results)
    error_node = FluentNode("handle_error").with_function(handle_error)

    # Add nodes to workflow using >> operator
    print("📝 Adding nodes to workflow...")
    workflow >> validate_node
    workflow >> process_node
    workflow >> summary_node
    workflow >> save_node
    workflow >> error_node

    # Set entry point
    workflow.set_entry_point(validate_node)

    # Add conditional routing after validation
    workflow.add_conditional_edges(
        validate_node,
        route_after_validation,
        {
            "process_content": process_node,
            "handle_error": error_node
        }
    )

    # Create linear flow for successful processing using >> operator
    print("🔗 Creating workflow edges...")
    process_node >> summary_node >> save_node >> "END"
    error_node >> "END"

    # Compile the workflow
    print("⚙️  Compiling workflow...")
    app = workflow.compile()

    # Test with valid document
    print("\n✅ Testing with valid document:")
    valid_state = {
        "document": "This is a comprehensive example document that demonstrates the new LangGraph Fluent API functionality with operator overloading.",
        "is_valid": False,
        "processed_content": "",
        "summary": "",
        "error_message": "",
        "processing_step": ""
    }

    result = app.invoke(valid_state)
    print(f"Final state: {result}")

    # Test with invalid document
    print("\n❌ Testing with invalid document:")
    invalid_state = {
        "document": "Short",
        "is_valid": False,
        "processed_content": "",
        "summary": "",
        "error_message": "",
        "processing_step": ""
    }

    result = app.invoke(invalid_state)
    print(f"Final state: {result}")

    print("\n🎉 Fluent API example completed successfully!")
    print("\nKey Benefits Demonstrated:")
    print("• ➡️  Intuitive >> operator for adding nodes and creating edges")
    print("• 🔗 Method chaining with .with_function()")
    print("• 🎯 Clear, readable workflow construction")
    print("• 🔀 Full compatibility with existing LangGraph features")
    print("• 🛠️  Easy integration with conditional edges and routing")


# Alternative example showing more advanced features
def advanced_example():
    """Advanced example showing more complex workflow patterns."""

    print("\n🔥 Advanced Fluent API Example")
    print("=" * 50)

    # Create a more complex workflow
    workflow = create_workflow(DocumentProcessingState)

    # Create multiple processing paths
    validate = FluentNode("validate").with_function(validate_document)
    process_fast = FluentNode("process_fast").with_function(process_content)
    process_detailed = FluentNode("process_detailed").with_function(process_content)
    summarize = FluentNode("summarize").with_function(generate_summary)
    save = FluentNode("save").with_function(save_results)
    error = FluentNode("error").with_function(handle_error)

    # Build workflow with branching paths
    workflow >> validate >> process_fast >> summarize >> save
    workflow >> process_detailed
    workflow >> error

    # Connect alternative paths
    process_detailed >> summarize  # Alternative processing path

    # Set entry and compile
    workflow.set_entry_point("validate")

    print("Advanced workflow created with multiple processing paths!")
    print("Nodes:", list(workflow.nodes.keys()))

    return workflow


if __name__ == "__main__":
    # Run the main example
    main()

    # Run the advanced example
    advanced_example()

    # Show comparison with traditional syntax
    print("\n📊 Syntax Comparison:")
    print("-" * 30)
    print("Traditional LangGraph:")
    print("  workflow.add_node('process', process_func)")
    print("  workflow.add_edge('start', 'process')")
    print("  workflow.add_edge('process', END)")
    print()
    print("Fluent API:")
    print("  start = FluentNode('start').with_function(start_func)")
    print("  process = FluentNode('process').with_function(process_func)")
    print("  workflow >> start >> process >> 'END'")
    print()
    print("✨ Much more intuitive and readable!")
