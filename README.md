# E-Commerce Agent v1

E-Commerce Agent v1 is a bilingual (English and Bengali) e-commerce platform integrated with an AI-powered customer support chat assistant. The platform allows users to browse products, manage orders, and interact with an intelligent chatbot for assistance.

---

## Features

### E-Commerce Platform
- **Product Catalog**: Browse products with categories, variants, and images.
- **Shopping Cart**: Add, update, and remove items from the cart.
- **Order Management**: Place orders and view order details.
- **Admin Dashboard**: Manage products, categories, and orders.
- **Bilingual Support**: Product details available in English and Bengali.

### AI Chat Assistant
- **Natural Language Interaction**: Supports English, Bengali, and Banglish (Bengali written in English).
- **Product Search**: Find products by category or keyword.
- **Order Assistance**: Help with adding items to the cart and placing orders.
- **Smart Typo Correction**: Detects and corrects common typos.
- **Dark/Light Mode**: User-friendly chat interface with theme options.

---

## Project Structure

```
ecom-agent-v1/
├── agent/                # AI Chat Assistant
│   ├── app.py            # Chat backend service
│   ├── templates/        # Chat UI templates
│   ├── requirements.txt  # Python dependencies for the agent
│   └── .env              # Environment variables for API keys
├── ecommerce/            # E-commerce Platform
│   ├── app.py            # Main e-commerce backend
│   ├── templates/        # Store and admin templates
│   ├── static/           # Static assets (images, CSS, JS)
│   ├── seed_data.py      # Script to seed the database with sample data
│   ├── requirements.txt  # Python dependencies for the platform
│   └── instance/         # SQLite database
```

---

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **AI Integration**: Nebius API with DeepSeek-V3-0324 LLM
- **Language Tools**: `langdetect` for language detection

---

## Setup Instructions

### Prerequisites
- Python 3.13 or higher
- Virtual environment tools (e.g., `venv` or `virtualenv`)

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/ecom-agent-v1.git
    cd ecom-agent-v1
    ```

2. **Set up the e-commerce platform**:
    ```bash
    cd ecommerce
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    python seed_data.py  # Seed the database with sample data
    ```

3. **Set up the AI chat assistant**:
    ```bash
    cd ../agent
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

4. **Configure environment variables**:  
    Create a `.env` file in the `agent` directory with the following content:
    ```
    NEBIUS_API_KEY=your_api_key_here
    BACKEND_API_URL=http://localhost:5000/api
    ```

5. **Run the services**:

    - In one terminal, start the e-commerce platform:
      ```bash
      cd ecommerce
      python app.py  # Runs on http://localhost:5000
      ```

    - In another terminal, start the chat assistant:
      ```bash
      cd agent
      python app.py  # Runs on http://localhost:5001
      ```

---

## Access the Application

- **E-commerce Store**: [http://localhost:5000](http://localhost:5000)
- **Admin Dashboard**: [http://localhost:5000/admin](http://localhost:5000/admin)
- **Chat Assistant**: [http://localhost:5001](http://localhost:5001)

---

## Usage

1. Browse products and categories on the e-commerce platform.
2. Use the chat assistant to search for products, get recommendations, and place orders.
3. Manage products, categories, and orders via the admin dashboard.

---

## Contributing

1. Fork the repository.
2. Create a feature branch:
    ```bash
    git checkout -b feature/your-feature-name
    ```
3. Commit your changes:
    ```bash
    git commit -m "Add your feature description"
    ```
4. Push to the branch:
    ```bash
    git push origin feature/your-feature-name
    ```
5. Open a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Nebius API**: For powering the AI chat assistant.
- **Bootstrap**: For the responsive frontend design.
- **Flask**: For the lightweight and flexible backend framework.

