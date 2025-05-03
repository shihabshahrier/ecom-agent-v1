import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
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
    return render_template('admin/dashboard.html')

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

# Initialize the database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)