import os
from flask import Flask, request, jsonify, render_template, session
from openai import OpenAI
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime
import re
from langdetect import detect, LangDetectException
import requests
import copy
import re

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ecom_agent_secret'
LLM = "deepseek-ai/DeepSeek-V3-0324"
language = "bn"

# Initialize OpenAI client
client = OpenAI(
    base_url="https://api.studio.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)

# Backend API URL
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:5000/api")

# Typo corrections for English and Bangla
typo_corrections = {
    # English typos
    "electroncs": "electronics",
    "clothng": "clothing",
    "tshirt": "t-shirt",
    "jens": "jeans",
    "coffe": "coffee",
    "wirless": "wireless",
    "earbuds": "earbuds",
    "smartwatch": "smart watch",
    "smartwach": "smart watch",
    # Bangla common typos (in both Bangla and Banglish)
    "ইলকট্রনিকস": "ইলেকট্রনিকস",
    "পশাক": "পোশাক",
    "টশার্ট": "টি-শার্ট",
    "জনস": "জিন্স",
    "কফ": "কফি",
    "ilektroniks": "electronics",
    "poshak": "clothing",
    "tishirt": "t-shirt",
    "jins": "jeans",
    "kofi": "coffee",
    "oyarles": "wireless",
    "iarbuds": "earbuds",
    "smart wach": "smart watch"
}

# English to Bangla and reverse common term mapping
en_bn_term_mapping = {
    "electronics": "ইলেকট্রনিকস",
    "clothing": "পোশাক",
    "home": "গৃহসজ্জা",
    "t-shirt": "টি-শার্ট",
    "jeans": "জিন্স",
    "wireless earbuds": "ওয়্যারলেস ইয়ারবাডস",
    "smart watch": "স্মার্ট ওয়াচ",
    "coffee maker": "কফি মেকার",
    # Reverse mapping
    "ইলেকট্রনিকস": "electronics",
    "পোশাক": "clothing",
    "গৃহসজ্জা": "home",
    "টি-শার্ট": "t-shirt",
    "জিন্স": "jeans",
    "ওয়্যারলেস ইয়ারবাডস": "wireless earbuds",
    "স্মার্ট ওয়াচ": "smart watch",
    "কফি মেকার": "coffee maker"
}

# Banglish to Bangla common term mapping
banglish_bn_mapping = {
    "elektroniks": "ইলেকট্রনিকস",
    "poshak": "পোশাক",
    "grihosojja": "গৃহসজ্জা",
    "tishirt": "টি-শার্ট",
    "jins": "জিন্স",
    "warless earbuds": "ওয়্যারলেস ইয়ারবাডস",
    "oyarles earbuds": "ওয়্যারলেস ইয়ারবাডস",
    "smart watch": "স্মার্ট ওয়াচ",
    "kofi maker": "কফি মেকার"
}

# Before starting the request, ensure cart session exists
@app.before_request
def before_request():
    if 'cart_id' not in session:
        session['cart_id'] = str(uuid.uuid4())

# Helper function to detect language
def detect_language(text):
    try:
        # First check if text contains Bangla characters
        if re.search(r'[\u0980-\u09FF]', text):
            return "bn"
        
        # Try to determine if the text is Banglish
        if any(banglish_word in text.lower() for banglish_word in banglish_bn_mapping.keys()):
            return "banglish"
            
        # Use language detection library
        detected = detect(text)
        if detected == "bn":
            return "bn"
        return "en"  # Default to English
    except LangDetectException:
        return "en"  # Default to English if detection fails

# Attempt to correct typos and normalize input
def correct_typos(text):
    words = text.lower().split()
    corrected_words = []
    
    for word in words:
        if word in typo_corrections:
            corrected_words.append(typo_corrections[word])
        else:
            corrected_words.append(word)
    
    return " ".join(corrected_words)

# Handle Banglish text
def process_banglish(text):
    # Simple implementation - replace common Banglish terms with Bangla
    for banglish, bangla in banglish_bn_mapping.items():
        text = re.sub(r'\b' + re.escape(banglish) + r'\b', bangla, text, flags=re.IGNORECASE)
    return text

# API call functions - integrateswith real backend
def get_categories():
    """Get all product categories from the backend"""
    try:
        response = requests.get(f"{BACKEND_API_URL}/categories")
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Error fetching categories: {str(e)}")
        return []

def get_products(category_id=None):
    """Get products from the backend, optionally filtered by category"""
    try:
        params = {"category_id": category_id} if category_id else {}
        response = requests.get(f"{BACKEND_API_URL}/products", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return []

def get_product_by_id(product_id):
    """Get product details by ID"""
    try:
        response = requests.get(f"{BACKEND_API_URL}/products/{product_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching product details: {str(e)}")
        return None

def search_products_by_keyword(keyword):
    """Search products by keyword in name or description"""
    # First get all products
    all_products = get_products()
    if not all_products:
        return []
    
    # Then search through them for the keyword
    keyword = keyword.lower()
    results = []
    
    for product in all_products:
        # Search in English fields
        if (keyword in product["name"].lower() or 
            keyword in product["description"].lower()):
            results.append(product)
        # Search in Bangla fields if they exist
        elif (product.get("name_bn") and keyword in product.get("name_bn", "").lower() or 
              product.get("description_bn") and keyword in product.get("description_bn", "").lower()):
            results.append(product)
    
    return results

def search_products_by_category(category):
    """Search products by category, handling both English and Bangla"""
    # First try to map the category name if it's in Bangla or has a typo
    if category in en_bn_term_mapping:
        search_category = en_bn_term_mapping[category]
    else:
        search_category = category
    
    # Get all categories to find the right ID
    all_categories = get_categories()
    category_id = None
    
    for cat in all_categories:
        if (cat["name"].lower() == search_category.lower() or 
            (cat.get("name_bn", "").lower() == search_category.lower())):
            category_id = cat["id"]
            break
    
    # If we found a matching category, get products for that category
    if category_id:
        return get_products(category_id)
    else:
        # Try keyword search instead
        return search_products_by_keyword(category)

def check_product_availability(product_id, quantity=1):
    """Check if product is available in requested quantity"""
    product = get_product_by_id(product_id)
    if not product:
        return False, "Product not found"
    if product["stock"] < quantity:
        return False, f"Only {product['stock']} units available"
    return True, "Product available"

def add_to_cart(product_id, quantity=1, variant_id=None):
    """Add product to the cart"""
    try:
        data = {
            'session_id': session['cart_id'],
            'product_id': product_id,
            'quantity': quantity
        }
        if variant_id:
            data['variant_id'] = variant_id
            
        response = requests.post(f"{BACKEND_API_URL}/cart/add", json=data)
        if response.status_code == 200:
            return True, "Product added to cart"
        else:
            return False, "Error adding product to cart"
    except Exception as e:
        print(f"Error adding to cart: {str(e)}")
        return False, str(e)

def get_cart():
    """Get current cart contents"""
    try:
        response = requests.get(f"{BACKEND_API_URL}/cart", params={'session_id': session['cart_id']})
        if response.status_code == 200:
            return response.json()
        else:
            return {'items': [], 'total': 0}
    except Exception as e:
        print(f"Error retrieving cart: {str(e)}")
        return {'items': [], 'total': 0}

def create_order(customer_info):
    """Create a new order from current cart"""
    try:
        data = {
            'session_id': session['cart_id'],
            'customer_info': customer_info
        }
        
        response = requests.post(f"{BACKEND_API_URL}/orders/create", json=data)
        if response.status_code == 200:
            return response.json(), "Order created successfully"
        else:
            return None, "Error creating order"
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return None, str(e)

def generate_invoice(order_id):
    """Generate an invoice from an order"""
    try:
        response = requests.get(f"{BACKEND_API_URL}/orders/{order_id}/invoice")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error generating invoice: {str(e)}")
        return None

# AI conversation management
def process_user_message(user_message, conversation_history):
    """Process user message with AI and get appropriate response"""
    
    # Preprocess user message
    original_message = user_message
    
    # Detect language
    detected_lang = detect_language(user_message)
    
    # Apply typo corrections
    user_message = correct_typos(user_message)
    
    # Process Banglish if detected
    if detected_lang == "banglish":
        user_message = process_banglish(user_message)
        detected_lang = "bn"  # Treat as Bangla after processing
    
    # Update conversation history with the processed message
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Get available categories for the system prompt
    categories = get_categories()
    category_list = []
    for cat in categories:
        if cat.get("name_bn"):
            category_list.append(f"{cat['name']}/{cat['name_bn']}")
        else:
            category_list.append(cat['name'])
    
    category_str = ", ".join(category_list)
    
    # Create system prompt with product knowledge and available actions
    system_prompt = {
        "role": "system",
        "content": f"""
You are a helpful bilingual e-commerce customer service AI that can speak and understand both English and Bangla (Bengali) and even banglish. But you will always reply in {language}. Your task is to assist customers with:
1. Finding products based on categories or keywords
2. Providing product information including price and availability
3. Processing orders when customers want to buy something
4. Collecting delivery information for orders

Available Fucntions that you can perform:
- search_products: Search for products by category or keyword
- get_product_details: Get detailed information about a specific product
- create_order: Create an order based on the customer's cart
- collect_customer_info: Collect customer information for order processing
- generate_invoice: Generate an invoice for the order
- general_response: Provide general information or assistance

The available categories are: {category_str}

When a customer wants to place an order, ask for:
- Their name (নাম)
- Shipping address (ঠিকানা)
- Email address (ইমেইল)
- Phone number (ফোন নম্বর)
- Payment method (পেমেন্ট পদ্ধতি) (for demo purposes only, no real payment processing)

When a customer asks for product information, provide:
- Product name (পণ্যের নাম)
- Product description (পণ্যের বিবরণ)
- Product price (পণ্যের দাম)
- Product availability (পণ্যের প্রাপ্যতা)
- Product variants (if applicable) (পণ্যের ভেরিয়েন্টস)

For product searches, respond with the available products and their details.
If a customer wants to buy a product, confirm the details and ask for their information.
Once all information is collected, provide a summary of the order.

IMPORTANT: The detected language of the current user message is "{detected_lang}". 
If detected_lang is "bn", respond in Bangla.
If detected_lang is "en", respond in English.

Always respond in JSON format wrapped in <ai_response> tags with these fields:
- "message": Your natural-sounding response to the customer in the appropriate language
- "action": One of ["search_products", "get_product_details", "create_order", "collect_customer_info", "generate_invoice", "general_response"]
- "parameters": Any parameters needed for the action
- "context_update": Any updates to the conversation context

Example:
<ai_response>
{{
  "message": "I found 3 products in the Electronics category. Would you like to know more about any of them?",
  "action": "search_products",
  "parameters": {{"category": "Electronics"}},
  "context_update": {{"last_search_results": [1, 2, 3], "language": "en"}}
}}
</ai_response>

Or in Bangla:
<ai_response>
{{
  "message": "আমি ইলেকট্রনিকস বিভাগে ৩টি পণ্য খুঁজে পেয়েছি। আপনি কি কোনোটি সম্পর্কে আরও জানতে চান?",
  "action": "search_products",
  "parameters": {{"category": "ইলেকট্রনিকস"}},
  "context_update": {{"last_search_results": [1, 2, 3], "language": "bn"}}
}}
</ai_response>
"""
    }
    
    # Create context message with latest state information
    context_message = {
        "role": "system",
        "content": f"""
The user's original message was: "{original_message}"
The processed message after typo correction and language processing is: "{user_message}"
The detected language is: "{detected_lang}"

Remember: You must only talk about products that actually exist in the database. Never make up product information.
If you're asked about specific products, you must first search for them to confirm they exist.
"""
    }
    
    # Combine messages for AI
    messages = [system_prompt, context_message] + conversation_history
    
    # Get response from AI
    response = client.chat.completions.create(
        model=f"{LLM}",
        messages=messages,
        max_tokens=800,
        temperature=0.2,
    )
    
    ai_response = response.choices[0].message.content
    
    # Extract JSON from the AI response
    try:
        json_start = ai_response.find("<ai_response>")
        json_end = ai_response.find("</ai_response>")
        
        if json_start != -1 and json_end != -1:
            json_str = ai_response[json_start + len("<ai_response>"):json_end].strip()
            ai_action = json.loads(json_str)
        else:
            # Fallback if AI didn't use the requested format
            ai_action = {
                "message": ai_response,
                "action": "general_response",
                "parameters": {},
                "context_update": {"language": detected_lang}
            }
    except Exception as e:
        print(f"Error parsing AI response: {str(e)}")
        ai_action = {
            "message": "I apologize, but I'm having trouble understanding. Could you please try again?",
            "action": "general_response",
            "parameters": {},
            "context_update": {"language": detected_lang}
        }
    
    # Update conversation history
    conversation_history.append({
        "role": "assistant",
        "content": ai_action["message"]
    })
    
    return ai_action, conversation_history

def validate_ai_response(ai_action, available_data):
    """
    Validate the AI response against the actual database
    to prevent hallucinations and ensure responses only reference real products
    """
    validated_action = copy.deepcopy(ai_action)
    
    # If it's a search action, check if mentioned products actually exist
    if ai_action["action"] == "search_products":
        if "category" in ai_action["parameters"]:
            actual_products = search_products_by_category(ai_action["parameters"]["category"])
        elif "keyword" in ai_action["parameters"]:
            actual_products = search_products_by_keyword(ai_action["parameters"]["keyword"])
        else:
            actual_products = []
        
        if actual_products:
            actual_product_names = [p["name"] for p in actual_products]
            pattern = r'\d+\.\s+[^,\n]+\s+-\s+\$\d+(\.\d+)?'
            validated_action["message"] = re.sub(pattern, '', validated_action["message"])
            
            # Add actual products to the message
            product_list = "\n".join([
                f"{idx+1}. {p['name']} - ${p['price']:.2f}"
                for idx, p in enumerate(actual_products)
            ])
            validated_action["message"] = f"{validated_action['message']}\n\n{product_list}"

    
    # Validate category references
    if "category" in ai_action["parameters"]:
        categories = available_data["categories"]
        category = ai_action["parameters"]["category"]
        
        if not any(c["name"].lower() == category.lower() for c in categories):
            # Try to map category to existing one
            if category in en_bn_term_mapping:
                mapped_category = en_bn_term_mapping[category]
                if any(c["name"].lower() == mapped_category.lower() for c in categories):
                    validated_action["parameters"]["category"] = mapped_category
            else:
                # Remove invalid category
                validated_action["parameters"].pop("category")
                validated_action["action"] = "general_response"
                validated_action["message"] = "I couldn't find that category. Here are our available categories: " + \
                    ", ".join(c["name"] for c in categories)

    return validated_action

# Flask routes
@app.route('/')
def index():
    return render_template('store/chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    conversation_history = data.get('conversation_history', [])
    
    ai_action, updated_history = process_user_message(user_message, conversation_history)
    
    # Validate AI response against actual database
    available_data = {
        "products": get_products(),
        "categories": get_categories()
    }
    ai_action = validate_ai_response(ai_action, available_data)
    
    # Execute action based on AI response
    result = None
    
    if ai_action["action"] == "search_products":
        if "category" in ai_action["parameters"]:
            result = search_products_by_category(ai_action["parameters"]["category"])
        elif "keyword" in ai_action["parameters"]:
            result = search_products_by_keyword(ai_action["parameters"]["keyword"])
    
    elif ai_action["action"] == "get_product_details":
        if "product_id" in ai_action["parameters"]:
            result = get_product_by_id(ai_action["parameters"]["product_id"])
    
    elif ai_action["action"] == "add_to_cart":
        if "product_id" in ai_action["parameters"]:
            product_id = ai_action["parameters"]["product_id"]
            quantity = ai_action["parameters"].get("quantity", 1)
            variant_id = ai_action["parameters"].get("variant_id")
            success, message = add_to_cart(product_id, quantity, variant_id)
            result = {"success": success, "message": message}
            if success:
                # Get updated cart
                cart = get_cart()
                result["cart"] = cart
    
    elif ai_action["action"] == "create_order":
        if "customer_info" in ai_action["parameters"]:
            order, message = create_order(ai_action["parameters"]["customer_info"])
            if order:
                result = order
                # Generate invoice
                invoice = generate_invoice(order["order_id"])
                if invoice:
                    result["invoice"] = invoice
            else:
                result = {"error": message}
    
    elif ai_action["action"] == "get_cart":
        result = get_cart()
    
    return jsonify({
        "ai_message": ai_action["message"],
        "action": ai_action["action"],
        "result": result,
        "conversation_history": updated_history
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)