import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ecom'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Models
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_bn = db.Column(db.String(100))
    description = db.Column(db.Text)
    products = db.relationship('Product', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_bn': self.name_bn,
            'description': self.description
        }

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_bn = db.Column(db.String(100))
    description = db.Column(db.Text)
    description_bn = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade="all, delete-orphan")
    variants = db.relationship('ProductVariant', backref='product', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_bn': self.name_bn,
            'description': self.description,
            'description_bn': self.description_bn,
            'price': self.price,
            'stock': self.stock,
            'category_id': self.category_id,
            'category_name': self.category.name,
            'images': [img.to_dict() for img in self.images],
            'variants': [variant.to_dict() for variant in self.variants],
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'url': f'/static/uploads/{self.filename}',
            'is_primary': self.is_primary
        }

class ProductVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    color = db.Column(db.String(50))
    size = db.Column(db.String(50))
    sku = db.Column(db.String(100))
    stock = db.Column(db.Integer, default=0)
    price_adjustment = db.Column(db.Float, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'color': self.color,
            'size': self.size,
            'sku': self.sku,
            'stock': self.stock,
            'price_adjustment': self.price_adjustment
        }

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref='cart_items')
    variant = db.relationship('ProductVariant', backref='cart_items')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True)
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    
    # Add these relationships
    product = db.relationship('Product', backref='order_items')
    variant = db.relationship('ProductVariant', backref='order_items')

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return filename
    return None

# Routes - Admin Panel
@app.route('/admin')
def admin_dashboard():
    # Get counts
    products_count = Product.query.count()
    categories_count = Category.query.count()
    orders_count = Order.query.count()
    
    # Get recent products and orders
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         products_count=products_count,
                         categories_count=categories_count,
                         orders_count=orders_count,
                         recent_products=recent_products,
                         recent_orders=recent_orders)

# Category Management
@app.route('/admin/categories')
def category_list():
    categories = Category.query.all()
    return render_template('admin/categories/list.html', categories=categories)

@app.route('/admin/categories/new', methods=['GET', 'POST'])
def category_create():
    if request.method == 'POST':
        name = request.form.get('name')
        name_bn = request.form.get('name_bn')
        description = request.form.get('description')
        
        category = Category(name=name, name_bn=name_bn, description=description)
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully', 'success')
        return redirect(url_for('category_list'))
        
    return render_template('admin/categories/create.html')

@app.route('/admin/categories/edit/<int:id>', methods=['GET', 'POST'])
def category_edit(id):
    category = Category.query.get_or_404(id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.name_bn = request.form.get('name_bn')
        category.description = request.form.get('description')
        
        db.session.commit()
        flash('Category updated successfully', 'success')
        return redirect(url_for('category_list'))
        
    return render_template('admin/categories/edit.html', category=category)

@app.route('/admin/categories/delete/<int:id>', methods=['POST'])
def category_delete(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully', 'success')
    return redirect(url_for('category_list'))

# Product Management
@app.route('/admin/products')
def product_list():
    products = Product.query.all()
    return render_template('admin/products/list.html', products=products)

@app.route('/admin/products/new', methods=['GET', 'POST'])
def product_create():
    if request.method == 'POST':
        # Basic product info
        name = request.form.get('name')
        name_bn = request.form.get('name_bn')
        description = request.form.get('description')
        description_bn = request.form.get('description_bn')
        price = float(request.form.get('price', 0))
        stock = int(request.form.get('stock', 0))
        category_id = int(request.form.get('category_id'))
        
        # Create product
        product = Product(
            name=name, 
            name_bn=name_bn,
            description=description,
            description_bn=description_bn,
            price=price,
            stock=stock,
            category_id=category_id
        )
        db.session.add(product)
        db.session.flush()  # Get product ID without committing
        
        # Handle image uploads
        if 'images' in request.files:
            images = request.files.getlist('images')
            for i, image in enumerate(images):
                if image.filename:
                    filename = save_uploaded_file(image)
                    if filename:
                        is_primary = i == 0  # First image is primary
                        product_image = ProductImage(
                            filename=filename,
                            product_id=product.id,
                            is_primary=is_primary
                        )
                        db.session.add(product_image)
        
        # Handle variants
        variant_count = int(request.form.get('variant_count', 0))
        for i in range(variant_count):
            color = request.form.get(f'variant_color_{i}')
            size = request.form.get(f'variant_size_{i}')
            sku = request.form.get(f'variant_sku_{i}')
            var_stock = int(request.form.get(f'variant_stock_{i}', 0))
            price_adjustment = float(request.form.get(f'variant_price_adjustment_{i}', 0))
            
            variant = ProductVariant(
                product_id=product.id,
                color=color,
                size=size,
                sku=sku,
                stock=var_stock,
                price_adjustment=price_adjustment
            )
            db.session.add(variant)
        
        db.session.commit()
        flash('Product created successfully', 'success')
        return redirect(url_for('product_list'))
    
    categories = Category.query.all()
    return render_template('admin/products/create.html', categories=categories)

@app.route('/admin/products/edit/<int:id>', methods=['GET', 'POST'])
def product_edit(id):
    product = Product.query.get_or_404(id)
    
    if request.method == 'POST':
        # Update basic product info
        product.name = request.form.get('name')
        product.name_bn = request.form.get('name_bn')
        product.description = request.form.get('description')
        product.description_bn = request.form.get('description_bn')
        product.price = float(request.form.get('price', 0))
        product.stock = int(request.form.get('stock', 0))
        product.category_id = int(request.form.get('category_id'))
        
        # Handle image uploads
        if 'new_images' in request.files:
            images = request.files.getlist('new_images')
            for image in images:
                if image.filename:
                    filename = save_uploaded_file(image)
                    if filename:
                        # If no primary image exists, make this primary
                        is_primary = not any(img.is_primary for img in product.images)
                        product_image = ProductImage(
                            filename=filename,
                            product_id=product.id,
                            is_primary=is_primary
                        )
                        db.session.add(product_image)
        
        # Handle existing images
        for img in product.images:
            if request.form.get(f'delete_image_{img.id}'):
                db.session.delete(img)
            elif request.form.get(f'primary_image_{img.id}'):
                # Set this as primary, unset others
                for other_img in product.images:
                    other_img.is_primary = (other_img.id == img.id)
        
        # Handle variants - first remove existing ones if needed
        if request.form.get('replace_variants') == 'yes':
            for variant in product.variants:
                db.session.delete(variant)
            
            # Then add new variants
            variant_count = int(request.form.get('variant_count', 0))
            for i in range(variant_count):
                color = request.form.get(f'variant_color_{i}')
                size = request.form.get(f'variant_size_{i}')
                sku = request.form.get(f'variant_sku_{i}')
                var_stock = int(request.form.get(f'variant_stock_{i}', 0))
                price_adjustment = float(request.form.get(f'variant_price_adjustment_{i}', 0))
                
                variant = ProductVariant(
                    product_id=product.id,
                    color=color,
                    size=size,
                    sku=sku,
                    stock=var_stock,
                    price_adjustment=price_adjustment
                )
                db.session.add(variant)
        
        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('product_list'))
    
    categories = Category.query.all()
    return render_template('admin/products/edit.html', product=product, categories=categories)

@app.route('/admin/products/delete/<int:id>', methods=['POST'])
def product_delete(id):
    product = Product.query.get_or_404(id)
    
    # Delete product images from filesystem
    for image in product.images:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
        except:
            pass  # File might not exist
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully', 'success')
    return redirect(url_for('product_list'))

# Add after existing admin routes
@app.route('/admin/orders')
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders/list.html', orders=orders)

@app.route('/admin/orders/<int:id>')
def admin_order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/orders/detail.html', order=order)

@app.route('/admin/orders/<int:id>/status', methods=['POST'])
def admin_order_status(id):
    order = Order.query.get_or_404(id)
    status = request.form.get('status')
    if status in ['pending', 'processing', 'shipped', 'delivered']:
        order.status = status
        db.session.commit()
        flash('Order status updated successfully', 'success')
    return redirect(url_for('admin_order_detail', id=order.id))

# API Routes
@app.route('/api/categories', methods=['GET'])
def api_categories():
    categories = Category.query.all()
    return jsonify([category.to_dict() for category in categories])

@app.route('/api/products', methods=['GET'])
def api_products():
    category_id = request.args.get('category_id')
    
    if category_id:
        products = Product.query.filter_by(category_id=category_id).all()
    else:
        products = Product.query.all()
        
    return jsonify([product.to_dict() for product in products])

@app.route('/api/products/<int:id>', methods=['GET'])
def api_product_detail(id):
    product = Product.query.get_or_404(id)
    return jsonify(product.to_dict())

# Customer-facing routes
@app.route('/')
def home():
    products = Product.query.limit(8).all()
    categories = Category.query.all()
    return render_template('store/home.html', products=products, categories=categories)

@app.route('/category/<int:id>')
def category_products(id):
    category = Category.query.get_or_404(id)
    products = Product.query.filter_by(category_id=id).all()
    return render_template('store/category.html', category=category, products=products)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('store/product.html', product=product)

@app.before_request
def before_request():
    if 'cart_id' not in session:
        session['cart_id'] = str(uuid.uuid4())

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    variant_id = request.form.get('variant_id')
    quantity = int(request.form.get('quantity', 1))
    
    cart_item = CartItem.query.filter_by(
        session_id=session['cart_id'],
        product_id=product_id,
        variant_id=variant_id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            session_id=session['cart_id'],
            product_id=product_id,
            variant_id=variant_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Product added to cart', 'success')
    return redirect(url_for('cart_view'))

@app.route('/cart')
def cart_view():
    cart_items = CartItem.query.filter_by(session_id=session['cart_id']).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('store/cart.html', cart_items=cart_items, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        cart_items = CartItem.query.filter_by(session_id=session['cart_id']).all()
        if not cart_items:
            flash('Your cart is empty', 'error')
            return redirect(url_for('cart_view'))
        
        # Create order
        order = Order(
            order_number=f'ORD-{datetime.now().strftime("%Y%m%d")}-{uuid.uuid4().hex[:6].upper()}',
            customer_name=request.form['name'],
            customer_email=request.form['email'],
            customer_phone=request.form['phone'],
            address=request.form['address'],
            total_amount=sum(item.product.price * item.quantity for item in cart_items)
        )
        db.session.add(order)
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                product_id=cart_item.product_id,
                variant_id=cart_item.variant_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
        
        # Clear cart
        CartItem.query.filter_by(session_id=session['cart_id']).delete()
        db.session.commit()
        
        return redirect(url_for('order_complete', order_id=order.id))
    
    cart_items = CartItem.query.filter_by(session_id=session['cart_id']).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('store/checkout.html', cart_items=cart_items, total=total)

@app.route('/order/<int:order_id>')
def order_complete(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('store/order_complete.html', order=order)

# Add these new routes
@app.route('/cart/update/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.session_id != session['cart_id']:
        flash('Invalid cart item', 'error')
        return redirect(url_for('cart_view'))
    
    quantity = int(request.form.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
        db.session.commit()
        flash('Cart updated', 'success')
    
    return redirect(url_for('cart_view'))

@app.route('/cart/remove/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.session_id != session['cart_id']:
        flash('Invalid cart item', 'error')
        return redirect(url_for('cart_view'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart', 'success')
    return redirect(url_for('cart_view'))

# Initialize the database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)