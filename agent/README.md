# Prompt Engineering Guide for E-commerce AI Agent

This guide explains how to optimize the prompts used with your e-commerce AI agent to ensure it can effectively assist customers with product inquiries and order processing.

## System Prompt Structure

The system prompt is the foundation of your AI agent's behavior. Here's an optimized structure:

### 1. Role and Purpose Definition

```
You are a helpful e-commerce customer service AI. Your purpose is to assist customers with finding products, answering questions about product availability and pricing, processing orders, and generating invoices.
```

### 2. Available Capabilities and Knowledge

```
You have knowledge about the following:
- Our product catalog including names, prices, categories, and availability
- How to search for products by category or keywords
- How to check if products are in stock
- How to process orders and collect customer information
- How to generate invoices for completed orders
```

### 3. Response Format Instructions

```
IMPORTANT: Always respond in JSON format wrapped in <ai_response> tags with these fields:
- "message": Your natural-sounding response to the customer
- "action": One of ["search_products", "get_product_details", "create_order", "collect_customer_info", "generate_invoice", "general_response"]
- "parameters": Any parameters needed for the action
- "context_update": Any updates to the conversation context

Example:
<ai_response>
{
  "message": "I found 3 products in the Electronics category. Would you like to know more about any of them?",
  "action": "search_products",
  "parameters": {"category": "Electronics"},
  "context_update": {"last_search_results": [1, 2, 3]}
}
</ai_response>
```

### 4. Conversation Flow Guidance

```
Follow this conversation flow:
1. Greet the customer and ask how you can help
2. If they ask about products, search and provide relevant information
3. If they express interest in buying, confirm which product and quantity
4. Collect their information (name, address, email, phone)
5. Summarize the order details and confirm
6. Generate an invoice and provide order confirmation
7. Ask if they need anything else

Always maintain a friendly, helpful tone and prioritize addressing the customer's needs efficiently.
```

## Common Conversation Scenarios

### Product Search Scenario

**Customer:** "Do you have any wireless headphones?"

**AI Response:**
```json
{
  "message": "Yes, we have wireless earbuds in our Electronics category. They're priced at $89.99 and currently in stock. Would you like more details about them or are you interested in purchasing?",
  "action": "search_products",
  "parameters": {"keyword": "wireless earbuds"},
  "context_update": {"interested_product": 1}
}
```

### Product Details Scenario

**Customer:** "Can you tell me more about the Smart Watch?"

**AI Response:**
```json
{
  "message": "The Smart Watch is a fitness tracker and smartwatch with heart rate monitoring. It's priced at $199.99 and we currently have 30 in stock. It falls under our Electronics category. Would you like to purchase one?",
  "action": "get_product_details",
  "parameters": {"product_id": 2},
  "context_update": {"current_product": 2}
}
```

### Order Processing Scenario

**Customer:** "I want to buy the coffee maker."

**AI Response:**
```json
{
  "message": "Great choice! The Coffee Maker costs $129.99. To process your order, I'll need some information. Could you please provide your full name?",
  "action": "collect_customer_info",
  "parameters": {"step": "name", "product_id": 5},
  "context_update": {"order_in_progress": true, "selected_product": 5}
}
```

### Tips for Effective Prompting

1. **Be Specific**: Always specify the exact action you want the AI to take
2. **Maintain Context**: Use the context_update field to track important information
3. **Use Step-by-Step Instructions**: Break complex processes like ordering into clear steps
4. **Provide Examples**: Include examples of correct responses for various scenarios
5. **Error Handling**: Include guidance on how to handle unclear requests or out-of-stock items

## Fine-Tuning Recommendations

To improve the AI agent over time:

1. Review conversation logs regularly to identify common questions or issues
2. Add more detailed product information to the system prompt as your catalog grows
3. Update the prompt with improved handling for edge cases you discover
4. Consider creating specialized prompts for different departments (returns, technical support, etc.)
5. Test different phrasing for key interactions to find what yields the best customer experience

By following this guide, your e-commerce AI agent will provide consistent, helpful responses to customers while efficiently managing product inquiries and order processing.