from app import app, db, Category, Product, ProductImage

with app.app_context():
    db.drop_all()
    db.create_all()

    # --- Sample Categories ---
    electronics = Category(
        name='Electronics',
        name_bn='ইলেকট্রনিক্স',
        description='Electronic devices and accessories'
    )
    fashion = Category(
        name='Fashion',
        name_bn='ফ্যাশন',
        description='Clothing and accessories'
    )

    db.session.add_all([electronics, fashion])
    db.session.commit()

    # --- Sample Products ---
    phone = Product(
        name='Smartphone X10',
        name_bn='স্মার্টফোন X10',
        description='Latest generation smartphone with high performance',
        description_bn='সর্বশেষ প্রজন্মের উচ্চ কর্মক্ষমতা সম্পন্ন স্মার্টফোন',
        price=699.99,
        stock=50,
        category=electronics
    )
    tshirt = Product(
        name='Cool T-Shirt',
        name_bn='কুল টি-শার্ট',
        description='Cotton t-shirt with printed design',
        description_bn='প্রিন্টেড ডিজাইন সহ সুতি টি-শার্ট',
        price=19.99,
        stock=100,
        category=fashion
    )

    db.session.add_all([phone, tshirt])
    db.session.commit()

    # --- Sample Product Images ---
    phone_img = ProductImage(
        product=phone, 
        filename='smartphone1.jpg',
        is_primary=True
    )
    tshirt_img = ProductImage(
        product=tshirt, 
        filename='tshirt1.jpg',
        is_primary=True
    )

    db.session.add_all([phone_img, tshirt_img])
    db.session.commit()

    print("✅ Database seeded successfully.")
